from sqlalchemy import Column, String, Float

from app.db.base import Base


class Company(Base):
    __tablename__ = "companies"

    symbol = Column(String, primary_key=True)

    company_name = Column(String)

    isin = Column(String)

    series = Column(String)

    listing_date = Column(String)

    face_value = Column(Float)