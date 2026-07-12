from app.nse.client import NSEClient
from datetime import date, timedelta

client = NSEClient()
today  = date.today()
data   = client.get_json(
    "/api/integrated-filing-results",
    params={
        "index":     "equities",
        "from_date": (today - timedelta(days=7)).strftime("%d-%m-%Y"),
        "to_date":   today.strftime("%d-%m-%Y"),
        "type":      "Integrated Filing- Financials",
        "page":      1,
        "size":      20,
    }
)
for f in data.get("data", []):
    print(f.get("symbol"), "|", repr(f.get("consolidated")), "|", repr(f.get("type_Sub")))