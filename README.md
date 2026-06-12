# Fundamental Analysis Tool

A professional equity research platform that combines quantitative Discounted Cash Flow (DCF) modeling with AI powered qualitative auditing. The tool automatically fetches financial data and parses annual reports to provide a comprehensive valuation and management integrity assessment.

## Core Features

*   Quantitative Checklist: Automatically validates 10 key financial metrics including Gross Profit Margins, Debt to Asset ratios, and Return on Equity.
*   AI Qualitative Audit: Uses Gemini 3.5 Flash to parse annual reports (10-K for US, Annual Reports for India) to identify hidden risks and moats.
*   Dynamic DCF Engine: Calculates intrinsic value with parameters that are automatically adjusted based on AI audit findings.
*   Multi Market Support: Full support for US stocks (via SEC) and Indian stocks (via NSE and BSE).
*   Currency Awareness: Automatically detects and displays values in USD or INR based on the ticker symbol.

## Architecture

The project is built with a decoupled architecture:

*   Frontend: React (Vite) with Tailwind CSS for a terminal inspired high data density UI.
*   Backend: FastAPI (Python) for financial logic and AI orchestration.
*   Data Fetchers:
    *   yfinance: For historical free cash flow and shares outstanding data.
    *   edgartools: For direct access to SEC filings.
    *   NSE/BSE Fetchers: Custom scrapers for Indian annual reports.
    *   PyMuPDF: For extracting text from PDF reports.
*   AI Layer: Google Gemini 2.0/3.5 for expert level sentiment analysis and management auditing.

## Setup Instructions

### Prerequisites
*   Python 3.10 or higher
*   Node.js 18 or higher
*   Google AI Studio API Key

### Backend Setup
1. Create and activate a virtual environment:
   python -m venv venv
   source venv/bin/activate
2. Install dependencies:
   pip install -r requirements.txt
3. Create a .env file in the root directory:
   GOOGLE_API_KEY=your_api_key_here
4. Start the backend:
   fastapi dev api.py --port 8000

### Frontend Setup
1. Navigate to the frontend folder:
   cd frontend
2. Install dependencies:
   npm install
3. Start the development server:
   npm run dev -- --port 3001

## Usage

1. Open http://localhost:3001 in your browser.
2. Enter a ticker symbol:
   *   For US stocks: Use symbols like AAPL, MSFT, or TSLA.
   *   For Indian stocks: Use the .NS (NSE) or .BO (BSE) suffix, such as INFY.NS or RELIANCE.NS.
3. For Indian stocks requiring qualitative analysis, place the annual report PDF in the reports/ folder named as {TICKER}_annual_report.pdf to bypass bot protection.

## Disclaimer

This tool is for educational and research purposes only. Valuation results are based on AI interpretations and historical data, which may be non deterministic. This is not financial advice.
