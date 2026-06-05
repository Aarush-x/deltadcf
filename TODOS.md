# Project TODOS

## High Priority
- [ ] **Implement Fallback Data Source**
  - **What:** Add a secondary API (e.g., Alpha Vantage or Financial Modeling Prep) for when `yfinance` returns empty or incomplete cash flow data.
  - **Why:** `yfinance` is a scraper-based library and can occasionally miss specific financial rows. A secondary source ensures the "Quant-First" accuracy mandate.
  - **Context:** See engineering review findings from 2026-06-05.
  - **Depends on:** Core data ingestion layer.

- [ ] **Multi-Pass Evaluation Suite**
  - **What:** Create a benchmark dataset of "Golden Reports" (e.g., AAPL 10-K, RELIANCE Annual Report) with human-verified growth drivers and risks.
  - **Why:** Validates that the AI multi-pass extraction (Pass 1: Extract, Pass 2: Cluster, Pass 3: Suggest) is accurate and not hallucinating growth rates.
  - **Context:** Critical for preventing "Insight-First" hallucinations in the final FA report.

## Low Priority
- [ ] Add support for historical DCF backtesting.
- [ ] Integrate analyst consensus comparison (optional/deferred).
