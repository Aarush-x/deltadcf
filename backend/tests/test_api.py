from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from api import _analysis_cache, _local_report, app
from errors import AIProviderError, DataProviderRateLimitError, ExternalServiceError


client = TestClient(app)


@pytest.fixture(autouse=True)
def reset_analysis_cache():
    _analysis_cache.clear()
    yield
    _analysis_cache.clear()


def test_health_endpoint():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


@pytest.mark.parametrize(
    "ticker",
    ["BAD%20TICKER", "AAPL%2FSECRET", "TOO-LONG-TICKER-SYMBOL-123"],
)
def test_invalid_ticker_is_rejected(ticker):
    response = client.get(f"/api/analyze/{ticker}")

    assert response.status_code in {404, 422}
    assert "traceback" not in response.text.lower()


def test_missing_reports_directory_is_safe(tmp_path):
    missing_directory = tmp_path / "not-created"

    assert _local_report("AAPL", missing_directory) is None


@patch("api.resolve_ticker", side_effect=ExternalServiceError("provider token=secret"))
def test_external_provider_failure_returns_safe_response(_mock_resolve):
    response = client.get("/api/analyze/AAPL")

    assert response.status_code == 503
    assert response.json() == {
        "detail": "A financial data provider is temporarily unavailable. Try again later."
    }
    assert "secret" not in response.text


@patch("api.FinancialDataFetcher")
@patch("api.resolve_ticker", return_value="AAPL")
def test_provider_quota_returns_retryable_429(_mock_resolve, mock_fetcher_class):
    mock_fetcher_class.return_value.get_free_cash_flow.side_effect = (
        DataProviderRateLimitError("secret quota detail")
    )

    response = client.get("/api/analyze/AAPL")

    assert response.status_code == 429
    assert response.headers["retry-after"] == "3600"
    assert response.json() == {
        "detail": "The daily financial-data allowance has been reached. Try again later."
    }
    assert "secret" not in response.text


@patch("api.resolve_ticker", side_effect=RuntimeError("/private/path api-key-value"))
def test_unexpected_failure_does_not_leak_exception(_mock_resolve):
    response = client.get("/api/analyze/AAPL")

    assert response.status_code == 500
    assert response.json() == {
        "detail": "The analysis could not be completed due to an internal error."
    }
    assert "/private/path" not in response.text
    assert "api-key-value" not in response.text


@patch("api.get_mda_text", return_value="annual report content")
@patch("api.ReportProcessor")
@patch("api.FinancialDataFetcher")
@patch("api.resolve_ticker", return_value="AAPL")
def test_ai_provider_failure_returns_safe_response(
    _mock_resolve,
    mock_fetcher_class,
    _mock_processor_class,
    _mock_get_mda,
):
    fetcher = mock_fetcher_class.return_value
    fetcher.get_free_cash_flow.return_value = {"2024-12-31": 100.0}
    fetcher.get_shares_outstanding.return_value = 10
    fetcher.get_net_debt.return_value = 0.0
    fetcher.get_checklist_metrics.return_value = {}

    with patch(
        "api.AIResearcher.analyze_checklist",
        side_effect=AIProviderError("upstream secret"),
    ):
        response = client.get("/api/analyze/AAPL")

    assert response.status_code == 503
    assert response.json() == {
        "detail": "The AI analysis provider is temporarily unavailable. Try again later."
    }
    assert "upstream secret" not in response.text


@patch("api.get_mda_text", return_value="")
@patch("api.ReportProcessor")
@patch("api.FinancialDataFetcher")
@patch("api.resolve_ticker", return_value="AAPL")
def test_successful_analysis_response_shape(
    _mock_resolve,
    mock_fetcher_class,
    _mock_processor_class,
    _mock_get_mda,
):
    fetcher = mock_fetcher_class.return_value
    fetcher.get_free_cash_flow.return_value = {"2024-12-31": 100.0}
    fetcher.get_shares_outstanding.return_value = 10
    fetcher.get_net_debt.return_value = 0.0
    fetcher.get_checklist_metrics.return_value = {
        "gross_profit": 40.0,
        "revenue": 100.0,
        "total_debt": 10.0,
        "total_assets": 100.0,
        "operating_cash_flow": 20.0,
        "return_on_equity": 0.30,
    }

    response = client.get("/api/analyze/AAPL")

    assert response.status_code == 200
    assert response.headers["x-deltadcf-cache"] == "MISS"
    payload = response.json()
    assert payload["ticker"] == "AAPL"
    assert payload["currency"] == "USD"
    assert isinstance(payload["quantitative_checklist"], list)
    assert set(payload["ai_researcher_report"]) == {
        "core_business_audit",
        "management_integrity",
    }
    assert set(payload["dcf_parameters"]) == {
        "stage_1_growth",
        "stage_2_growth",
        "discount_rate",
    }
    assert isinstance(payload["valuation"]["intrinsic_price_per_share"], float)

    cached_response = client.get("/api/analyze/AAPL")
    assert cached_response.status_code == 200
    assert cached_response.headers["x-deltadcf-cache"] == "HIT"
    assert cached_response.json() == payload
    assert mock_fetcher_class.call_count == 1
