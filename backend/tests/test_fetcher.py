from unittest.mock import MagicMock, patch

import pytest

from errors import DataProviderRateLimitError, ExternalServiceError
from src.data.fetcher import FinancialDataFetcher, clear_fundamentals_cache


@pytest.fixture(autouse=True)
def reset_fundamentals_cache():
    clear_fundamentals_cache()
    yield
    clear_fundamentals_cache()


def _response(payload):
    response = MagicMock()
    response.json.return_value = payload
    return response


@patch("src.data.fetcher._wait_for_request_slot")
@patch("src.data.fetcher.requests.get")
def test_fetcher_normalizes_and_caches_fundamentals(mock_get, _mock_wait):
    mock_get.side_effect = [
        _response(
            {
                "annualReports": [
                    {
                        "fiscalDateEnding": "2025-03-31",
                        "operatingCashflow": "1000",
                        "capitalExpenditures": "200",
                    }
                ]
            }
        ),
        _response(
            {
                "annualReports": [
                    {
                        "totalAssets": "2000",
                        "shortLongTermDebtTotal": "300",
                        "cashAndShortTermInvestments": "100",
                    }
                ]
            }
        ),
        _response(
            {
                "annualReports": [
                    {
                        "grossProfit": "400",
                        "totalRevenue": "1000",
                        "netIncome": "150",
                    }
                ]
            }
        ),
        _response(
            {
                "Symbol": "RELIANCE.BSE",
                "SharesOutstanding": "10",
                "ReturnOnEquityTTM": "0.25",
            }
        ),
    ]

    fetcher = FinancialDataFetcher("RELIANCE.NS", api_key="test-key")

    assert fetcher.get_free_cash_flow() == {"2025-03-31": 800.0}
    assert fetcher.get_shares_outstanding() == 10
    assert fetcher.get_net_debt() == 200.0
    assert fetcher.get_checklist_metrics()["gross_profit"] == 400.0
    assert mock_get.call_count == 4
    assert all(
        call.kwargs["params"]["symbol"] == "RELIANCE.BSE"
        for call in mock_get.call_args_list
    )

    second_fetcher = FinancialDataFetcher("RELIANCE.NS", api_key="test-key")
    assert second_fetcher.get_shares_outstanding() == 10
    assert mock_get.call_count == 4


@patch("src.data.fetcher._wait_for_request_slot")
@patch("src.data.fetcher.requests.get")
def test_fetcher_surfaces_provider_quota(mock_get, _mock_wait):
    mock_get.return_value = _response(
        {"Note": "Thank you for using Alpha Vantage! Our standard API call frequency is limited."}
    )
    fetcher = FinancialDataFetcher("AAPL", api_key="test-key")

    with pytest.raises(DataProviderRateLimitError, match="quota exceeded"):
        fetcher.get_free_cash_flow()


def test_fetcher_requires_api_key():
    fetcher = FinancialDataFetcher("AAPL", api_key=None)

    with pytest.raises(ExternalServiceError, match="ALPHA_VANTAGE_API_KEY"):
        fetcher.get_free_cash_flow()


@patch("src.data.fetcher._wait_for_request_slot")
@patch("src.data.fetcher.requests.get")
def test_http_failure_does_not_expose_api_key(mock_get, _mock_wait):
    response = MagicMock()
    response.ok = False
    response.url = "https://www.alphavantage.co/query?apikey=top-secret"
    mock_get.return_value = response
    fetcher = FinancialDataFetcher("AAPL", api_key="top-secret")

    with pytest.raises(ExternalServiceError) as captured:
        fetcher.get_free_cash_flow()

    assert "top-secret" not in str(captured.value)
    assert captured.value.__cause__ is None
