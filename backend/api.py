import logging
import re
from pathlib import Path
from typing import Annotated

from fastapi import FastAPI, HTTPException, Path as FastAPIPath, Response
from fastapi.middleware.cors import CORSMiddleware

from errors import AIProviderError, DataProviderRateLimitError, ExternalServiceError
from settings import settings
from src.analysis.dcf import DCFEngine
from src.analysis.research_checklist import ResearchChecklist
from src.data.fetcher import FinancialDataFetcher
from src.data.report_processor import AIResearcher, ReportProcessor
from src.data.sp500 import SP500_TICKERS
from src.utils.cache import TTLCache


logger = logging.getLogger(__name__)

BASE_GROWTH_STAGE_1 = 0.18
BASE_GROWTH_STAGE_2 = 0.10
BASE_DISCOUNT_RATE = 0.09
TERMINAL_RATE = 0.03
TICKER_PATTERN = re.compile(r"^[A-Z0-9^][A-Z0-9.^=-]{0,19}$")
ANALYSIS_CACHE_TTL_SECONDS = 15 * 60
ANALYSIS_CACHE_MAX_ENTRIES = 128
_analysis_cache: TTLCache[str, dict] = TTLCache(
    ttl_seconds=ANALYSIS_CACHE_TTL_SECONDS,
    max_entries=ANALYSIS_CACHE_MAX_ENTRIES,
)

FULL_CHECKLIST_TEXT = """
1. Gross Profit Margin > 20%: Higher the margin, higher is the evidence of a sustainable moat
2. Revenue Growth: In line with the gross profit growth
3. EPS: Consistent with Net Profits (check for dilution)
4. Debt Level: Company should not be highly leveraged
5. Inventory: Check for growing inventory along with PAT margin (manufacturing)
6. Sales vs Receivables: Revenue should be backed by cash collections, not just receivables
7. Cash flow from operations: Must be positive
8. Return on Equity > 25%
9. Business Diversity: Prefer 1 or 2 simple business lines
10. Subsidiaries: Not too many (check for siphoning risk)
"""

app = FastAPI(
    title="DeltaDCF API",
    version="1.0.0",
    docs_url=None if settings.is_production else "/docs",
    redoc_url=None if settings.is_production else "/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=list(settings.cors_allowed_origins),
    allow_credentials=False,
    allow_methods=["GET"],
    allow_headers=["Accept", "Content-Type"],
)


def format_pct(value: float) -> str:
    return f"{value:.1%}"


def format_adjustment(value: float) -> str:
    pct = value * 100
    return f"{pct:+.1f}%"


def transform_checklist_results(results: dict) -> list:
    return [
        {
            "metric": check,
            "value": result["value"],
            "status": "PASS" if result["passed"] else "FAIL",
        }
        for check, result in results.items()
    ]


def normalize_ticker(value: str) -> str:
    ticker = value.strip().upper()
    if not TICKER_PATTERN.fullmatch(ticker):
        raise HTTPException(
            status_code=422,
            detail="Ticker must contain only letters, numbers, dots, carets, equals signs, or hyphens.",
        )
    canonical_ticker = ticker.replace(".", "-")
    if canonical_ticker not in SP500_TICKERS:
        raise HTTPException(
            status_code=422,
            detail="DeltaDCF currently supports S&P 500 stocks only.",
        )
    return canonical_ticker


def resolve_ticker(query: str) -> str:
    """Validate a ticker without spending a provider request on symbol search."""
    return normalize_ticker(query)


def _local_report(ticker_symbol: str, reports_dir: Path) -> Path | None:
    if not reports_dir.is_dir():
        return None

    prefix = ticker_symbol.upper()
    candidates = sorted(
        path
        for path in reports_dir.iterdir()
        if path.is_file()
        and path.suffix.lower() == ".pdf"
        and path.name.upper().startswith(prefix)
    )
    return candidates[0] if candidates else None


def get_mda_text(ticker_symbol: str, processor: ReportProcessor) -> str:
    local_report = _local_report(ticker_symbol, processor.reports_dir)
    if local_report:
        raw_text = processor.extract_text_from_pdf(local_report)
        return processor.get_key_sections(raw_text).get("mda", "")

    return processor.get_sec_mda() or ""


@app.get("/health", include_in_schema=False)
def health() -> dict[str, str]:
    return {"status": "ok"}


TickerPath = Annotated[
    str,
    FastAPIPath(
        min_length=1,
        max_length=20,
        pattern=r"^[A-Za-z0-9^][A-Za-z0-9.^=-]{0,19}$",
        description="An S&P 500 ticker such as AAPL, NVDA, or BRK-B",
    ),
]


