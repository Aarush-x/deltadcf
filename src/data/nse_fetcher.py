import requests
from typing import Optional, List, Dict
import time

class NSEFetcher:
    """
    Handles retrieval of annual report URLs from NSE India.
    Requires session/cookie management to bypass bot protection.
    """
    
    def __init__(self):
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "Referer": "https://www.nseindia.com/"
        }
        self.session = requests.Session()
        self.cookies_initialized = False

    def _init_session(self):
        """Fetches initial cookies from NSE homepage."""
        if not self.cookies_initialized:
            print("Initializing NSE session...")
            try:
                self.session.get("https://www.nseindia.com", headers=self.headers, timeout=10)
                self.cookies_initialized = True
            except Exception as e:
                print(f"Failed to initialize NSE session: {e}")

    def get_latest_annual_report_url(self, symbol: str) -> Optional[str]:
        """Fetches the latest annual report PDF URL for a given symbol."""
        self._init_session()
        
        # Clean symbol (remove .NS)
        clean_symbol = symbol.replace(".NS", "").upper()
        api_url = f"https://www.nseindia.com/api/annual-reports?symbol={clean_symbol}&index=equities"
        
        try:
            # Adding a small delay to avoid aggressive rate limiting
            time.sleep(1)
            response = self.session.get(api_url, headers=self.headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json().get('data', [])
                if data:
                    # Reports are usually sorted by year; get the first one
                    latest_report = data[0]
                    url = latest_report.get('url')
                    print(f"Found latest NSE report for {clean_symbol}: {latest_report.get('financialYear')}")
                    return url
            else:
                print(f"NSE API error ({response.status_code}) for {clean_symbol}")
                
        except Exception as e:
            print(f"Error fetching report URL from NSE: {e}")
            
        return None

if __name__ == "__main__":
    fetcher = NSEFetcher()
    print(f"URL: {fetcher.get_latest_annual_report_url('INFY')}")
