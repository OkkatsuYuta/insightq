"""
Fetches the 2 most recent Consolidated quarterly filings per company.
The full-year figures are embedded inside each quarterly filing and
stored automatically in the year_value column alongside quarter_value.

Usage:
    python -m scripts.fetch_earnings TCS INFY HDFCBANK
"""

import sys

from app.db import SessionLocal
from app.models import Company
from app.providers.integrated_filings import IntegratedFilingDiscovery, _parse_broadcast_date
from app.clients.filing_downloader import FilingDownloader
from app.parsers.integrated_filing_parser import IntegratedFilingParser
from app.extractors.financial_extractor import FinancialExtractor
from app.importers.filing_importer import save_filing


def get_company_name(symbol):
    session = SessionLocal()
    try:
        company = session.get(Company, symbol.upper())
        return company.company_name if company else None
    finally:
        session.close()


def fetch_and_save_latest(symbol, company_name=None, discovery=None, downloader=None):
    """
    Fetch + parse + save the 3 most recent consolidated quarterly
    filings for one company. Returns a dict describing the primary
    (most recent) filing result.
    """

    symbol = symbol.upper().strip()

    if company_name is None:
        company_name = get_company_name(symbol)

    if not company_name:
        return {
            "ok":     False,
            "symbol": symbol,
            "error":  (
                f"'{symbol}' not found in companies table. "
                "Run `python -m scripts.fetch_companies` first."
            ),
        }

    discovery = discovery or IntegratedFilingDiscovery()
    downloader = downloader or FilingDownloader()

    targets = discovery.get_target_filings(symbol=symbol, issuer=company_name)

    if not targets:
        return {
            "ok":     False,
            "symbol": symbol,
            "error":  f"No consolidated filings found for {symbol} on NSE.",
        }

    LABELS = ["Current quarter", "Previous quarter"]
    primary_result = None

    from concurrent.futures import ThreadPoolExecutor, as_completed

    def process_filing(args):
        i, filing_meta = args
        ixbrl_url = filing_meta.get("ixbrl")
        if not ixbrl_url:
            return i, None, "no ixbrl url"
        try:
            html         = downloader.download_html(ixbrl_url)
            parsed       = IntegratedFilingParser(html).parse()
            metadata     = parsed["metadata"]
            metadata.setdefault("company_name", company_name)
            standardized = FinancialExtractor(parsed).extract()
            bd           = _parse_broadcast_date(filing_meta)
            filing_date  = bd.strftime("%Y-%m-%d") if bd else None
            saved        = save_filing(
                symbol=symbol,
                company_name=company_name,
                metadata=metadata,
                standardized_metrics=standardized,
                ixbrl_url=ixbrl_url,
                xbrl_url=filing_meta.get("xbrl"),
                filing_date=filing_date,
                filing_type="quarterly",
            )
            return i, saved, None
        except Exception as exc:
            return i, None, str(exc)

    results = {}
    with ThreadPoolExecutor(max_workers=2) as executor:
        futures = {executor.submit(process_filing, (i, fm)): i for i, fm in enumerate(targets)}
        for future in as_completed(futures):
            i, saved, err = future.result()
            label = LABELS[i] if i < len(LABELS) else f"Quarter -{i+1}"
            if err:
                print(f"  [{label}] failed: {err}")
            else:
                print(f"  [{label}] saved quarter_end={saved.quarter_end}")
                results[i] = saved

    if 0 in results:
        saved = results[0]
        primary_result = {
            "ok":           True,
            "symbol":       symbol,
            "company_name": company_name,
            "quarter_end":  str(saved.quarter_end) if saved.quarter_end else None,
            "filing_date":  saved.filing_date,
            "filing_type":  "quarterly",
        }

    if primary_result:
        return primary_result

    return {
        "ok":     False,
        "symbol": symbol,
        "error":  "All filing downloads failed.",
    }


def main():
    symbols = sys.argv[1:]

    if not symbols:
        print("Usage: python -m scripts.fetch_earnings SYMBOL [SYMBOL ...]")
        print("Example: python -m scripts.fetch_earnings TCS INFY HDFCBANK")
        return

    discovery = IntegratedFilingDiscovery()
    downloader = FilingDownloader()

    saved = 0
    skipped = 0

    for symbol in symbols:
        print(f"\n--- {symbol} ---")
        try:
            result = fetch_and_save_latest(
                symbol, discovery=discovery, downloader=downloader
            )
        except Exception as exc:
            print(f"Error: {exc}")
            skipped += 1
            continue

        if result["ok"]:
            saved += 1
        else:
            print(result["error"])
            skipped += 1

    print("\n====================================")
    print(f"Saved   : {saved}")
    print(f"Skipped : {skipped}")
    print("====================================")


if __name__ == "__main__":
    main()
