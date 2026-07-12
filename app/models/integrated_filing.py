from datetime import datetime

from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    Date,
    DateTime,
    ForeignKey,
    Boolean,
)

from sqlalchemy.orm import relationship

from app.db.base import Base


class IntegratedFiling(Base):
    __tablename__ = "integrated_filings"

    id = Column(Integer, primary_key=True)

    symbol = Column(String, index=True)

    company_name = Column(String)

    quarter_end = Column(Date)

    filing_date = Column(String)

    audited = Column(String)

    consolidated = Column(String)

    ixbrl_url = Column(String)

    xbrl_url = Column(String)

    filing_type = Column(String)   # "quarterly" | "annual"

    created_at = Column(DateTime, default=datetime.utcnow)

    is_revision = Column(Boolean, default=False)

    metrics = relationship(
        "FinancialMetric",
        back_populates="filing",
        cascade="all, delete-orphan",
    )


class FinancialMetric(Base):
    __tablename__ = "financial_metrics"

    id = Column(Integer, primary_key=True)

    filing_id = Column(
        Integer,
        ForeignKey("integrated_filings.id"),
        nullable=False,
    )

    metric = Column(String, index=True)

    quarter_value = Column(Float)

    year_value = Column(Float)

    filing = relationship(
        "IntegratedFiling",
        back_populates="metrics",
    )