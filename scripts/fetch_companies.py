from io import StringIO

import pandas as pd

from app.db import SessionLocal
from app.models import Company
from app.nse.client import NSEClient

NSE_URL = "https://archives.nseindia.com/content/equities/EQUITY_L.csv"


def download_company_list():
    print("Downloading company list...")

    client = NSEClient()

    csv_text = client.download_csv(NSE_URL)

    df = pd.read_csv(StringIO(csv_text))

    # Clean column names
    df.columns = (
        df.columns
        .str.strip()
        .str.replace("\ufeff", "", regex=False)
    )

    print("\nColumns found:")
    print(df.columns.tolist())

    print(f"\nFound {len(df)} companies")

    return df


def main():
    df = download_company_list()

    session = SessionLocal()

    inserted = 0
    updated = 0

    for _, row in df.iterrows():

        symbol = str(row["SYMBOL"]).strip()

        company = session.get(Company, symbol)

        company_name = row.get("NAME OF COMPANY")
        isin = row.get("ISIN NUMBER") or row.get("ISIN")
        series = row.get("SERIES")
        listing_date = row.get("DATE OF LISTING")
        face_value = row.get("FACE VALUE")

        if company is None:
            company = Company(
                symbol=symbol,
                company_name=company_name,
                isin=isin,
                series=series,
                listing_date=listing_date,
                face_value=float(face_value) if pd.notna(face_value) else None,
            )

            session.add(company)
            inserted += 1

        else:
            company.company_name = company_name
            company.isin = isin
            company.series = series
            company.listing_date = listing_date
            company.face_value = (
                float(face_value) if pd.notna(face_value) else None
            )

            updated += 1

    session.commit()
    session.close()

    print("\n===================================")
    print(f"Inserted : {inserted}")
    print(f"Updated  : {updated}")
    print("===================================")
    print("Database updated successfully!")


if __name__ == "__main__":
    main()