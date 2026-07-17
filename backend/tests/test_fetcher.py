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
    response.ok = True
    return response


def _fact(unit, records):
    return {"units": {unit: records}}


def _annual(value, end="2025-09-27", filed="2025-10-31"):
    return {
        "form": "10-K",
        "fy": int(end[:4]),
        "fp": "FY",
        "start": f"{int(end[:4]) - 1}-09-29",
        "end": end,
        "filed": filed,
        "accn": f"annual-{end}",
        "val": value,
    }


def _instant(value, end="2025-09-27", filed="2025-10-31"):
    return {
        "form": "10-K",
        "fy": int(end[:4]),
        "fp": "FY",
        "end": end,
        "filed": filed,
        "accn": f"instant-{end}",
        "val": value,
    }


def _sec_payload():
    prior_original = _annual(90, end="2024-09-28", filed="2024-11-01")
    prior_restated = _annual(100, end="2024-09-28", filed="2025-10-31")
    return {
        "facts": {
            "dei": {
                "EntityCommonStockSharesOutstanding": _fact("shares", [_instant(10)]),
            },
            "us-gaap": {
                "NetCashProvidedByUsedInOperatingActivities": _fact(
                    "USD", [prior_original, prior_restated, _annual(120)]
                ),
                "PaymentsToAcquirePropertyPlantAndEquipment": _fact(
                    "USD", [_annual(20, end="2024-09-28"), _annual(30)]
                ),
                "Assets": _fact("USD", [_instant(1000)]),
                "LongTermDebt": _fact("USD", [_instant(300)]),
                "CashAndCashEquivalentsAtCarryingValue": _fact("USD", [_instant(100)]),
                "ShortTermInvestments": _fact("USD", [_instant(50)]),
                "RevenueFromContractWithCustomerExcludingAssessedTax": _fact("USD", [_annual(500)]),
                "GrossProfit": _fact("USD", [_annual(200)]),
                "NetIncomeLoss": _fact("USD", [_annual(100)]),
                "StockholdersEquity": _fact("USD", [_instant(400)]),
                "InventoryNet": _fact("USD", [_instant(25)]),
                "AccountsReceivableNetCurrent": _fact("USD", [_instant(40)]),
            },
        }
    }


@patch("src.data.sec_fundamentals.requests.get")
def test_us_fetcher_uses_sec_normalizes_restatements_and_caches(mock_get):
    mock_get.side_effect = [
        _response({"0": {"ticker": "AAPL", "cik_str": 320193, "title": "Apple Inc."}}),
        _response(_sec_payload()),
    ]
    fetcher = FinancialDataFetcher(
        "aapl",
        api_key=None,
        sec_identity="DeltaDCF owner@example.com",
    )

    assert fetcher.get_free_cash_flow() == {
        "2025-09-27": 90.0,
        "2024-09-28": 80.0,
    }
    assert fetcher.get_shares_outstanding() == 10
    assert fetcher.get_net_debt() == 150.0
    metrics = fetcher.get_checklist_metrics()
    assert metrics["gross_profit"] == 200.0
    assert metrics["return_on_equity"] == 0.25
    assert mock_get.call_count == 2

    assert fetcher.get_shares_outstanding() == 10
    assert mock_get.call_count == 2


@patch("src.data.sec_fundamentals.requests.get")
def test_sec_normalizes_dot_class_ticker_to_hyphen(mock_get):
    mock_get.side_effect = [
        _response({"0": {"ticker": "BRK-B", "cik_str": 1067983}}),
        _response(_sec_payload()),
    ]

    fetcher = FinancialDataFetcher(
        "brk.b",
        api_key=None,
        sec_identity="DeltaDCF owner@example.com",
    )

    assert fetcher.get_shares_outstanding() == 10
    assert "CIK0001067983.json" in mock_get.call_args_list[1].args[0]


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
    fetcher = FinancialDataFetcher("RELIANCE.NS", api_key="test-key")

    with pytest.raises(DataProviderRateLimitError, match="quota exceeded"):
        fetcher.get_free_cash_flow()


def test_fetcher_requires_api_key():
    fetcher = FinancialDataFetcher("RELIANCE.NS", api_key=None)

    with pytest.raises(ExternalServiceError, match="ALPHA_VANTAGE_API_KEY"):
        fetcher.get_free_cash_flow()


@patch("src.data.fetcher._wait_for_request_slot")
@patch("src.data.fetcher.requests.get")
def test_http_failure_does_not_expose_api_key(mock_get, _mock_wait):
    response = MagicMock()
    response.ok = False
    response.url = "https://www.alphavantage.co/query?apikey=top-secret"
    mock_get.return_value = response
    fetcher = FinancialDataFetcher("RELIANCE.NS", api_key="top-secret")

    with pytest.raises(ExternalServiceError) as captured:
        fetcher.get_free_cash_flow()

    assert "top-secret" not in str(captured.value)
    assert captured.value.__cause__ is None
