import yfinance as yf
import pandas as pd
from typing import Dict, Optional, Any
import json

class FinancialDataFetcher:
    """
    Fetches structured financial data using yfinance.
    Focuses on accuracy and avoids PDF scraping.
    """
    
    def __init__(self, ticker_symbol: str):
        self.ticker_symbol = ticker_symbol
        self.ticker = yf.Ticker(ticker_symbol)
        
    def get_free_cash_flow(self, years: int = 3) -> Optional[Dict[str, float]]:
        """Retrieves the Free Cash Flow for the last N years."""
        try:
            cf = self.ticker.cashflow
            if cf.empty:
                return None
            
            if 'Free Cash Flow' in cf.index:
                fcf = cf.loc['Free Cash Flow']
                fcf.index = fcf.index.astype(str)
                return fcf.head(years).to_dict()
            return None
        except Exception as e:
            print(f"Error fetching FCF for {self.ticker_symbol}: {e}")
            return None

    def get_checklist_metrics(self) -> Dict[str, Any]:
        """Retrieves quantitative metrics for the Research Checklist."""
        info = self.ticker.info
        income_stmt = self.ticker.income_stmt
        balance_sheet = self.ticker.balance_sheet
        cash_flow = self.ticker.cashflow
        
        metrics = {}
        try:
            # Gross Profit Margin
            if not income_stmt.empty:
                latest_income = income_stmt.iloc[:, 0]
                metrics['gross_profit'] = latest_income.get('Gross Profit')
                metrics['revenue'] = latest_income.get('Total Revenue')
                metrics['net_income'] = latest_income.get('Net Income')
                
            # ROE & Assets
            if not balance_sheet.empty:
                latest_bs = balance_sheet.iloc[:, 0]
                metrics['total_assets'] = latest_bs.get('Total Assets')
                metrics['total_debt'] = info.get('totalDebt')
                metrics['return_on_equity'] = info.get('returnOnEquity')
                
            # CFO
            if not cash_flow.empty:
                latest_cf = cash_flow.iloc[:, 0]
                metrics['operating_cash_flow'] = latest_cf.get('Operating Cash Flow')
                
            # Inventory & Receivables (Latest available)
            if not balance_sheet.empty:
                metrics['inventory'] = latest_bs.get('Inventory')
                metrics['receivables'] = latest_bs.get('Net Receivables')
                
        except Exception as e:
            print(f"Error extracting checklist metrics: {e}")
            
        return metrics

    def get_shares_outstanding(self) -> Optional[int]:
        return self.ticker.info.get('sharesOutstanding')

    def get_net_debt(self) -> Optional[float]:
        try:
            info = self.ticker.info
            total_debt = info.get('totalDebt')
            total_cash = info.get('totalCash')
            
            # Default to 0.0 if None (common for debt-free companies)
            debt_val = float(total_debt) if total_debt is not None else 0.0
            cash_val = float(total_cash) if total_cash is not None else 0.0
            
            return debt_val - cash_val
        except Exception as e:
            print(f"Error calculating net debt for {self.ticker_symbol}: {e}")
            return 0.0

if __name__ == "__main__":
    # Quick sanity check
    fetcher = FinancialDataFetcher("AAPL")
    print(f"FCF: {fetcher.get_free_cash_flow()}")
    print(f"Shares: {fetcher.get_shares_outstanding()}")
    print(f"Net Debt: {fetcher.get_net_debt()}")
