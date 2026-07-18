# DeltaDCF

DeltaDCF is an open-source equity-research prototype for valuing **S&P 500 companies**. It combines a transparent two-stage discounted cash flow (DCF) model with SEC EDGAR fundamentals and an optional AI-assisted review of annual filings.

The application is designed to answer three practical questions:

- What is a reasonable intrinsic value per share under explicit assumptions?
- Which financial-quality signals support or weaken the valuation?
- What do the company's filings reveal about its business and management?

> DeltaDCF currently accepts S&P 500 tickers only. It is a research and educational tool, not investment advice.

## What the analysis includes

Each completed analysis produces:

- Historical free cash flow derived from operating cash flow less capital expenditure.
- A 10-year, two-stage DCF with a Gordon Growth terminal value.
- Enterprise value, equity value after net debt, and intrinsic value per share.
- A quantitative checklist covering margins, leverage, cash generation, and return on equity.
- A 10-stage core-business audit supported by structured SEC facts and filing excerpts.
- Management-integrity alerts and bounded AI adjustments to the baseline assumptions.
- The baseline, AI adjustment, and final value for every DCF parameter.

### DCF methodology

The baseline valuation is intentionally simple and inspectable:

| Input | Baseline |
| --- | ---: |
| Starting free cash flow | Latest annual operating cash flow minus absolute capital expenditure |
| Stage 1 | 5 years at 18% growth |
| Stage 2 | 5 years at 10% growth |
| Terminal growth | 3% |
| Discount rate | 9% |

DeltaDCF discounts ten projected annual cash flows, adds a Gordon Growth terminal value, subtracts net debt, and divides the resulting equity value by diluted shares outstanding.

When AI analysis is enabled, the model may adjust the growth and discount-rate assumptions based on the filing review. Those adjustments are bounded in code and shown separately from the baseline, so the qualitative layer cannot silently replace the valuation logic. Structured SEC financial facts remain authoritative for the numerical audit.

## Use cases

- **Research triage:** turn a ticker into a consistent first-pass valuation and business-quality review.
- **Scenario framing:** see exactly which growth, terminal, and discount-rate assumptions drive intrinsic value.
- **Financial-statement review:** compare revenue, earnings, inventory, receivables, cash flow, leverage, and ROE trends.
- **Annual-report auditing:** extract business, risk, governance, compensation, related-party, and subsidiary context from SEC filings.
- **Learning and prototyping:** study how a full-stack research product connects public filings, deterministic finance logic, caching, and an LLM.

DeltaDCF is not a stock screener, trading system, portfolio optimizer, or substitute for reviewing primary filings.

## How it works

```text
S&P 500 ticker
      |
      v
SEC EDGAR Company Facts ---------> normalized financial statements
      |                                      |
      |                                      v
      |                               quantitative checks
      v
10-K sections + Exhibit 21 ------> AI-assisted filing audit
                                             |
                                             v
                                   bounded DCF adjustments
                                             |
                                             v
historical FCF + shares + net debt ---> intrinsic value/share
```

For US fundamentals, SEC EDGAR is the primary source. Alpha Vantage is an optional fallback when SEC data is unavailable or insufficient. Completed analyses are cached in memory for 15 minutes, fundamentals for 24 hours, and the SEC ticker map for 24 hours. These bounded caches are process-local and reset when the backend restarts or a free hosting instance sleeps.

## Tech stack

| Layer | Technology | Role |
| --- | --- | --- |
| Frontend | React 19, Vite 6, Tailwind CSS, TanStack Query | Ticker search, analysis states, results, and five-minute client freshness window |
| API | Python 3.11, FastAPI, Uvicorn | Validation, orchestration, caching, provider error handling, and response delivery |
| Financial data | SEC EDGAR Company Facts, Alpha Vantage fallback | Statements, shares, debt, cash, and historical free cash flow inputs |
| Filing data | edgartools, SEC 10-K sections, Exhibit 21, PyMuPDF | Annual-report and subsidiary context |
| Valuation | Custom Python DCF engine | Two-stage cash-flow projection, terminal value, and per-share valuation |
| AI | Google Gemini or local Ollama | Structured business and management audit plus bounded assumption offsets |
| Deployment | Vercel, Render, Docker | Static frontend and containerized backend |
| Quality | pytest, GitHub Actions | Backend tests, frontend production build, and Docker build |

## Repository layout

```text
backend/
  api.py                    FastAPI entry point and analysis orchestration
  src/analysis/dcf.py       DCF calculation engine
  src/data/                 SEC and fallback financial-data adapters
  src/report/               Filing retrieval, parsing, and AI audit
  tests/                    Backend unit and API tests
frontend/
  src/                      React application
.github/workflows/ci.yml    Continuous integration
render.yaml                 Render Blueprint
```

## Run locally

### Prerequisites

- Python 3.11 or later
- Node.js 22 or later
- A monitored email address for the SEC identity header
- Optional: a Google Gemini API key or a locally running Ollama model

Clone the repository:

```bash
git clone https://github.com/Aarush-x/deltadcf.git
cd deltadcf
```

### 1. Start the backend

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-dev.txt
cp .env.example .env
```

At minimum, update `backend/.env` with an honest SEC identity:

```dotenv
APP_ENV=development
SEC_IDENTITY=DeltaDCF you@example.com
CORS_ALLOWED_ORIGINS=http://localhost:5173
```

To use Gemini, also set:

```dotenv
AI_PROVIDER=gemini
GOOGLE_API_KEY=your_google_api_key
```

Start the API:

```bash
python api.py
```

Verify it in another terminal:

```bash
curl --fail http://localhost:8000/health
curl --fail http://localhost:8000/api/analyze/AAPL
```

### 2. Start the frontend

```bash
cd frontend
npm ci
cp .env.example .env.local
npm run dev
```

Open `http://localhost:5173`. Vite development defaults to the backend at `http://localhost:8000`; `frontend/.env.local` can override it with:

