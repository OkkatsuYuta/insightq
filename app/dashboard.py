import sqlite3
from pathlib import Path
from flask import Flask, jsonify, render_template, request

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH  = BASE_DIR / "data" / "earnings_tracker.db"

if not DB_PATH.exists():
    import subprocess
    subprocess.run(["python", "create_database.py"], cwd=BASE_DIR)

DASHBOARD_METRICS = [
    "total_income",
    "total_expense",
    "net_profit",
    "profit_before_tax",
    "eps_basic",
]

UPCOMING_WINDOW_DAYS = 28
RELEASED_WINDOW_DAYS = 7

app = Flask(__name__)


def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def _attach_metrics(conn, filings):
    """Add metric values to a list of filing dicts."""
    placeholders = ",".join("?" * len(DASHBOARD_METRICS))
    results = []
    for f in filings:
        rows = conn.execute(
            f"""
            SELECT metric, quarter_value FROM financial_metrics
            WHERE filing_id = ? AND metric IN ({placeholders})
            """,
            [f["id"], *DASHBOARD_METRICS],
        ).fetchall()
        m = {r["metric"]: r["quarter_value"] for r in rows}
        results.append({
            "symbol":        f["symbol"],
            "company_name":  f["company_name"],
            "quarter_end":   f["quarter_end"],
            "filing_date":   f["filing_date"],
            "filing_type":   f["filing_type"] if "filing_type" in f.keys() else None,
            "consolidated":  f["consolidated"],
            "total_income":  m.get("total_income"),
            "total_expense": m.get("total_expense"),
            "pat":           m.get("net_profit"),
            "pbt":           m.get("profit_before_tax"),
            "eps":           m.get("eps_basic"),
            "consolidated":  f["consolidated"],
            "is_revision":   f["is_revision"] if "is_revision" in f.keys() else False,
        })
    return results


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/upcoming")
def api_upcoming():
    conn = get_conn()
    rows = conn.execute(
        f"""
        SELECT symbol, company_name, MIN(meeting_date) AS meeting_date, purpose
        FROM results_calendar
        WHERE meeting_date BETWEEN date('now') AND date('now', '+{UPCOMING_WINDOW_DAYS} days')
        GROUP BY symbol
        ORDER BY meeting_date ASC
        """
    ).fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])


@app.route("/api/released")
def api_released():
    """
    Companies that announced Financial Results in the last 14 days.
    - If we have filing data: show figures
    - If not: show as a card with no figures so user can tap to fetch
    """
    conn = get_conn()

    # All companies with saved filing data (no date filter)
    filings = conn.execute(
        """
        SELECT f.id, f.symbol, f.company_name, f.quarter_end,
               f.filing_date, f.consolidated, f.is_revision,
               COALESCE(f.filing_type, 'quarterly') AS filing_type
        FROM integrated_filings f
        WHERE COALESCE(f.filing_type, 'quarterly') = 'quarterly'
        AND f.quarter_end = (
            SELECT MAX(f2.quarter_end)
            FROM   integrated_filings f2
            WHERE  f2.symbol = f.symbol
            AND    COALESCE(f2.filing_type, 'quarterly') = 'quarterly'
        )
        ORDER BY COALESCE(f.filing_date, f.quarter_end) DESC
        """
    ).fetchall()

    filed_symbols = {f["symbol"] for f in filings}
    results = _attach_metrics(conn, filings)

    # Companies that announced results in the last 14 days but no filing data yet
    announced = conn.execute(
        """
        SELECT symbol, company_name, MAX(meeting_date) AS meeting_date
        FROM results_calendar
        WHERE meeting_date BETWEEN date('now', '-14 days') AND date('now')
        GROUP BY symbol
        ORDER BY meeting_date DESC
        """
    ).fetchall()

    for row in announced:
        if row["symbol"] not in filed_symbols:
            results.append({
                "symbol":        row["symbol"],
                "company_name":  row["company_name"],
                "quarter_end":   None,
                "filing_date":   row["meeting_date"],
                "consolidated":  None,
                "total_income":  None,
                "total_expense": None,
                "pat":           None,
                "pbt":           None,
                "eps":           None,
                "no_data":       True,
            })

    conn.close()
    return jsonify(results)


