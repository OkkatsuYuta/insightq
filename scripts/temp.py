import requests

session = requests.Session()
session.headers.update({
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://archives.nseindia.com/",
})
session.get("https://www.nseindia.com", timeout=10)
session.get("https://archives.nseindia.com", timeout=10)
r = session.get("https://archives.nseindia.com/content/equities/EQUITY_L.csv", timeout=30)
print(r.status_code)
print(dict(r.headers))