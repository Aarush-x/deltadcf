# DeltaDCF - Fundamental Analysis Tool

DeltaDCF is an equity research platform that combines quantitative Discounted Cash Flow (DCF) modeling with AI-powered qualitative auditing. The tool automatically fetches financial data, parses annual reports, and performs valuation audits with parameter adjustments based on business risks.

## Core Features

*   **Quantitative Checklist**: Automatically validates key financial metrics including Gross Profit Margins, Debt to Asset ratios, and Return on Equity (ROE).
*   **Dual-Provider AI Brain**: Performs qualitative audits on Management Discussion and Analysis (MD&A) sections using either a local Ollama model (Gemma 12B) or Google Gemini (Gemini 2.0 Flash) in the cloud.
*   **Dynamic DCF Engine**: Calculates intrinsic value with parameters (growth rates and discount rates) that are adjusted dynamically based on AI audit findings.
*   **Multi-Market Support**: Support for US stocks (via SEC filings) and Indian stocks (via NSE and BSE filings).
*   **Robust Math Engine**: Mathematical validations to prevent division by zero, handle debt-free companies gracefully, and handle shares outstanding errors.

## Architecture

The project has a decoupled architecture:

*   **Frontend**: React (Vite) with Tailwind CSS for a terminal-inspired high data density UI dashboard.
*   **Backend**: FastAPI (Python) for financial logic, DCF calculations, and AI orchestration.
*   **Data Fetchers**:
    *   yfinance: For historical free cash flow, outstanding shares, and balance sheet metrics.
    *   edgartools: For direct access to SEC 10-K filings.
    *   NSE/BSE Fetchers: Custom scrapers for Indian annual reports.
    *   PyMuPDF: For extracting text from PDF reports.

## Setup Instructions

### Prerequisites
*   Python 3.10 or higher
*   Node.js 18 or higher
*   Ollama (optional, for local model execution)
*   Google AI Studio API Key (optional, for cloud model execution)

### 1. Environment Configuration
Create a `.env` file in the root directory of the project with the following keys:
```text
GOOGLE_API_KEY="your_optional_gemini_api_key"
OLLAMA_MODEL="gemma-4-12b-it-qat-q4_0"
OLLAMA_BASE_URL="http://localhost:11434"
CORS_ALLOWED_ORIGINS="http://localhost:5173,http://localhost:3000,http://localhost:3001"
```
*Note: If GOOGLE_API_KEY is defined, the system defaults to using Gemini Cloud. If it is empty, the system falls back to using the local Ollama Gemma instance.*

### 2. Local Ollama Model Setup (Optional)
If using the local Gemma model:
1. Download the Gemma 12B Q4 GGUF file.
2. Navigate to your download folder and create a Modelfile:
   ```bash
   echo "FROM ./gemma-4-12b-it-qat-q4_0.gguf" > Modelfile
   ```
3. Register the model in Ollama:
   ```bash
   ollama create gemma-4-12b-it-qat-q4_0 -f Modelfile
   ```
4. Verify registration:
   ```bash
   ollama list
   ```

### 3. Backend Setup
1. Create and activate a virtual environment:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Start the FastAPI development backend server:
   ```bash
   fastapi dev api.py --port 8000
   ```

### 4. Docker Backend Setup (Alternative)
If you prefer running the backend in a containerized environment (for deployment testing):
1. Build the Docker image:
   ```bash
   docker build -t deltadcf-backend .
   ```
2. Run the container:
   ```bash
   docker run -p 8000:8000 --env-file .env deltadcf-backend
   ```

### 5. Frontend Setup
1. Navigate to the frontend directory:
   ```bash
   cd frontend
   ```
2. Install dependencies:
   ```bash
   npm install
   ```
3. Start the Vite React development server:
   ```bash
   npm run dev -- --port 3001
   ```

## Usage

1. Open http://localhost:3001 in your web browser.
2. Enter a stock ticker:
   *   For US stocks: Enter standard symbols like AAPL, MSFT, or TSLA.
   *   For Indian stocks: Append the exchange suffix, such as INFY.NS or RELIANCE.NS.
3. For Indian stocks requiring qualitative analysis, place the annual report PDF in the `reports/` folder named as `{TICKER}_annual_report.pdf` (e.g. `INFY_annual_report.pdf`) to bypass scraper blocking checks.

## Disclaimer

This tool is for educational and research purposes only. Valuation results are based on historical data and AI interpretations, which may be non-deterministic. This is not financial advice.
