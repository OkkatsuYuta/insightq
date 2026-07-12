from datetime import datetime, date, timedelta

from app.db import SessionLocal
from app.models import ResultsCalendar
from app.nse.client import NSEClient

LOOKAHEAD_DAYS = 28  # next 4 weeks


def main():

    client  = NSEClient()
    session = SessionLocal()

    today      = date.today()
    window_end = today + timedelta(days=LOOKAHEAD_DAYS)

    inserted = 0
    updated  = 0

    print("Fetching upcoming events...")

    events = client.get_event_calendar()

    for event in events:
        purpose = event.get("purpose", "")
        if "Financial Results" not in purpose:
            continue

        try:
            meeting_date = datetime.strptime(event["date"], "%d-%b-%Y").date()
        except (ValueError, KeyError):
            continue

        if not (today <= meeting_date <= window_end):
            continue

        symbol   = event["symbol"]
        existing = (
            session.query(ResultsCalendar)
            .filter_by(symbol=symbol, meeting_date=meeting_date, purpose=purpose)
            .first()
        )

        if existing:
            existing.company_name = event["company"]
            existing.description  = event.get("bm_desc")
            existing.exchange     = "NSE"
            updated += 1
        else:
            session.add(ResultsCalendar(
                symbol       = symbol,
                company_name = event["company"],
                purpose      = purpose,
                description  = event.get("bm_desc"),
                meeting_date = meeting_date,
                exchange     = "NSE",
            ))
            inserted += 1

    # Remove events outside the window
    stale = (
        session.query(ResultsCalendar)
        .filter(
            (ResultsCalendar.meeting_date < today)
            | (ResultsCalendar.meeting_date > window_end)
        )
        .delete(synchronize_session=False)
    )

    session.commit()
    session.close()

    print(f"  Processed {len(events)} events")
    print("\n====================================")
    print(f"Inserted      : {inserted}")
    print(f"Updated       : {updated}")
    print(f"Removed stale : {stale}")
    print("====================================")


if __name__ == "__main__":
    main()