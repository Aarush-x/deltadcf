import json
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from api import FULL_CHECKLIST_TEXT, _analysis_cache, _local_report, app
from errors import AIProviderError, DataProviderRateLimitError, ExternalServiceError
from src.data.fetcher import FinancialDataFetcher, FundamentalsBundle
from src.data.report_processor import AIResearcher, ReportProcessor


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
    fetcher.get_ai_financial_context.return_value = {"annual_periods": []}

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
    fetcher.get_ai_financial_context.return_value = {"annual_periods": []}

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


def test_financial_context_contains_exact_metrics_and_trends():
    bundle = FundamentalsBundle(
        cash_flow={
            "annualReports": [
                {
                    "fiscalDateEnding": "2025-09-27",
                    "operatingCashflow": 120.0,
                    "capitalExpenditures": 20.0,
                },
                {
                    "fiscalDateEnding": "2024-09-28",
                    "operatingCashflow": 100.0,
                    "capitalExpenditures": 20.0,
                },
            ]
        },
        balance_sheet={
            "annualReports": [
                {
                    "fiscalDateEnding": "2025-09-27",
                    "totalAssets": 1000.0,
                    "shortLongTermDebtTotal": 200.0,
                    "stockholdersEquity": 400.0,
                    "inventory": 60.0,
                    "currentNetReceivables": 90.0,
                },
                {
                    "fiscalDateEnding": "2024-09-28",
                    "totalAssets": 900.0,
                    "shortLongTermDebtTotal": 220.0,
                    "stockholdersEquity": 350.0,
                    "inventory": 50.0,
                    "currentNetReceivables": 100.0,
                },
            ]
        },
        income_statement={
            "annualReports": [
                {
                    "fiscalDateEnding": "2025-09-27",
                    "totalRevenue": 500.0,
                    "grossProfit": 200.0,
                    "netIncome": 100.0,
                    "dilutedEPS": 7.46,
                    "dilutedAverageShares": 13.4,
                },
                {
                    "fiscalDateEnding": "2024-09-28",
                    "totalRevenue": 400.0,
                    "grossProfit": 150.0,
                    "netIncome": 80.0,
                    "dilutedEPS": 6.08,
                    "dilutedAverageShares": 13.8,
                },
            ]
        },
        overview={"SharesOutstanding": 13.0},
    )
    fetcher = FinancialDataFetcher("AAPL", api_key=None)

    with patch.object(fetcher, "_get_bundle", return_value=bundle):
        context = fetcher.get_ai_financial_context()

    latest = context["annual_periods"][0]
    assert latest["diluted_eps"] == 7.46
    assert latest["free_cash_flow"] == 100.0
    assert latest["return_on_equity"] == pytest.approx(100 / 375)
    assert latest["year_over_year_change"]["inventory"] == pytest.approx(0.20)
    assert latest["year_over_year_change"]["receivables"] == pytest.approx(-0.10)
    assert latest["year_over_year_change"]["diluted_average_shares"] < 0


@patch("src.data.report_processor.Company")
def test_sec_context_includes_targeted_sections_and_subsidiaries(mock_company):
    tenk = {
        "Item 1": "Two reportable business segments.",
        "Item 7": "Management discusses operating performance.",
        "Item 11": "Executive compensation is incorporated by reference.",
        "Item 13": "Related party disclosures.",
    }
    exhibit = MagicMock(document_type="EX-21.1")
    exhibit.text.return_value = "Apple Asia Limited — Hong Kong"
    filing = mock_company.return_value.get_filings.return_value.latest.return_value
    filing.obj.return_value = tenk
    filing.exhibits = [exhibit]
    processor = ReportProcessor(
        "AAPL", sec_identity="DeltaDCF owner@example.com"
    )

    context = processor.get_sec_mda()

    assert "[BUSINESS DESCRIPTION]" in context
    assert "[MANAGEMENT DISCUSSION AND ANALYSIS]" in context
    assert "[SUBSIDIARIES - EXHIBIT 21]" in context
    assert "Apple Asia Limited" in context


def test_ai_prompt_prioritizes_structured_financial_facts():
    response_payload = {
        "core_business_audit": [],
        "management_integrity": [],
        "valuation_impact": {},
    }
    ai = AIResearcher()
    ai.client = MagicMock()
    ai.client.models.generate_content.return_value.text = json.dumps(response_payload)
    financial_context = {
        "source": "SEC EDGAR Company Facts",
        "annual_periods": [{"fiscal_date": "2025-09-27", "diluted_eps": 7.46}],
    }

    ai.analyze_checklist(
        "[SUBSIDIARIES - EXHIBIT 21]\nApple Asia Limited",
        FULL_CHECKLIST_TEXT,
        financial_context=financial_context,
    )

    prompt_text = ai.client.models.generate_content.call_args.kwargs["contents"]
    assert '"diluted_eps":7.46' in prompt_text
    assert "Never say" in prompt_text
    assert "SUBSIDIARIES - EXHIBIT 21" in prompt_text
