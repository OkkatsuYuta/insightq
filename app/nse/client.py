import requests

from app.config import NSE_BASE_URL, HEADERS


class NSEClient:

    def __init__(self):

        self.session = requests.Session()

        self.session.headers.update(HEADERS)

        # Get NSE cookies
        self.session.get(NSE_BASE_URL)

    # ----------------------------------------------------------
    # Generic JSON Request
    # ----------------------------------------------------------

    def get_json(self, endpoint, params=None):

        url = f"{NSE_BASE_URL}{endpoint}"

        response = self.session.get(
            url,
            params=params,
            timeout=30
        )

        response.raise_for_status()

        return response.json()

    # ----------------------------------------------------------
    # Generic CSV Download
    # ----------------------------------------------------------

    def download_csv(self, url):

        print(f"Downloading from: {url}")

        response = self.session.get(
            url,
            timeout=30
        )

        response.raise_for_status()

        return response.text

    # ----------------------------------------------------------
    # Company Master
    # ----------------------------------------------------------

    def get_company_list_csv(self):

        return self.download_csv(
            "https://archives.nseindia.com/content/equities/EQUITY_L.csv"
        )

    # ----------------------------------------------------------
    # Event Calendar
    # ----------------------------------------------------------

    def get_event_calendar(self, index="equities", event_type=None):

        params = {
            "index": index
        }

        if event_type:
            params["type"] = event_type

        return self.get_json(
            "/api/event-calendar",
            params=params
        )