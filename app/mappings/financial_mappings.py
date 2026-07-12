"""
Standard financial metric mappings.

Keys are our internal metric names.
Values are all label variants seen in real NSE iXBRL filings.
Labels are matched after collapsing whitespace, so newlines / extra
spaces in the raw HTML don't matter.
"""

STANDARD_METRICS = {

    "revenue": [
        "Revenue from operations",
        "Revenue",
        "Income from operations",
    ],

    "other_income": [
        "Other income",
    ],

    "total_income": [
        "Total income",
    ],

    "total_expense": [
        "Total expenses",
        "Total expense",
        # Banking sector
        "Total expenditure excluding provisions and contingencies",
    ],

    "employee_cost": [
        "Employee benefit expense",
        "Employee benefits expense",
    ],

    "finance_cost": [
        "Finance costs",
        "Finance cost",
    ],

    "depreciation": [
        # NSE iXBRL exact label
        "Depreciation, depletion and amortisation expense",
        "Depreciation and amortisation expense",
        "Depreciation",
    ],

    "profit_before_tax": [
        # NSE iXBRL uses "Total profit before tax"
        "Total profit before tax",
        "Profit before tax",
        "Profit before exceptional items and tax",
        "Total profit before exceptional items and tax",
        # Banking sector
        "Total profit (loss) from ordinary activities before tax",
    ],

    "tax_expense": [
        "Total tax expenses",
        "Tax expense",
        "Current tax",
    ],

    "net_profit": [
        # NSE iXBRL exact label (with collapsed whitespace)
        "Total profit (loss) for period",
        "Net Profit Loss for the period from continuing operations",
        "Profit for the period",
        "Profit after tax",
        "Net Profit",
        "Net profit",
        # Banking sector
        "Net profit (loss) for the period",
        "Net profit (loss) from ordinary activities after tax",
        "Net Profit (loss) after taxes minority interest and share of profit (loss) of associates",
    ],

    "eps_basic": [
        # NSE iXBRL exact labels (whitespace collapsed)
        "Basic earnings (loss) per share from continuing and discontinued operations",
        "Basic earnings (loss) per share from continuing operations",
        "Basic earnings per share",
        "Basic EPS",
        # Banking sector
        "Basic earnings per share before extraordinary items",
        "Basic earnings per share after extraordinary items",
    ],

    "eps_diluted": [
        "Diluted earnings (loss) per share from continuing and discontinued operations",
        "Diluted earnings (loss) per share from continuing operations",
        "Diluted earnings per share",
        "Diluted EPS",
        # Banking sector
        "Diluted earnings per share before extraordinary items",
        "Diluted earnings per share after extraordinary items",
    ],

    "total_assets": [
        "Total assets",
    ],

    "total_equity": [
        "Total equity",
        "Equity",
    ],

    "total_liabilities": [
        "Total liabilities",
        "Total equity and liabilites",   # NSE typo present in real filings
    ],

    "cash_equivalents": [
        "Cash and cash equivalents cash flow statement",
        "Cash and cash equivalents",
    ],
}