@app.route("/api/symbol/<symbol>")
def api_symbol(symbol):
    """
    Return 3 rows for ONE symbol:
      1. Current quarter  (quarter_value from latest filing)
      2. Previous quarter (quarter_value from previous filing)
      3. Full year        (year_value from latest filing)
    """
    conn = get_conn()

    filings = conn.execute(
        """
        SELECT id, symbol, company_name, quarter_end, filing_date,
               consolidated, COALESCE(filing_type, 'quarterly') AS filing_type
        FROM   integrated_filings
        WHERE  symbol = ?
        ORDER  BY quarter_end DESC
        LIMIT  2
        """,
        [symbol.upper()],
    ).fetchall()

    if not filings:
        conn.close()
        return jsonify([])

    placeholders = ",".join("?" * len(DASHBOARD_METRICS))
    results = []

    for i, filing in enumerate(filings):
        rows = conn.execute(
            f"""
            SELECT metric, quarter_value, year_value FROM financial_metrics
            WHERE filing_id = ? AND metric IN ({placeholders})
            """,
            [filing["id"], *DASHBOARD_METRICS],
        ).fetchall()
        m_q = {r["metric"]: r["quarter_value"] for r in rows}
        m_y = {r["metric"]: r["year_value"]    for r in rows}

        # Quarter row
        results.append({
            "symbol":        filing["symbol"],
            "company_name":  filing["company_name"],
            "quarter_end":   filing["quarter_end"],
            "filing_date":   filing["filing_date"],
            "consolidated":  filing["consolidated"],
            "row_type":      "current_quarter" if i == 0 else "previous_quarter",
            "total_income":  m_q.get("total_income"),
            "total_expense": m_q.get("total_expense"),
            "pat":           m_q.get("net_profit"),
            "pbt":           m_q.get("profit_before_tax"),
            "eps":           m_q.get("eps_basic"),
        })

        # Full year row — only from the latest (first) filing
        if i == 0:
            results.append({
                "symbol":        filing["symbol"],
                "company_name":  filing["company_name"],
                "quarter_end":   filing["quarter_end"],
                "filing_date":   filing["filing_date"],
                "consolidated":  filing["consolidated"],
                "row_type":      "full_year",
                "total_income":  m_y.get("total_income"),
                "total_expense": m_y.get("total_expense"),
                "pat":           m_y.get("net_profit"),
                "pbt":           m_y.get("profit_before_tax"),
                "eps":           m_y.get("eps_basic"),
            })

    conn.close()
    return jsonify(results)


@app.route("/api/companies/search")
def api_companies_search():
    q = request.args.get("q", "").strip()
    if not q:
        return jsonify([])
    conn = get_conn()
    rows = conn.execute(
        """
        SELECT symbol, company_name FROM companies
        WHERE  symbol LIKE ? OR company_name LIKE ?
        ORDER  BY symbol LIMIT 15
        """,
        (f"%{q}%", f"%{q}%"),
    ).fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])


@app.route("/api/fetch/<symbol>", methods=["POST"])
def api_fetch_symbol(symbol):
    from scripts.fetch_earnings import fetch_and_save_latest
    try:
        result = fetch_and_save_latest(symbol)
    except Exception as exc:
        return jsonify({"ok": False, "symbol": symbol.upper(), "error": str(exc)}), 502
    return jsonify(result), (200 if result.get("ok") else 404)

@app.route("/api/calendar")
def api_calendar():
    year  = request.args.get("year",  type=int)
    month = request.args.get("month", type=int)
    if not year or not month:
        from datetime import date as _date
        today = _date.today()
        year, month = today.year, today.month

    # Format month boundaries
    from datetime import date as _date
    import calendar as _cal
    last_day = _cal.monthrange(year, month)[1]
    m_start  = f"{year}-{month:02d}-01"
    m_end    = f"{year}-{month:02d}-{last_day:02d}"

    conn = get_conn()

    # Released: filings whose filing_date falls in this month
    filings = conn.execute(
        """
        SELECT f.id, f.symbol, f.company_name, f.filing_date, f.quarter_end
        FROM   integrated_filings f
        WHERE  COALESCE(f.filing_type, 'quarterly') = 'quarterly'
        AND    f.filing_date BETWEEN ? AND ?
        AND    f.quarter_end = (
            SELECT MAX(f2.quarter_end)
            FROM   integrated_filings f2
            WHERE  f2.symbol = f.symbol
        )
        """,
        [m_start, m_end],
    ).fetchall()

    # Get PAT for each filing
    released_by_date = {}
    for f in filings:
        pat_row = conn.execute(
            """
            SELECT quarter_value FROM financial_metrics
            WHERE filing_id = ? AND metric = 'net_profit'
            """,
            [f["id"]],
        ).fetchone()
        pat = pat_row["quarter_value"] if pat_row else None
        date_key = f["filing_date"][:10] if f["filing_date"] else None
        if not date_key:
            continue
        if date_key not in released_by_date:
            released_by_date[date_key] = []
        released_by_date[date_key].append({
            "symbol":       f["symbol"],
            "company_name": f["company_name"],
            "pat":          pat,
        })

    # Upcoming: board meetings in this month
    upcoming = conn.execute(
        """
        SELECT symbol, company_name, meeting_date
        FROM   results_calendar
        WHERE  meeting_date BETWEEN ? AND ?
        ORDER  BY meeting_date ASC
        """,
        [m_start, m_end],
    ).fetchall()

    upcoming_by_date = {}
    for r in upcoming:
        date_key = str(r["meeting_date"])
        if date_key not in upcoming_by_date:
            upcoming_by_date[date_key] = []
        upcoming_by_date[date_key].append({
            "symbol":       r["symbol"],
            "company_name": r["company_name"],
        })

    conn.close()

    # Merge into one dict keyed by date
    all_dates = set(released_by_date) | set(upcoming_by_date)
    result = {}
    for d in all_dates:
        result[d] = {
            "released": released_by_date.get(d, []),
            "upcoming": upcoming_by_date.get(d, []),
        }

    return jsonify(result)

if __name__ == "__main__":
    app.run(debug=True, port=5000)
