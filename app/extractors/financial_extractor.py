from app.mappings.financial_mappings import STANDARD_METRICS
import re


def _normalize(text):
    """Collapse all whitespace so newlines in NSE labels don't break matching."""
    return re.sub(r"\s+", " ", text or "").strip()


class FinancialExtractor:
    """
    Converts raw parsed financial statements into
    standardized financial metrics.
    """

    def __init__(self, parsed_statements):
        self.parsed = parsed_statements

    def extract(self):
        standardized = {}

        # Combine all statements, normalizing every key
        all_items = {}
        for statement_name in ("income_statement", "balance_sheet", "cash_flow"):
            for label, value in self.parsed.get(statement_name, {}).items():
                all_items[_normalize(label)] = value

        # Match each standard metric against normalized labels
        for metric, possible_labels in STANDARD_METRICS.items():
            standardized[metric] = None
            for label in possible_labels:
                normalized_label = _normalize(label)
                if normalized_label in all_items:
                    standardized[metric] = all_items[normalized_label]
                    break

        return standardized
    
    @staticmethod
    def to_float(value):
        """
        Convert NSE numeric strings into float.
        Handles Indian comma formatting and bracket notation for negatives:
          '70,69,800.00'  ->  7069800.0
          '(4,52,600.00)' -> -452600.0
        """

        if value is None:
            return None

        value = str(value).strip()

        if value in ("", "-", "—"):
            return None

        # Brackets mean negative: (1,000.00) -> -1000.0
        negative = value.startswith("(") and value.endswith(")")
        if negative:
            value = value[1:-1]

        value = value.replace(",", "")

        try:
            result = float(value)
            return -result if negative else result
        except ValueError:
            return None