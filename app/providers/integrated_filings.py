from datetime import datetime
from app.nse.client import NSEClient


def _parse_qe_date(filing):
    """Parse qe_Date field like '31-MAR-2026' into a date object."""
    val = filing.get("qe_Date", "")
    if not val:
        return None
    for fmt in ("%d-%b-%Y", "%d-%B-%Y", "%Y-%m-%d"):
        try:
            return datetime.strptime(val.strip(), fmt).date()
        except ValueError:
            continue
    return None


def _parse_broadcast_date(filing):
    """Parse broadcast_Date like '09-Apr-2026 23:42:16'."""
    val = filing.get("broadcast_Date", "")
    if not val:
        return None
    for fmt in ("%d-%b-%Y %H:%M:%S", "%d-%B-%Y %H:%M:%S"):
        try:
            return datetime.strptime(val.strip(), fmt)
        except ValueError:
            continue
    return None


class IntegratedFilingDiscovery:
    """
    Discover available Integrated Financial Filings for a given NSE company.

    NSE returns filings newest-first. Each quarter has two filings:
    Consolidated and Standalone. We always prefer Consolidated.

    There are no separate "annual" filings — the year-to-date figures
    are embedded as year_value in each quarterly filing's HTML.

    We fetch the 3 most recent CONSOLIDATED quarterly filings:
      1. Current quarter
      2. Previous quarter
      3. Quarter before that (effectively last year's Q4 if current is Q1)
    """

    def __init__(self):
        self.client = NSEClient()

    def get_filings(self, symbol: str, issuer: str, page: int = 1, size: int = 6):
        data = self.client.get_json(
            "/api/integrated-filing-results",
            params={
                "index":        "equities",
                "symbol":       symbol,
                "issuer":       issuer,
                "period_ended": "all",
                "type":         "Integrated Filing- Financials",
                "page":         page,
                "size":         size,
            },
        )
        return data.get("data", [])

    def get_latest_filing(self, symbol: str, issuer: str):
        """Return the most recent Consolidated filing."""
        filings = self.get_filings(symbol, issuer, size=10)
        for f in filings:
            if f.get("consolidated", "").strip().lower() == "consolidated":
                return f
        # Fall back to first filing if no consolidated found
        return filings[0] if filings else None

    def get_target_filings(self, symbol: str, issuer: str):
        """
        Return the 3 most recent Consolidated quarterly filings,
        deduplicated by quarter-end date (qe_Date).

        Returns list of filing dicts ordered newest -> oldest.
        """
        filings = self.get_filings(symbol, issuer, size=20)

        seen_quarters = set()
        targets = []

        for f in filings:
            # Only take Consolidated
            if f.get("consolidated", "").strip().lower() != "consolidated":
                continue

            # Skip if no ixbrl URL
            if not f.get("ixbrl"):
                continue

            qe = _parse_qe_date(f)
            if qe is None:
                continue

            # One filing per quarter-end date
            if qe in seen_quarters:
                continue

            seen_quarters.add(qe)
            targets.append(f)

            if len(targets) == 2:
                break

        return targets