@app.get("/api/analyze/{ticker}")
def analyze(ticker: TickerPath, response: Response):
    """Run the existing DCF pipeline in FastAPI's worker thread pool."""
    try:
        ticker_symbol = resolve_ticker(ticker)
        cached_analysis = _analysis_cache.get(ticker_symbol)
        if cached_analysis is not None:
            response.headers["X-DeltaDCF-Cache"] = "HIT"
            return cached_analysis

        response.headers["X-DeltaDCF-Cache"] = "MISS"
        fetcher = FinancialDataFetcher(
            ticker_symbol,
            api_key=settings.alpha_vantage_api_key,
            timeout=settings.external_request_timeout_seconds,
            sec_identity=settings.sec_identity,
        )
        fcf_history = fetcher.get_free_cash_flow()
        shares = fetcher.get_shares_outstanding()
        net_debt = fetcher.get_net_debt()

        if not fcf_history or not shares:
            raise HTTPException(
                status_code=404,
                detail="Financial data was not found. Verify the ticker and try again.",
            )
        if net_debt is None:
            net_debt = 0.0

        latest_date = max(fcf_history.keys())
        initial_fcf = fcf_history[latest_date]

        checklist = ResearchChecklist(fetcher.get_checklist_metrics())
        checklist.run_quantitative_checks()
        quantitative_checklist = transform_checklist_results(checklist.results)

        processor = ReportProcessor(
            ticker_symbol,
            reports_dir=settings.reports_dir,
            timeout=settings.external_request_timeout_seconds,
            max_report_bytes=settings.max_report_bytes,
            sec_identity=settings.sec_identity,
        )
        ai = AIResearcher(
            api_key=settings.google_api_key,
            model_name=settings.ollama_model,
            base_url=settings.ollama_base_url,
            provider=settings.ai_provider,
            timeout=settings.external_request_timeout_seconds,
        )

        mda_text = get_mda_text(ticker_symbol, processor)
        financial_context = fetcher.get_ai_financial_context()
        ai_report = (
            ai.analyze_checklist(
                mda_text,
                FULL_CHECKLIST_TEXT,
                financial_context=financial_context,
            )
            if mda_text or financial_context.get("annual_periods")
            else AIResearcher.empty_response()
        )

        valuation_impact = ai_report["valuation_impact"]
        stage_1_offset = valuation_impact["stage_1_growth_offset"]
        stage_2_offset = valuation_impact["stage_2_growth_offset"]
        discount_offset = valuation_impact["discount_rate_offset"]

        final_growth_stage_1 = BASE_GROWTH_STAGE_1 + stage_1_offset
        final_growth_stage_2 = BASE_GROWTH_STAGE_2 + stage_2_offset
        final_discount_rate = BASE_DISCOUNT_RATE + discount_offset

        engine = DCFEngine(
            initial_fcf=initial_fcf,
            growth_stages=[(5, final_growth_stage_1), (5, final_growth_stage_2)],
            terminal_rate=TERMINAL_RATE,
            discount_rate=final_discount_rate,
        )
        intrinsic_value = engine.calculate_intrinsic_value()
        price_per_share = engine.calculate_price_per_share(
            intrinsic_value, net_debt, shares
        )

        currency = "USD"
        result = {
            "ticker": ticker_symbol,
            "currency": currency,
            "quantitative_checklist": quantitative_checklist,
            "ai_researcher_report": {
                "core_business_audit": ai_report["core_business_audit"],
                "management_integrity": ai_report["management_integrity"],
            },
            "dcf_parameters": {
                "stage_1_growth": {
                    "base": format_pct(BASE_GROWTH_STAGE_1),
                    "final": format_pct(final_growth_stage_1),
                    "adjustment": format_adjustment(stage_1_offset),
                },
                "stage_2_growth": {
                    "base": format_pct(BASE_GROWTH_STAGE_2),
                    "final": format_pct(final_growth_stage_2),
                    "adjustment": format_adjustment(stage_2_offset),
                },
                "discount_rate": {
                    "base": format_pct(BASE_DISCOUNT_RATE),
                    "final": format_pct(final_discount_rate),
                    "adjustment": format_adjustment(discount_offset),
                },
            },
            "valuation": {"intrinsic_price_per_share": price_per_share},
        }
        _analysis_cache.set(ticker_symbol, result)
        return result
    except HTTPException:
        raise
    except AIProviderError as exc:
        logger.warning("AI provider failed for %s", ticker, exc_info=exc)
        raise HTTPException(
            status_code=503,
            detail="The AI analysis provider is temporarily unavailable. Try again later.",
        ) from exc
    except DataProviderRateLimitError as exc:
        logger.warning("Financial data quota exceeded for %s", ticker, exc_info=exc)
        raise HTTPException(
            status_code=429,
            detail="The daily financial-data allowance has been reached. Try again later.",
            headers={"Retry-After": "3600"},
        ) from exc
    except ExternalServiceError as exc:
        logger.warning("External data provider failed for %s", ticker, exc_info=exc)
        raise HTTPException(
            status_code=503,
            detail="A financial data provider is temporarily unavailable. Try again later.",
        ) from exc
    except ValueError as exc:
        logger.info("Analysis input was rejected for %s", ticker, exc_info=exc)
        raise HTTPException(
            status_code=422,
            detail="The analysis could not be completed for this ticker.",
        ) from exc
    except Exception as exc:
        logger.exception("Unexpected analysis failure for %s", ticker)
        raise HTTPException(
            status_code=500,
            detail="The analysis could not be completed due to an internal error.",
        ) from exc


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("api:app", host="0.0.0.0", port=settings.port)
