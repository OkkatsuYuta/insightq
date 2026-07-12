from app.nse.client import NSEClient


class FilingDownloader:
    """
    Downloads Integrated Filing HTML pages from NSE.
    """

    def __init__(self):
        self.client = NSEClient()

    def download_html(self, url: str) -> str:
        """
        Download the HTML page of an Integrated Filing.
        """

        response = self.client.session.get(
            url,
            timeout=30
        )

        response.raise_for_status()

        return response.text