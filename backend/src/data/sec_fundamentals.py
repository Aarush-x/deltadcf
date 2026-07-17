from __future__ import annotations

import logging
from datetime import date
from typing import Any, Iterable

import requests

from errors import ExternalServiceError
from src.utils.cache import TTLCache


logger = logging.getLogger(__name__)

SEC_TICKERS_URL = "https://www.sec.gov/files/company_tickers.json"
SEC_COMPANY_FACTS_URL = "https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json"
SEC_CACHE_TTL_SECONDS = 24 * 60 * 60
ANNUAL_FORMS = {"10-K", "10-K/A", "20-F", "20-F/A", "40-F", "40-F/A"}

_ticker_map_cache: TTLCache[str, dict[str, str]] = TTLCache(
    ttl_seconds=SEC_CACHE_TTL_SECONDS,
    max_entries=1,
)


def clear_sec_cache() -> None:
    _ticker_map_cache.clear()


def normalize_sec_ticker(ticker_symbol: str) -> str:
    """Normalize US class-share symbols to the SEC ticker convention."""
    return ticker_symbol.strip().upper().replace(".", "-")


def _number(value: Any) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _annual_duration(record: dict[str, Any]) -> bool:
    try:
        days = (date.fromisoformat(record["end"]) - date.fromisoformat(record["start"])).days
    except (KeyError, TypeError, ValueError):
        return False
    return 250 <= days <= 450


def _unit_records(fact: dict[str, Any], unit: str) -> list[dict[str, Any]]:
    units = fact.get("units") or {}
    records = units.get(unit)
    return records if isinstance(records, list) else []


def _deduplicate_by_period(
    records: Iterable[dict[str, Any]], *, duration: bool
) -> dict[str, float]:
    selected: dict[str, tuple[str, str, float]] = {}
    for record in records:
        if record.get("form") not in ANNUAL_FORMS:
            continue
        if duration and not _annual_duration(record):
            continue
        period_end = record.get("end")
        value = _number(record.get("val"))
        if not period_end or value is None:
            continue
        candidate = (str(record.get("filed") or ""), str(record.get("accn") or ""), value)
        current = selected.get(str(period_end))
        if current is None or candidate[:2] > current[:2]:
            selected[str(period_end)] = candidate
    return {period_end: candidate[2] for period_end, candidate in selected.items()}


def _concept_series(
    facts: dict[str, Any],
    aliases: Iterable[str],
    *,
    unit: str = "USD",
    duration: bool,
) -> dict[str, float]:
    combined: dict[str, float] = {}
    for alias in aliases:
        fact = facts.get(alias)
        if not isinstance(fact, dict):
            continue
        series = _deduplicate_by_period(_unit_records(fact, unit), duration=duration)
        for period_end, value in series.items():
            combined.setdefault(period_end, value)
    return combined


def _value_on_or_before(series: dict[str, float], period_end: str) -> float | None:
    eligible = [date_key for date_key in series if date_key <= period_end]
    return series[max(eligible)] if eligible else None


def _sum_series(*series_items: dict[str, float]) -> dict[str, float]:
    period_ends = set().union(*(series.keys() for series in series_items))
    result: dict[str, float] = {}
    for period_end in period_ends:
        values = [_value_on_or_before(series, period_end) for series in series_items]
        present = [value for value in values if value is not None]
        if present:
            result[period_end] = sum(present)
    return result


def _latest(series: dict[str, float]) -> float | None:
    return series[max(series)] if series else None


