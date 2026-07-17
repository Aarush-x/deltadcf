# DeltaDCF

DeltaDCF is an equity-research application that combines a quantitative discounted cash flow model with optional AI-assisted annual-report auditing. It uses Alpha Vantage for structured fundamentals, SEC filings for US report analysis, and NSE/BSE report sources for Indian securities.

The DCF formulas and baseline assumptions remain in `backend/src/analysis/dcf.py` and `backend/api.py`. The production configuration in this repository changes deployment, validation, failure handling, and operational safety; it does not redesign the valuation model.

## Architecture

| Component | Directory | Production runtime | Responsibility |
| --- | --- | --- | --- |
| Web UI | `frontend/` | Vercel | Vite + React interface; calls the configured API |
| API | `backend/` | Render Docker web service | FastAPI orchestration, cached Alpha Vantage fundamentals, report processing, AI audit, and DCF response |
| CI | `.github/workflows/ci.yml` | GitHub Actions | Backend tests, frontend build, and Docker build |

The API entry point is `backend/api.py` (`api:app`). `GET /api/analyze/{ticker}` validates the symbol, fetches financial statements through Alpha Vantage, runs the quantitative checklist, obtains report text from SEC/NSE/BSE or an optional local PDF, calls the selected AI provider when report text exists, and applies the resulting offsets to the existing DCF calculation. `GET /health` is a dependency-free liveness endpoint.

External services are failure domains. Alpha Vantage, SEC/edgartools, NSE, BSE, Google Gemini, local Ollama, and third-party PDF responses can be slow, rate-limited, unavailable, or change behavior without notice. Downloaded reports are size-limited, stored in the operating system's temporary directory, and deleted after processing. A local `reports/` directory is optional and is not required on Render.

Successful complete analyses are cached in memory for 15 minutes. The underlying Alpha Vantage fundamentals bundle is cached for 24 hours, so an expired analysis can be recomputed without consuming another four provider calls. Provider calls are paced below two requests per second to avoid burst throttling. Both caches are bounded and process-local; they reset when the free Render instance restarts or sleeps.

## Local setup

### Backend

Python 3.11 or later is recommended.

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-dev.txt
cp .env.example .env
python api.py
```

The backend listens on `http://localhost:8000`. Verify it with:

```bash
curl --fail http://localhost:8000/health
```

Set `ALPHA_VANTAGE_API_KEY` for all financial analyses. For local AI analysis, either set `GOOGLE_API_KEY` and `AI_PROVIDER=gemini`, or run Ollama and use `AI_PROVIDER=ollama`. `AI_PROVIDER=auto` is a development-only convenience: it uses Gemini when a key exists and otherwise attempts local Ollama.

### Frontend

Node.js 22 is recommended.

```bash
cd frontend
npm ci
cp .env.example .env.local
npm run dev
```

The local frontend defaults to `http://localhost:8000` only in Vite development mode. A production build stops with a clear error when `VITE_API_URL` is missing.

## Environment variables

### Backend

| Variable | Production | Purpose |
| --- | --- | --- |
| `APP_ENV` | `production` | Selects production-safe defaults and validation |
| `LOG_LEVEL` | `INFO` | Python logging level |
| `PORT` | Set automatically by Render | Uvicorn listen port; defaults to `8000` locally |
| `GOOGLE_API_KEY` | Required when AI report analysis is expected | Server-side Gemini credential; never expose through Vite |
| `ALPHA_VANTAGE_API_KEY` | Required | Server-side fundamentals credential; free keys currently have a small daily request allowance |
| `AI_PROVIDER` | `gemini` | Production permits the cloud provider only |
| `CORS_ALLOWED_ORIGINS` | Required | Comma-separated exact frontend origins, with no wildcard |
| `OLLAMA_MODEL` | Local only | Optional local Ollama model name |
| `OLLAMA_BASE_URL` | Local only | Optional local Ollama URL |
| `SEC_IDENTITY` | Recommended | Honest edgartools identity, such as `DeltaDCF you@example.com` |
| `REPORTS_DIR` | Optional | Local PDF fallback directory; defaults to `reports` |
| `EXTERNAL_REQUEST_TIMEOUT_SECONDS` | Optional | External HTTP timeout; defaults to `60` |
| `MAX_REPORT_BYTES` | Optional | Maximum downloaded PDF size; defaults to 25 MiB |

In production, `AI_PROVIDER=ollama`, `AI_PROVIDER=auto`, and wildcard CORS are rejected at startup. The health endpoint remains available when `GOOGLE_API_KEY` is unset, but an analysis that requires Gemini returns a safe `503` until the key is configured.

### Frontend

The only Vercel variable is:

```text
VITE_API_URL=https://your-render-service.onrender.com
```

Do not add `GOOGLE_API_KEY`, provider credentials, or any backend secret to a `VITE_*` variable because Vite embeds those values in the browser bundle.

## Docker

Build from the repository root so the Docker context matches CI and Render:

```bash
docker build -f backend/Dockerfile -t deltadcf-backend .
```

Run the production image:

```bash
docker run --rm -p 8000:8000 \
  -e PORT=8000 \
  -e APP_ENV=production \
  -e LOG_LEVEL=INFO \
  -e AI_PROVIDER=gemini \
  -e CORS_ALLOWED_ORIGINS=http://localhost:4173 \
  -e GOOGLE_API_KEY=your_key_here \
  -e ALPHA_VANTAGE_API_KEY=your_key_here \
  -e SEC_IDENTITY="DeltaDCF you@example.com" \
  deltadcf-backend
```

