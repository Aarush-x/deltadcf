import pytest
from unittest.mock import MagicMock, patch
from src.data.fetcher import FinancialDataFetcher
from errors import ExternalServiceError

@patch('yfinance.Ticker')
def test_fetcher_get_free_cash_flow(mock_ticker):
    # Setup mock ticker response
    mock_cf = MagicMock()
    mock_cf.empty = False
    mock_cf.index = ['Free Cash Flow']
    mock_cf.loc = {'Free Cash Flow': MagicMock()}
    mock_cf.loc['Free Cash Flow'].head.return_value.to_dict.return_value = {'2024-12-31': 1000.0}
    
    mock_ticker_instance = mock_ticker.return_value
    mock_ticker_instance.cashflow = mock_cf
    
    fetcher = FinancialDataFetcher("AAPL")
    fcf = fetcher.get_free_cash_flow()
    
    assert fcf == {'2024-12-31': 1000.0}

@patch('yfinance.Ticker')
def test_fetcher_get_shares_outstanding(mock_ticker):
    mock_ticker_instance = mock_ticker.return_value
    mock_ticker_instance.info = {'sharesOutstanding': 1000000}
    
    fetcher = FinancialDataFetcher("AAPL")
    shares = fetcher.get_shares_outstanding()
    
    assert shares == 1000000


@patch('yfinance.Ticker')
def test_fetcher_provider_exception_is_not_treated_as_missing_data(mock_ticker):
    mock_ticker.return_value.info.get.side_effect = RuntimeError("upstream unavailable")

    fetcher = FinancialDataFetcher("AAPL")

    with pytest.raises(ExternalServiceError, match="Shares provider failed"):
        fetcher.get_shares_outstanding()
