"""
Bulk-fetches all Consolidated Integrated Filings released in the last 7 days
(or a custom date range) and saves them to the database.

Skips symbols that already have a filing for that quarter_end in the DB.
Skips symbols not present in the companies table.

Usage:
    python -m scripts.fetch_bulk_filings
    python -m scripts.fetch_bulk_filings --days 14
    python -m scripts.fetch_bulk_filings --from 29-06-2026 --to 06-07-2026
"""

import argparse
from datetime import date, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed

from app.db import SessionLocal
from app.models import Company, IntegratedFiling
from app.nse.client import NSEClient
from app.providers.integrated_filings import _parse_qe_date, _parse_broadcast_date
from app.clients.filing_downloader import FilingDownloader
from app.parsers.integrated_filing_parser import IntegratedFilingParser
from app.extractors.financial_extractor import FinancialExtractor
from app.importers.filing_importer import save_filing


# ── Helpers ────────────────────────────────────────────────────────────────

def get_known_symbols(session):
    """Return set of all symbols present in the companies table."""
    rows = session.query(Company.symbol).all()
    return {r.symbol for r in rows}


def get_existing_filings(session):
    """Return dict of (symbol, quarter_end, consolidated_type) -> is_revision already in the DB."""
    rows = session.query(
        IntegratedFiling.symbol,
        IntegratedFiling.quarter_end,
        IntegratedFiling.consolidated,
        IntegratedFiling.is_revision,
    ).all()
    return {
        (r.symbol, r.quarter_end, (r.consolidated or "").strip().lower()): (r.is_revision is True)
        for r in rows
    }


def discover_filings(client, from_date: str, to_date: str, page_size: int = 100):
    """
    Pull all filings from the bulk endpoint for the given date window.
    Returns a flat list of raw filing dicts from NSE.
    """
    all_filings = []
    page = 1

    while True:
        print(f"  Fetching page {page}...")
        data = client.get_json(
            "/api/integrated-filing-results",
            params={
                "index":     "equities",
                "from_date": from_date,
                "to_date":   to_date,
                "type":      "Integrated Filing- Financials",
                "page":      page,
                "size":      page_size,
            }
        )

        records = data.get("data", [])
        if not records:
            break

        all_filings.extend(records)

        for r in records:
            if r.get("type_Sub"):
                print(f"  type_Sub found: {r['symbol']} | {r['type_Sub']} | {r.get('consolidated')} | {r.get('qe_Date')}")

        # If we got fewer records than page_size, we're on the last page
        if len(records) < page_size:
            break

        page += 1

    return all_filings


def pick_best_filings(raw_filings):
    """
    For each (symbol, quarter), pick the best filing:
      - Consolidated preferred over Standalone
      - Revision preferred over Original within the same type
    """
    consolidated = {}  # (symbol, qe) -> best consolidated filing
    standalone   = {}  # (symbol, qe) -> best standalone filing

    for f in raw_filings:
        if not f.get("ixbrl"):
            continue

        symbol = f.get("symbol", "").strip().upper()
        qe     = _parse_qe_date(f)
        if not symbol or qe is None:
            continue

        filing_type = f.get("consolidated", "").strip().lower()
        is_revision = f.get("type_Sub", "").strip().lower() == "revision"
        key = (symbol, qe)

        if filing_type == "consolidated":
            existing = consolidated.get(key)
            if existing is None or (is_revision and existing.get("type_Sub", "").strip().lower() != "revision"):
                consolidated[key] = f
        elif filing_type == "standalone":
            existing = standalone.get(key)
            if existing is None or (is_revision and existing.get("type_Sub", "").strip().lower() != "revision"):
                standalone[key] = f

    # Merge: consolidated takes priority; fall back to standalone
    best = {**standalone, **consolidated}
    return list(best.values())