Then check:

```bash
curl --fail http://localhost:8000/health
```

The image uses a slim Python base, caches dependency installation before application code, runs as an unprivileged user, honors `${PORT:-8000}`, and includes an internal health check. Secrets are runtime environment variables and are not copied into the image.

## Render deployment

The root `render.yaml` defines a Docker web service with the root Docker context, `backend/Dockerfile`, `/health`, and automatic deployment after GitHub checks pass.

1. Push this branch and open a pull request instead of merging directly to `main`.
2. In Render, choose **New > Blueprint** and connect the GitHub repository.
3. Select the repository and allow Render to read the root `render.yaml`.
4. Supply the prompted variables:
   - `GOOGLE_API_KEY`: a valid server-side Gemini key.
   - `ALPHA_VANTAGE_API_KEY`: a free Alpha Vantage API key used for financial statements.
   - `CORS_ALLOWED_ORIGINS`: the exact Vercel production origin, for example `https://deltadcf.vercel.app`. Add preview origins as comma-separated values only when they are intentionally trusted.
   - `SEC_IDENTITY`: the application name and a monitored contact email.
5. Create the Blueprint and wait for the Docker build and `/health` check to pass.
6. Copy the final `https://<service>.onrender.com` URL into Vercel as `VITE_API_URL`.

Render injects `PORT`; do not hardcode it. The service has no persistent disk requirement. Local report files are optional, and exchange downloads are temporary.

## Vercel deployment

Create a Vercel project from the same GitHub repository with these settings:

- **Root Directory:** `frontend`
- **Framework Preset:** Vite
- **Build Command:** `npm run build`
- **Output Directory:** `dist`
- **Environment Variable:** `VITE_API_URL=https://your-render-service.onrender.com`

No `vercel.json` is needed because this UI has no client-side route paths that require SPA rewrites. Git integration creates previews for non-production branches; validate a preview before promoting or merging it. The Vercel environment must contain no backend secrets.

After Vercel assigns the production domain, update `CORS_ALLOWED_ORIGINS` in Render and redeploy the backend. Include only origins that should be able to call the API from browsers.

## Testing and CI

Run the same checks locally:

```bash
cd backend
python -m pytest

cd ../frontend
npm ci
VITE_API_URL=https://example.invalid npm run build

cd ..
docker build -f backend/Dockerfile -t deltadcf-backend .
```

CI mocks external services and never calls paid APIs. Backend coverage includes health, invalid ticker validation, missing report directories, provider failures, safe error bodies, mocked successful response shape, parser behavior, and DCF regression behavior.

To confirm the production build guard works:

```bash
cd frontend
env -u VITE_API_URL npm run build
```

That command is expected to fail with `VITE_API_URL is required for production builds`.

## Troubleshooting

- **Browser reports a provider failure:** Check Render logs for the server-side exception category. Confirm Alpha Vantage and Gemini key status. User responses intentionally omit raw provider messages.
- **Browser reports the daily financial-data allowance was reached:** Wait for the Alpha Vantage free allowance to reset. Cached tickers continue working while the Render process remains alive.
- **CORS error:** Set `CORS_ALLOWED_ORIGINS` to the exact Vercel origin, including `https://` and excluding a trailing slash, then redeploy Render.
- **Frontend build fails immediately:** Set `VITE_API_URL` for the Vercel environment or the local production-build command.
- **Render health check fails:** Confirm the container is using Render's injected `PORT` and that the Docker command has not been overridden.
- **Indian report audit is empty:** NSE/BSE endpoints may be blocking automation or may not expose a report. For local development, place a trusted PDF in `backend/reports/` with a ticker prefix such as `INFY_annual_report.pdf`.
- **SEC access fails:** Set an honest `SEC_IDENTITY` and check SEC availability and rate limits.

## Known limitations

- Analysis is synchronous. FastAPI runs it in a worker thread so it does not block the event loop. The bounded caches are per-process and non-durable; there is no queue or shared cache across service instances.
- Total analysis latency depends on several third-party providers and can exceed a frontend request timeout during outages or cold starts.
- Render's filesystem is treated as ephemeral; user-managed report persistence is intentionally not part of this deployment.
- NSE/BSE scraping and report URL formats can change without notice.
- Alpha Vantage's documented global examples use BSE symbols. For prototype compatibility, `.NS` and `.BO` inputs are translated to `.BSE` for structured fundamentals; availability varies by company.
- AI output is probabilistic. If no report text can be obtained, the DCF still runs with zero qualitative offsets, matching the existing fallback behavior.
- The fixed DCF assumptions are product choices, not individualized forecasts.

## Rollback

For application changes, redeploy the last known-good Git commit in Render and use Vercel's deployment history to promote the previous frontend deployment. If configuration caused the incident, restore the previous Render environment values and Vercel `VITE_API_URL`, then redeploy both services. Never roll back by reintroducing a leaked credential; rotate it first.

## Financial disclaimer

DeltaDCF is for educational and research purposes only. Its market data may be delayed or inaccurate, and its valuations and AI interpretations may be incomplete, non-deterministic, or wrong. Nothing produced by this software is financial, investment, tax, or legal advice. Verify all source data and consult a qualified professional before making financial decisions.
