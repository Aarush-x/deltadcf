import yfinance as yf
import json
import sys

def verify_nifty_50(ticker_symbol="RELIANCE.NS"):
    print(f"--- Verifying Nifty 50: {ticker_symbol} ---")
    try:
        ticker = yf.Ticker(ticker_symbol)
        # Fetch cashflow
        cf = ticker.cashflow
        if cf.empty:
            print("Error: Cash flow statement is empty.")
            return None
        
        # Free Cash Flow is usually a row
        if 'Free Cash Flow' in cf.index:
            fcf = cf.loc['Free Cash Flow']
            # Convert index (Timestamps) to strings
            fcf.index = fcf.index.astype(str)
            # Get last 3 years
            fcf_last_3 = fcf.head(3).to_dict()
            print(f"Successfully retrieved FCF for {ticker_symbol}")
            return fcf_last_3
        else:
            print("Error: 'Free Cash Flow' row not found in cash flow statement.")
            return None
    except Exception as e:
        print(f"Exception during Nifty 50 verification: {e}")
        return None

def verify_sp500_yf(ticker_symbol="AAPL"):
    print(f"--- Verifying S&P 500 (yfinance): {ticker_symbol} ---")
    try:
        ticker = yf.Ticker(ticker_symbol)
        cf = ticker.cashflow
        if cf.empty:
            print("Error: Cash flow statement is empty.")
            return None
        
        if 'Free Cash Flow' in cf.index:
            fcf = cf.loc['Free Cash Flow']
            # Convert index (Timestamps) to strings
            fcf.index = fcf.index.astype(str)
            fcf_last_3 = fcf.head(3).to_dict()
            print(f"Successfully retrieved FCF for {ticker_symbol}")
            return fcf_last_3
        else:
            print("Error: 'Free Cash Flow' row not found.")
            return None
    except Exception as e:
        print(f"Exception during S&P 500 (yfinance) verification: {e}")
        return None

if __name__ == "__main__":
    results = {}
    
    nifty_fcf = verify_nifty_50()
    sp500_fcf = verify_sp500_yf()
    
    results['nifty_50'] = nifty_fcf
    results['sp500'] = sp500_fcf
    
    print("\n--- FINAL JSON OUTPUT ---")
    print(json.dumps(results, indent=2, default=str))