class SECFundamentalsFetcher:
    """Load and normalize public SEC XBRL Company Facts without an API key."""

    def __init__(self, ticker_symbol: str, identity: str, timeout: int = 30):
        self.ticker_symbol = normalize_sec_ticker(ticker_symbol)
        self.identity = identity.strip()
        self.timeout = timeout

    def _request_json(self, url: str) -> dict[str, Any]:
        if not self.identity or "@" not in self.identity:
            raise ExternalServiceError("SEC_IDENTITY must include a monitored contact email")
        try:
            response = requests.get(
                url,
                headers={
                    "User-Agent": self.identity,
                    "Accept-Encoding": "gzip, deflate",
                    "Accept": "application/json",
                },
                timeout=self.timeout,
            )
        except requests.RequestException:
            raise ExternalServiceError("SEC EDGAR request failed") from None
        if not response.ok:
            raise ExternalServiceError("SEC EDGAR request failed")
        try:
            payload = response.json()
        except ValueError:
            raise ExternalServiceError("SEC EDGAR returned invalid JSON") from None
        if not isinstance(payload, dict):
            raise ExternalServiceError("SEC EDGAR returned invalid data")
        return payload

    def _ticker_map(self) -> dict[str, str]:
        cached = _ticker_map_cache.get("tickers")
        if cached is not None:
            return cached
        payload = self._request_json(SEC_TICKERS_URL)
        ticker_map = {
            normalize_sec_ticker(str(company.get("ticker") or "")): str(company["cik_str"]).zfill(10)
            for company in payload.values()
            if isinstance(company, dict) and company.get("ticker") and company.get("cik_str") is not None
        }
        if not ticker_map:
            raise ExternalServiceError("SEC EDGAR returned no ticker mappings")
        _ticker_map_cache.set("tickers", ticker_map)
        return ticker_map

    def fetch_normalized(self) -> dict[str, dict[str, Any]]:
        cik = self._ticker_map().get(self.ticker_symbol)
        if not cik:
            raise ExternalServiceError("Ticker was not found in SEC EDGAR")
        payload = self._request_json(SEC_COMPANY_FACTS_URL.format(cik=cik))
        all_facts = payload.get("facts") or {}
        us_gaap = all_facts.get("us-gaap") or {}
        dei = all_facts.get("dei") or {}
        if not isinstance(us_gaap, dict) or not us_gaap:
            raise ExternalServiceError("SEC EDGAR returned no US GAAP facts")

        operating_cash_flow = _concept_series(
            us_gaap,
            (
                "NetCashProvidedByUsedInOperatingActivities",
                "NetCashProvidedByUsedInOperatingActivitiesContinuingOperations",
            ),
            duration=True,
        )
        capital_expenditure = _concept_series(
            us_gaap,
            (
                "PaymentsToAcquirePropertyPlantAndEquipment",
                "PaymentsForAdditionsToPropertyPlantAndEquipment",
                "PropertyPlantAndEquipmentAdditions",
            ),
            duration=True,
        )
        revenue = _concept_series(
            us_gaap,
            (
                "RevenueFromContractWithCustomerExcludingAssessedTax",
                "Revenues",
                "SalesRevenueNet",
            ),
            duration=True,
        )
        gross_profit = _concept_series(us_gaap, ("GrossProfit",), duration=True)
        net_income = _concept_series(
            us_gaap,
            ("NetIncomeLoss", "ProfitLoss"),
            duration=True,
        )

        assets = _concept_series(us_gaap, ("Assets",), duration=False)
        cash = _concept_series(
            us_gaap,
            (
                "CashAndCashEquivalentsAtCarryingValue",
                "CashCashEquivalentsRestrictedCashAndRestrictedCashEquivalents",
            ),
            duration=False,
        )
        short_term_investments = _concept_series(
            us_gaap,
            ("ShortTermInvestments", "MarketableSecuritiesCurrent"),
            duration=False,
        )
        debt_total = _concept_series(
            us_gaap,
            ("LongTermDebtAndFinanceLeaseObligations", "LongTermDebt"),
            duration=False,
        )
        if not debt_total:
            debt_total = _sum_series(
                _concept_series(
                    us_gaap,
                    ("LongTermDebtCurrent", "LongTermDebtAndFinanceLeaseObligationsCurrent"),
                    duration=False,
                ),
                _concept_series(
                    us_gaap,
                    ("LongTermDebtNoncurrent", "LongTermDebtAndFinanceLeaseObligationsNoncurrent"),
                    duration=False,
                ),
                _concept_series(us_gaap, ("ShortTermBorrowings",), duration=False),
            )
        inventory = _concept_series(us_gaap, ("InventoryNet",), duration=False)
        receivables = _concept_series(
            us_gaap,
            ("AccountsReceivableNetCurrent", "AccountsNotesAndLoansReceivableNetCurrent"),
            duration=False,
        )
        equity = _concept_series(
            us_gaap,
            ("StockholdersEquity", "StockholdersEquityIncludingPortionAttributableToNoncontrollingInterest"),
            duration=False,
        )
        shares = _concept_series(dei, ("EntityCommonStockSharesOutstanding",), unit="shares", duration=False)
        if not shares:
            shares = _concept_series(
                us_gaap,
                ("CommonStockSharesOutstanding",),
                unit="shares",
                duration=False,
            )

        cash_flow_reports = []
        for period_end in sorted(set(operating_cash_flow) & set(capital_expenditure), reverse=True):
            cash_flow_reports.append(
                {
                    "fiscalDateEnding": period_end,
                    "operatingCashflow": operating_cash_flow[period_end],
                    "capitalExpenditures": capital_expenditure[period_end],
                }
            )

        balance_reports = []
        balance_periods = set().union(
            assets, cash, short_term_investments, debt_total, inventory, receivables, equity
        )
        for period_end in sorted(balance_periods, reverse=True):
            cash_value = _value_on_or_before(cash, period_end)
            investments_value = _value_on_or_before(short_term_investments, period_end)
            balance_reports.append(
                {
                    "fiscalDateEnding": period_end,
                    "totalAssets": _value_on_or_before(assets, period_end),
                    "shortLongTermDebtTotal": _value_on_or_before(debt_total, period_end),
                    "cashAndShortTermInvestments": (cash_value or 0.0) + (investments_value or 0.0),
                    "inventory": _value_on_or_before(inventory, period_end),
                    "currentNetReceivables": _value_on_or_before(receivables, period_end),
                    "stockholdersEquity": _value_on_or_before(equity, period_end),
                }
            )

        income_reports = []
        income_periods = set().union(revenue, gross_profit, net_income)
        for period_end in sorted(income_periods, reverse=True):
            income_reports.append(
                {
                    "fiscalDateEnding": period_end,
                    "totalRevenue": _value_on_or_before(revenue, period_end),
                    "grossProfit": _value_on_or_before(gross_profit, period_end),
                    "netIncome": _value_on_or_before(net_income, period_end),
                }
            )

        latest_equity = _latest(equity)
        latest_net_income = _latest(net_income)
        return_on_equity = (
            latest_net_income / latest_equity
            if latest_net_income is not None and latest_equity not in (None, 0)
            else None
        )
        normalized = {
            "cash_flow": {"annualReports": cash_flow_reports},
            "balance_sheet": {"annualReports": balance_reports},
            "income_statement": {"annualReports": income_reports},
            "overview": {
                "Symbol": self.ticker_symbol,
                "SharesOutstanding": _latest(shares),
                "ReturnOnEquityTTM": return_on_equity,
            },
        }
        if not cash_flow_reports or not normalized["overview"]["SharesOutstanding"]:
            raise ExternalServiceError("SEC EDGAR facts were insufficient for DCF analysis")
        logger.info("Normalized SEC Company Facts", extra={"ticker": self.ticker_symbol, "cik": cik})
        return normalized
