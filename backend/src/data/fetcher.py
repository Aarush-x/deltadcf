from __future__ import annotations

import logging
import threading
import time
from dataclasses import dataclass
from typing import Any

import requests

from errors import DataProviderRateLimitError, ExternalServiceError
from src.data.sec_fundamentals import SECFundamentalsFetcher, clear_sec_cache
from src.utils.cache import TTLCache


logger = logging.getLogger(__name__)

ALPHA_VANTAGE_URL = "https://www.alphavantage.co/query"
FUNDAMENTALS_CACHE_TTL_SECONDS = 24 * 60 * 60
FUNDAMENTALS_CACHE_MAX_ENTRIES = 256
MIN_REQUEST_INTERVAL_SECONDS = 0.6
_request_pacing_lock = threading.Lock()
_bundle_fetch_lock = threading.Lock()
_last_request_started_at = 0.0


@dataclass(frozen=True)
class FundamentalsBundle:
    cash_flow: dict[str, Any]
    balance_sheet: dict[str, Any]
    income_statement: dict[str, Any]
    overview: dict[str, Any]


_fundamentals_cache: TTLCache[str, FundamentalsBundle] = TTLCache(
    ttl_seconds=FUNDAMENTALS_CACHE_TTL_SECONDS,
    max_entries=FUNDAMENTALS_CACHE_MAX_ENTRIES,
)


def clear_fundamentals_cache() -> None:
    _fundamentals_cache.clear()
    clear_sec_cache()


def _wait_for_request_slot() -> None:
    """Keep provider calls below the documented demo burst threshold."""
    global _last_request_started_at
    with _request_pacing_lock:
        elapsed = time.monotonic() - _last_request_started_at
        remaining = MIN_REQUEST_INTERVAL_SECONDS - elapsed
        if remaining > 0:
            time.sleep(remaining)
        _last_request_started_at = time.monotonic()


def _number(value: Any) -> float | None:
    if value in (None, "", "None", "-"):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _latest_report(payload: dict[str, Any]) -> dict[str, Any]:
    reports = payload.get("annualReports") or []
    return reports[0] if reports else {}


def _provider_symbol(ticker_symbol: str) -> str:
    """Translate common app symbols to Alpha Vantage's global symbol format."""
    ticker = ticker_symbol.strip().upper()
    if ticker.endswith(".NS"):
        return f"{ticker[:-3]}.BSE"
    if ticker.endswith(".BO"):
        return f"{ticker[:-3]}.BSE"
    if ticker.endswith(".BSE"):
        return ticker
    if "-" in ticker and "." not in ticker:
        return ticker.replace("-", ".")
    return ticker


