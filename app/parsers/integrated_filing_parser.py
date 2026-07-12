import re
from bs4 import BeautifulSoup


def _clean(text):
    """Collapse whitespace and newlines in a cell's text."""
    return re.sub(r"\s+", " ", text).strip()


class IntegratedFilingParser:
    """
    Parses an NSE Integrated Filing iXBRL HTML document.

    NSE filings follow a consistent table layout:
      Table 0  — filing metadata (2-col: label | value)
      Table 1  — Income Statement (4-col: idx | label | quarter | year)
      Table 3  — Balance Sheet   (2-col: label | year-end only)
      Table 6  — Cash Flow       (2-col: label | year-end only)

    We detect each table by keyword scoring rather than fixed indices
    so the parser is robust to NSE adding/removing tables over time.
    """

    INCOME_KEYWORDS = [
        "Revenue from operations",
        "Total income",
        "Employee benefit expense",
        "Total expenses",
        "Total profit before tax",
        # Banking sector
        "Total interest earned",
        "Interest expenses",
        "Total expenditure excluding provisions and contingencies",
        "Total profit (loss) from ordinary activities before tax",
    ]

    BALANCE_KEYWORDS = [
        "Total assets",
        "Total equity",
        "Total liabilities",
        "Property, plant and equipment",
        "Cash and cash equivalents",
    ]

    CASHFLOW_KEYWORDS = [
        "Net cash flows from",
        "Cash flows from",
        "Profit before tax",
        "Income taxes paid",
    ]

    METADATA_KEYWORDS = [
        "Name of company",
        "Date of end of financial year",
        "Nature of report standalone or consolidated",
        "Whether results are audited or unaudited",
    ]

    def __init__(self, html: str):
        self.soup   = BeautifulSoup(html, "lxml")
        self.tables = self.soup.find_all("table")

    # ── Table finder ────────────────────────────────────────

    def _find_table(self, keywords, min_score=2):
        best, best_score = None, 0
        for table in self.tables:
            text  = table.get_text(" ", strip=True)
            score = sum(1 for kw in keywords if kw.lower() in text.lower())
            if score > best_score:
                best_score, best = score, table
        return best if best_score >= min_score else None

    # ── Generic 4-column extractor (income statement) ───────
    # Columns: [index] [label] [quarter_value] [year_value]

    def _extract_4col(self, table):
        if table is None:
            return {}
        data = {}
        for row in table.find_all("tr"):
            cols = [_clean(c.get_text(" ", strip=True))
                    for c in row.find_all(["th", "td"])]
            if len(cols) < 4:
                continue
            label = cols[1]
            if not label or label.lower().startswith("date of") \
                    or label.lower().startswith("whether") \
                    or label.lower().startswith("nature of"):
                continue
            data[label] = {
                "quarter": cols[2],
                "year":    cols[3],
            }
        return data

    # ── Generic 2-column extractor (balance sheet / cashflow)
    # Columns: [label] [year_value]   (no quarter column)

    def _extract_2col(self, table):
        if table is None:
            return {}
        data = {}
        for row in table.find_all("tr"):
            cols = [_clean(c.get_text(" ", strip=True))
                    for c in row.find_all(["th", "td"])]
            # Accept rows with 2 OR 3 cols (some have a leading index)
            if len(cols) == 2:
                label, value = cols
            elif len(cols) >= 3:
                # last non-empty col is the value; second-to-last is label
                label = cols[-2]
                value = cols[-1]
            else:
                continue
            if not label or not value:
                continue
            # Skip header/meta rows
            if label.lower().startswith("date of") \
                    or label.lower().startswith("whether") \
                    or label.lower().startswith("nature of") \
                    or label.lower() == "particulars":
                continue
            # Store as year value; quarter stays None for balance sheet
            data[label] = {"quarter": None, "year": value}
        return data

    # ── Metadata ─────────────────────────────────────────────

    def extract_metadata(self):
        meta = {
            "company_name": None,
            "quarter_end":  None,
            "audited":      None,
            "consolidated": None,
        }

        table = self._find_table(self.METADATA_KEYWORDS, min_score=2)
        if not table:
            return meta

        for row in table.find_all("tr"):
            cols = [_clean(c.get_text(" ", strip=True))
                    for c in row.find_all(["th", "td"])]

            # Metadata table is 2-col: label | value
            if len(cols) < 2:
                continue

            label = cols[0].lower()
            value = cols[1] if len(cols) > 1 else ""

            if "name of company" in label or "name of bank" in label:
                meta["company_name"] = value

            elif "date of end of financial year" in label \
                    or "date of end of reporting period" in label:
                # Prefer "date of end of reporting period" from income table
                # but fall back to financial year end from metadata table
                if meta["quarter_end"] is None:
                    meta["quarter_end"] = value

            elif "audited or unaudited" in label:
                if meta["audited"] is None:
                    meta["audited"] = value

            elif "standalone or consolidated" in label:
                if meta["consolidated"] is None:
                    meta["consolidated"] = value

        # Also try to get the more precise quarter-end date from the
        # income statement table rows A/B (Date of end of reporting period)
        income_table = self._find_table(self.INCOME_KEYWORDS)
        if income_table:
            for row in income_table.find_all("tr"):
                cols = [_clean(c.get_text(" ", strip=True))
                        for c in row.find_all(["th", "td"])]
                if len(cols) >= 3:
                    label = cols[1].lower() if len(cols) > 2 else cols[0].lower()
                    value = cols[2] if len(cols) > 2 else cols[1]
                    if "date of end of reporting period" in label and value:
                        meta["quarter_end"] = value
                        break

        return meta

    # ── Main parse ───────────────────────────────────────────

    def parse(self):
        income_table   = self._find_table(self.INCOME_KEYWORDS)
        balance_table  = self._find_table(self.BALANCE_KEYWORDS)
        cashflow_table = self._find_table(self.CASHFLOW_KEYWORDS)

        return {
            "metadata":         self.extract_metadata(),
            "income_statement": self._extract_4col(income_table),
            "balance_sheet":    self._extract_2col(balance_table),
            "cash_flow":        self._extract_2col(cashflow_table),
        }
