import requests
from typing import Optional, Dict
import time

class BSEFetcher:
    """
    Handles retrieval of annual report URLs from BSE India.
    BSE is often more bot-friendly than NSE but requires 6-digit Scrip Codes.
    """
    
    # Common Nifty 50 Ticker to BSE Scrip Code mapping
    SYMBOL_TO_BSE = {
        "RELIANCE": "500325",
        "INFY": "500209",
        "TCS": "532540",
        "HDFCBANK": "500180",
        "ICICIBANK": "532174",
        "HINDUNILVR": "500696",
        "SBIN": "500112",
        "BHARTIARTL": "532454",
        "ITC": "500875",
        "KOTAKBANK": "532276"
    }

    def __init__(self):
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
            "Referer": "https://www.bseindia.com/",
            "Accept": "application/json, text/plain, */*"
        }
        self.session = requests.Session()

    def get_latest_annual_report_url(self, symbol: str) -> Optional[str]:
        """Fetches the latest annual report PDF URL from BSE India."""
        clean_symbol = symbol.replace(".NS", "").upper()
        scrip_code = self.SYMBOL_TO_BSE.get(clean_symbol)
        
        if not scrip_code:
            return None

        # Try a range of years as companies file at different times
        current_year = int(time.strftime("%Y"))
        years_to_try = [f"{current_year-1}-{current_year}", f"{current_year-2}-{current_year-1}"]
        
        for year_str in years_to_try:
            api_url = f"https://api.bseindia.com/BseIndiaAPI/api/AnnualReport/w"
            params = {"scripCode": scrip_code, "year": year_str}
            
            print(f"Searching BSE for {clean_symbol} report ({year_str})...")
            try:
                response = self.session.get(api_url, params=params, headers=self.headers, timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    if isinstance(data, list) and len(data) > 0:
                        # Find the first item with a valid file/attachment name
                        for item in data:
                            filename = item.get('FileName') or item.get('ATTACHMENTNAME')
                            if filename:
                                url = f"https://www.bseindia.com/xml-data/corpfiling/AttachLive/{filename}"
                                # Quick check if URL is valid
                                head = self.session.head(url, headers=self.headers)
                                if head.status_code != 200:
                                    url = f"https://www.bseindia.com/xml-data/corpfiling/AttachHis/{filename}"
                                
                                print(f"Found BSE report: {url}")
                                return url
            except Exception as e:
                print(f"Error checking BSE year {year_str}: {e}")
                
        return None

if __name__ == "__main__":
    fetcher = BSEFetcher()
    print(f"INFY URL: {fetcher.get_latest_annual_report_url('INFY')}")