class FinancialDataFetcher:
    """Fetch normalized DCF fundamentals from SEC EDGAR or Alpha Vantage."""

    def __init__(
        self,
        ticker_symbol: str,
        api_key: str | None,
        timeout: int = 30,
        sec_identity: str = "DeltaDCF support@example.com",
    ):
        self.ticker_symbol = ticker_symbol.strip().upper()
        self.provider_symbol = _provider_symbol(self.ticker_symbol)
        self.api_key = (api_key or "").strip()
        self.timeout = timeout
        self.sec_identity = sec_identity

    @property
    def is_us_ticker(self) -> bool:
        return not self.ticker_symbol.endswith((".NS", ".BO", ".BSE"))

    def _request(self, function: str) -> dict[str, Any]:
        if not self.api_key:
            raise ExternalServiceError("ALPHA_VANTAGE_API_KEY is not configured")
        _wait_for_request_slot()
        try:
            response = requests.get(
                ALPHA_VANTAGE_URL,
                params={
                    "function": function,
                    "symbol": self.provider_symbol,
                    "apikey": self.api_key,
                },
                timeout=self.timeout,
            )
        except requests.RequestException:
            raise ExternalServiceError("Alpha Vantage request failed") from None
        if not response.ok:
            raise ExternalServiceError("Alpha Vantage request failed")
        try:
            payload = response.json()
        except ValueError:
            raise ExternalServiceError("Alpha Vantage returned invalid JSON") from None

        provider_message = str(payload.get("Note") or payload.get("Information") or "")
        quota_message = provider_message.lower()
        if any(
            marker in quota_message
            for marker in ("rate limit", "call frequency", "requests per second", "requests per day")
        ):
            raise DataProviderRateLimitError("Alpha Vantage quota exceeded")
        if provider_message:
            raise ExternalServiceError("Alpha Vantage rejected the request")
        if payload.get("Error Message"):
            raise ExternalServiceError("Alpha Vantage did not recognize the ticker")
        return payload

    def _fetch_alpha_vantage_bundle(self) -> FundamentalsBundle:
        bundle = FundamentalsBundle(
            cash_flow=self._request("CASH_FLOW"),
            balance_sheet=self._request("BALANCE_SHEET"),
            income_statement=self._request("INCOME_STATEMENT"),
            overview=self._request("OVERVIEW"),
        )
        if not any(
            (
                bundle.cash_flow.get("annualReports"),
                bundle.balance_sheet.get("annualReports"),
                bundle.income_statement.get("annualReports"),
                bundle.overview.get("Symbol"),
            )
        ):
            raise ExternalServiceError("Alpha Vantage returned no fundamentals")
        return bundle

    def _fetch_bundle(self) -> FundamentalsBundle:
        if self.is_us_ticker:
            try:
                normalized = SECFundamentalsFetcher(
                    self.ticker_symbol,
                    identity=self.sec_identity,
                    timeout=self.timeout,
                ).fetch_normalized()
                return FundamentalsBundle(**normalized)
            except ExternalServiceError as exc:
                logger.warning(
                    "SEC fundamentals unavailable; falling back to Alpha Vantage",
                    extra={"ticker": self.ticker_symbol, "reason": str(exc)},
                )
        return self._fetch_alpha_vantage_bundle()

    def _get_bundle(self) -> FundamentalsBundle:
        cache_key = f"SEC:{self.ticker_symbol}" if self.is_us_ticker else f"ALPHA:{self.provider_symbol}"
        cached = _fundamentals_cache.get(cache_key)
        if cached is not None:
            logger.info("Fundamentals cache hit", extra={"ticker": self.ticker_symbol})
            return cached

        with _bundle_fetch_lock:
            cached = _fundamentals_cache.get(cache_key)
            if cached is not None:
                logger.info("Fundamentals cache hit", extra={"ticker": self.ticker_symbol})
                return cached
            logger.info("Fundamentals cache miss", extra={"ticker": self.ticker_symbol})
            bundle = self._fetch_bundle()
            _fundamentals_cache.set(cache_key, bundle)
            return bundle

    def get_free_cash_flow(self, years: int = 3) -> dict[str, float] | None:
        reports = self._get_bundle().cash_flow.get("annualReports") or []
        history: dict[str, float] = {}
        for report in reports[:years]:
            operating_cash_flow = _number(report.get("operatingCashflow"))
            capital_expenditure = _number(report.get("capitalExpenditures"))
            fiscal_date = report.get("fiscalDateEnding")
            if operating_cash_flow is None or capital_expenditure is None or not fiscal_date:
                continue
            history[str(fiscal_date)] = operating_cash_flow - abs(capital_expenditure)
        return history or None

    def get_shares_outstanding(self) -> int | None:
        shares = _number(self._get_bundle().overview.get("SharesOutstanding"))
        return int(shares) if shares and shares > 0 else None

    def get_net_debt(self) -> float | None:
        balance_sheet = _latest_report(self._get_bundle().balance_sheet)
        total_debt = _number(balance_sheet.get("shortLongTermDebtTotal"))
        if total_debt is None:
            short_debt = _number(balance_sheet.get("shortTermDebt")) or 0.0
            long_debt = _number(balance_sheet.get("longTermDebt")) or 0.0
            total_debt = short_debt + long_debt
        cash = _number(balance_sheet.get("cashAndShortTermInvestments"))
        if cash is None:
            cash = _number(balance_sheet.get("cashAndCashEquivalentsAtCarryingValue")) or 0.0
        return total_debt - cash

    def get_checklist_metrics(self) -> dict[str, Any]:
        bundle = self._get_bundle()
        income = _latest_report(bundle.income_statement)
        balance = _latest_report(bundle.balance_sheet)
        cash_flow = _latest_report(bundle.cash_flow)
        return {
            "gross_profit": _number(income.get("grossProfit")),
            "revenue": _number(income.get("totalRevenue")),
            "total_debt": _number(balance.get("shortLongTermDebtTotal"))
            or _number(balance.get("longTermDebt"))
            or 0.0,
            "total_assets": _number(balance.get("totalAssets")) or 0.0,
            "operating_cash_flow": _number(cash_flow.get("operatingCashflow")) or 0.0,
            "return_on_equity": _number(bundle.overview.get("ReturnOnEquityTTM")),
            "inventory": _number(balance.get("inventory")),
            "receivables": _number(balance.get("currentNetReceivables")),
            "net_income": _number(income.get("netIncome")),
        }