```dotenv
VITE_API_URL=http://localhost:8000
```

## Connect a local model with Ollama

Local Ollama support keeps filing text and model inference on your machine. It is available only when `APP_ENV=development`; production configuration deliberately rejects local-model providers.

1. Install [Ollama](https://ollama.com/) and pull a model with enough context for filing analysis:

   ```bash
   ollama pull gemma3:12b
   ```

2. Start Ollama if it is not already running:

   ```bash
   ollama serve
   ```

3. Configure `backend/.env`:

   ```dotenv
   APP_ENV=development
   AI_PROVIDER=ollama
   GOOGLE_API_KEY=
   OLLAMA_MODEL=gemma3:12b
   OLLAMA_BASE_URL=http://localhost:11434
   SEC_IDENTITY=DeltaDCF you@example.com
   CORS_ALLOWED_ORIGINS=http://localhost:5173
   ```

4. Confirm Ollama can see the model, then restart the backend:

   ```bash
   curl --fail http://localhost:11434/api/tags
   cd backend
   source .venv/bin/activate
   python api.py
   ```

`AI_PROVIDER=auto` is also available in development: it uses Gemini when `GOOGLE_API_KEY` is set and otherwise attempts Ollama. Explicitly selecting `ollama` is preferable when testing a local-only setup.

Model quality, available context, speed, and memory use vary substantially. A smaller model can run on lighter hardware but may produce weaker or incomplete filing audits. The deterministic DCF calculation still runs independently of the model's prose.

## Configuration reference

### Backend

| Variable | Required | Purpose |
| --- | --- | --- |
| `APP_ENV` | Yes in production | `development` or `production` behavior and validation |
| `SEC_IDENTITY` | Yes for SEC access | Application name and monitored contact email |
| `AI_PROVIDER` | For AI audit | `gemini`, `ollama`, or development-only `auto` |
| `GOOGLE_API_KEY` | For Gemini | Server-side Gemini credential; never expose it through Vite |
| `OLLAMA_MODEL` | For Ollama | Installed local model tag |
| `OLLAMA_BASE_URL` | For Ollama | Defaults to `http://localhost:11434` |
| `ALPHA_VANTAGE_API_KEY` | Optional | Fallback fundamentals credential |
| `CORS_ALLOWED_ORIGINS` | Yes in production | Comma-separated exact frontend origins |
| `PORT` | Hosting-managed | API port; defaults to `8000` locally |
| `EXTERNAL_REQUEST_TIMEOUT_SECONDS` | Optional | External request timeout; defaults to 60 seconds |
| `MAX_REPORT_BYTES` | Optional | Maximum downloaded filing size; defaults to 25 MiB |
| `REPORTS_DIR` | Optional | Local PDF fallback directory |

### Frontend

| Variable | Required | Purpose |
| --- | --- | --- |
| `VITE_API_URL` | Production builds | Public backend origin, such as `https://your-api.onrender.com` |

Never put provider secrets in a `VITE_*` variable: Vite embeds those values in the browser bundle.

## API

### Health check

```http
GET /health
```

### Analyze a company

```http
GET /api/analyze/{ticker}
```

Example:

```bash
curl --fail http://localhost:8000/api/analyze/NVDA
```

Unsupported or non-S&P 500 symbols are rejected before external data is requested. The frontend allows up to 120 seconds for a complete analysis because SEC retrieval and model inference can take time.

## Test and build

Run the same core checks used by CI:

```bash
cd backend
python -m pytest

cd ../frontend
npm ci
VITE_API_URL=https://example.invalid npm run build

cd ..
docker build -f backend/Dockerfile -t deltadcf-backend .
```

CI mocks external services and does not call paid APIs.

## Deploy

The intended hosted architecture is:

- **Frontend:** Vercel project with root directory `frontend`, build command `npm run build`, output directory `dist`, and `VITE_API_URL` set to the backend URL.
- **Backend:** Render Blueprint from the root `render.yaml`, using `backend/Dockerfile` and `/health` for liveness checks.

For production, set `APP_ENV=production`, `AI_PROVIDER=gemini`, `GOOGLE_API_KEY`, `SEC_IDENTITY`, and the exact Vercel origin in `CORS_ALLOWED_ORIGINS`. Render injects `PORT`. Production rejects `AI_PROVIDER=ollama`, `AI_PROVIDER=auto`, and wildcard CORS.

Build the backend container locally with:

```bash
docker build -f backend/Dockerfile -t deltadcf-backend .
```

## Reliability and limitations

- SEC EDGAR, Alpha Vantage, Gemini, and hosting platforms are external dependencies and can be unavailable or rate-limited.
- The 15-minute analysis cache reduces duplicate work, but all caches are non-durable and isolated to one backend process.
- Analysis is synchronous; cold starts, filing retrieval, and local-model inference can increase latency.
- The S&P 500 allowlist is a repository snapshot and must be updated as index membership changes.
- AI output is probabilistic and should be verified against the cited filing and structured financial facts.
- DCF results are highly sensitive to growth, discount-rate, terminal-growth, and capital-structure assumptions.

## Financial disclaimer

DeltaDCF is provided for educational and research purposes only. Market and filing data may be delayed, incomplete, or inaccurate, and valuations or AI interpretations may be wrong. Nothing produced by this software is financial, investment, tax, or legal advice. Verify primary sources and consult a qualified professional before making financial decisions.
