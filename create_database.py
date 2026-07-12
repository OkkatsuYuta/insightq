from app.db import engine, Base
from app.models import Company, ResultsCalendar, IntegratedFiling, FinancialMetric  # noqa: ensure all tables registered

Base.metadata.create_all(bind=engine)

print("Database created successfully.")
