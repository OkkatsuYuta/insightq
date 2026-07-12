"""
Saves a parsed, standardized Integrated Filing into the database.

Upserts on (symbol, quarter_end): re-running the pipeline for a company
that's already in the DB updates that quarter's numbers instead of
creating duplicate rows.
"""

from datetime import datetime
from types import SimpleNamespace

from app.db import SessionLocal
from app.models import IntegratedFiling, FinancialMetric
from app.extractors.financial_extractor import FinancialExtractor


def _parse_date(value):
    if not value:
        return None
    value = str(value).strip()
    for fmt in ("%d-%b-%Y", "%Y-%m-%d", "%d-%m-%Y"):
        try:
            return datetime.strptime(value, fmt).date()
        except ValueError:
            continue
    return None


def save_filing(
    symbol,
    company_name,
    metadata,
    standardized_metrics,
    ixbrl_url=None,
    xbrl_url=None,
    filing_date=None,
    filing_type=None,   # "quarterly" | "annual"
    session=None,
    is_revision=False,
):
    """
    Persist one filing + its standardized metrics.

    `metadata` is the dict returned by IntegratedFilingParser.parse()["metadata"].
    `standardized_metrics` is the dict returned by FinancialExtractor().extract():
    each value is either None or a {"quarter": str, "year": str} pair.
    `filing_date` is the date NSE actually published the filing (used to
    show only recently-released results on the dashboard). It's stored
    normalized as an ISO date string (YYYY-MM-DD) when parseable.
    """

    owns_session = session is None

    if owns_session:
        session = SessionLocal()

    try:
        quarter_end = _parse_date(metadata.get("quarter_end"))

        filing = (
            session.query(IntegratedFiling)
            .filter_by(symbol=symbol, quarter_end=quarter_end)
            .first()
        )

        if filing is None:
            filing = IntegratedFiling(
                symbol=symbol,
                company_name=company_name,
                quarter_end=quarter_end,
            )
            session.add(filing)
            session.flush()  # assign filing.id before attaching metrics
        else:
            filing.company_name = company_name

            # Replace old metrics for this filing rather than accumulating dupes
            session.query(FinancialMetric).filter_by(
                filing_id=filing.id
            ).delete()

        filing.audited = metadata.get("audited")
        filing.consolidated = metadata.get("consolidated")

        if filing_date:
            parsed_filing_date = _parse_date(filing_date)
            filing.filing_date = (
                parsed_filing_date.isoformat()
                if parsed_filing_date
                else str(filing_date)
            )

        if filing_type:
            filing.filing_type = filing_type
            filing.is_revision = is_revision

        if ixbrl_url:
            filing.ixbrl_url = ixbrl_url

        if xbrl_url:
            filing.xbrl_url = xbrl_url

        for metric_name, raw_value in standardized_metrics.items():

            if raw_value is None:
                quarter_value, year_value = None, None
            else:
                quarter_value = FinancialExtractor.to_float(raw_value.get("quarter"))
                year_value    = FinancialExtractor.to_float(raw_value.get("year"))

            session.add(
                FinancialMetric(
                    filing_id=filing.id,
                    metric=metric_name,
                    quarter_value=quarter_value,
                    year_value=year_value,
                )
            )

        session.commit()

        summary = SimpleNamespace(
            id=filing.id,
            symbol=filing.symbol,
            company_name=filing.company_name,
            quarter_end=filing.quarter_end,
            filing_date=filing.filing_date if hasattr(filing, "filing_date") else None,
            filing_type=filing.filing_type if hasattr(filing, "filing_type") else None,
        )

        return summary

    finally:
        if owns_session:
            session.close()
