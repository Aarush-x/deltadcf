import requests
from typing import Optional, Dict
import time

class BSEFetcher:
    """
    Handles retrieval of annual report URLs from BSE India.
    Dynamically resolves Tickers to BSE Scrip Codes.
    """
    
    def __init__(self):
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
            "Referer": "https://www.bseindia.com/",
            "Accept": "application/json, text/plain, */*"
        }
        self.session = requests.Session()

    def get_scrip_code(self, symbol: str) -> Optional[str]:
        """Searches BSE for the Scrip Code of a given symbol."""
        clean_symbol = symbol.replace(".NS", "").upper()
        search_url = f"https://api.bseindia.com/BseIndiaAPI/api/StockReachGraph/w?scripcode={clean_symbol}&flag=0&fromdate=&todate="
        
        try:
            # We use the StockReach API which often resolves the symbol to scrip code
            response = self.session.get(search_url, headers=self.headers, timeout=10)
            if response.status_code == 200:
                # If we get a response, the URL often contains the numeric scrip code in redirects 
                # or metadata. Alternatively, we use a general search.
                pass
            
            # General Search API for Scrip Code
            search_api = f"https://api.bseindia.com/BseIndiaAPI/api/getScCode/w?text={clean_symbol}"
            response = self.session.get(search_api, headers=self.headers, timeout=10)
            if response.status_code == 200:
                try:
                    data = response.json()
                    if isinstance(data, list) and len(data) > 0:
                        # Look for exact match or first result
                        for item in data:
                            # item['value'] is typically the scrip code
                            if clean_symbol in str(item.get('label', '')).upper():
                                return str(item.get('value'))
                        return str(data[0].get('value'))
                except ValueError:
                    print(f"BSE Scrip Code API returned non-JSON response for {clean_symbol}")
        except Exception as e:
            print(f"Error resolving scrip code for {clean_symbol}: {e}")
            
        return None

    def get_latest_annual_report_url(self, symbol: str) -> Optional[str]:
        """Fetches the latest annual report PDF URL from BSE India."""
        clean_symbol = symbol.replace(".NS", "").upper()
        scrip_code = self.get_scrip_code(clean_symbol)
        
        if not scrip_code:
            print(f"Could not resolve BSE Scrip Code for {clean_symbol}")
            return None

        current_year = int(time.strftime("%Y"))
        years_to_try = [f"{current_year-1}-{current_year}", f"{current_year-2}-{current_year-1}"]
        
        for year_str in years_to_try:
            api_url = f"https://api.bseindia.com/BseIndiaAPI/api/AnnualReport/w"
            params = {"scripCode": scrip_code, "year": year_str}
            
            print(f"Searching BSE for {clean_symbol} ({scrip_code}) report ({year_str})...")
            try:
                response = self.session.get(api_url, params=params, headers=self.headers, timeout=10)
                if response.status_code == 200:
                    try:
                        data = response.json()
                        if isinstance(data, list) and len(data) > 0:
                            for item in data:
                                filename = item.get('FileName') or item.get('ATTACHMENTNAME')
                                if filename:
                                    url = f"https://www.bseindia.com/xml-data/corpfiling/AttachLive/{filename}"
                                    return url
                    except ValueError:
                        print(f"BSE Annual Report API returned non-JSON response for {clean_symbol}")
            except Exception:
                pass
                
        return None

if __name__ == "__main__":
    fetcher = BSEFetcher()
    code = fetcher.get_scrip_code("INFY")
    print(f"INFY Code: {code}")