def process_one(filing_meta, known_symbols, existing_filings, downloader):
    """
    Download, parse and save one filing.
    Returns a result dict describing what happened.
    """
    symbol = filing_meta.get("symbol", "").strip().upper()
    qe     = _parse_qe_date(filing_meta)

    # Skip if company not in our DB
    if symbol not in known_symbols:
        return {"symbol": symbol, "status": "skipped", "reason": "not in companies table"}

    # Skip if we already have this quarter + type combination
    filing_type = filing_meta.get("consolidated", "").strip().lower()
    is_revision = filing_meta.get("type_Sub", "").strip().lower() == "revision"
    key = (symbol, qe, filing_type)

    print(f"  DEBUG {symbol} {qe} {filing_type} is_revision={is_revision} existing={existing_filings.get(key)}")    

    if key in existing_filings:
        already_revision = existing_filings[key]
        if already_revision or not is_revision:
            return {"symbol": symbol, "status": "skipped", "reason": f"already have {qe} {filing_type}"}
    
    ixbrl_url    = filing_meta.get("ixbrl")
    company_name = filing_meta.get("cmName", "").strip()

    try:
        html         = downloader.download_html(ixbrl_url)
        parsed       = IntegratedFilingParser(html).parse()
        metadata     = parsed["metadata"]
        metadata.setdefault("company_name", company_name)
        standardized = FinancialExtractor(parsed).extract()

        bd           = _parse_broadcast_date(filing_meta)
        filing_date  = bd.strftime("%Y-%m-%d") if bd else None

        save_filing(
            symbol=symbol,
            company_name=company_name,
            metadata=metadata,
            standardized_metrics=standardized,
            ixbrl_url=ixbrl_url,
            xbrl_url=filing_meta.get("xbrl"),
            filing_date=filing_date,
            filing_type="quarterly",
            is_revision=is_revision,
        )

        return {"symbol": symbol, "status": "saved", "quarter_end": str(qe)}

    except Exception as exc:
        return {"symbol": symbol, "status": "error", "reason": str(exc)}


# ── Main ───────────────────────────────────────────────────────────────────

def main(from_date: str = None, to_date: str = None, days: int = 7, max_workers: int = 4):

    today    = date.today()
    date_to  = to_date   or today.strftime("%d-%m-%Y")
    date_from = from_date or (today - timedelta(days=days)).strftime("%d-%m-%Y")

    print(f"\nFetching filings from {date_from} to {date_to}...")

    client    = NSEClient()
    downloader = FilingDownloader()

    # ── Step 1: Discover all filings in the window
    raw = discover_filings(client, date_from, date_to)
    print(f"  Total raw records: {len(raw)}")

    # ── Step 2: Filter to best consolidated filing per (symbol, quarter)
    targets = pick_best_filings(raw)
    print(f"  Unique consolidated targets: {len(targets)}")

    if not targets:
        print("Nothing to process.")
        return

    # ── Step 3: Load DB state once (avoid redundant queries per symbol)
    session = SessionLocal()
    known_symbols    = get_known_symbols(session)
    existing_filings = get_existing_filings(session)
    session.close()

    # ── Step 4: Process in parallel
    saved   = []
    skipped = []
    errors  = []

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(process_one, fm, known_symbols, existing_filings, downloader): fm
            for fm in targets
        }
        for future in as_completed(futures):
            result = future.result()
            status = result["status"]
            if status == "saved":
                saved.append(result["symbol"])
                print(f"  ✓  {result['symbol']} — saved {result['quarter_end']}")
            elif status == "skipped":
                skipped.append(result["symbol"])
                print(f"  –  {result['symbol']} — skipped ({result['reason']})")
            else:
                errors.append(result["symbol"])
                print(f"  ✗  {result['symbol']} — error: {result['reason']}")

    print("\n====================================")
    print(f"Saved   : {len(saved)}")
    print(f"Skipped : {len(skipped)}")
    print(f"Errors  : {len(errors)}")
    print("====================================")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--days",  type=int, default=7,    help="Lookback window in days (default: 7)")
    parser.add_argument("--from",  dest="from_date",       help="Start date dd-mm-yyyy")
    parser.add_argument("--to",    dest="to_date",         help="End date dd-mm-yyyy")
    parser.add_argument("--workers", type=int, default=4,  help="Parallel download threads (default: 4)")
    args = parser.parse_args()

    main(
        from_date=args.from_date,
        to_date=args.to_date,
        days=args.days,
        max_workers=args.workers,
    )