from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    Date,
    DateTime,
    UniqueConstraint,
)

from app.db.base import Base


class ResultsCalendar(Base):
    __tablename__ = "results_calendar"

    __table_args__ = (
        UniqueConstraint(
            "symbol",
            "meeting_date",
            "purpose",
            name="uq_results_calendar",
        ),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)

    symbol = Column(String, nullable=False)

    company_name = Column(String, nullable=False)

    purpose = Column(String, nullable=False)

    description = Column(Text)

    meeting_date = Column(Date)

    announcement_date = Column(DateTime)

    exchange = Column(String, default="NSE")

    status = Column(String, default="NEW")