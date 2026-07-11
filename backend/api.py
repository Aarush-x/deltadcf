import os
import yfinance as yf

from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from src.data.fetcher import FinancialDataFetcher
from src.analysis.dcf import DCFEngine
from src.analysis.research_checklist import ResearchChecklist
from src.data.report_processor import ReportProcessor, AIResearcher
from src.data.nse_fetcher import NSEFetcher
from src.data.bse_fetcher import BSEFetcher

BASE_GROWTH_STAGE_1 = 0.18
BASE_GROWTH_STAGE_2 = 0.10
BASE_DISCOUNT_RATE = 0.09
TERMINAL_RATE = 0.03

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

app = FastAPI()

cors_origins_str = os.getenv("CORS_ALLOWED_ORIGINS")
if cors_origins_str:
    cors_origins = [orig.strip() for orig in cors_origins_str.split(",") if orig.strip()]
else:
    cors_origins = ["http://localhost:5173", "http://localhost:3000", "http://localhost:3001"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_methods=["GET"],
    allow_headers=["*"],
)


def format_pct(value: float) -> str:
    return f"{value:.1%}"


def format_adjustment(value: float) -> str:
    pct = value * 100
    if pct >= 0:
        return f"+{pct:.1f}%"
    return f"{pct:.1f}%"


def transform_checklist_results(results: dict) -> list:
    return [
        {
            "metric": check,
            "value": res["value"],
            "status": "PASS" if res["passed"] else "FAIL",
        }
        for check, res in results.items()
    ]


def resolve_ticker(query: str) -> str:
    """
    Tries to resolve a query (ticker or company name) to a valid ticker symbol.
    Prefers NSE (.NS) for Indian stocks and major US exchanges for others.
    """
    query = query.strip().upper()
    
    # If it already looks like a ticker, return it
    if "." in query or (len(query) <= 5 and query.isalpha()):
        # Quick check if it exists
        try:
            t = yf.Ticker(query)
            if t.info.get('symbol'):
                return query
        except:
            pass

    try:
        search = yf.Search(query, max_results=8)
        quotes = search.quotes
        if not quotes:
            return query

        # 1. Prefer NSE (.NS)
        for q in quotes:
            symbol = q.get('symbol', '')
            if symbol.endswith('.NS'):
                return symbol
        
        # 2. Prefer BSE (.BO)
        for q in quotes:
            symbol = q.get('symbol', '')
            if symbol.endswith('.BO'):
                return symbol
                
        # 3. Prefer US Major Exchanges
        for q in quotes:
            exch = q.get('exchange', '')
            if exch in ['NMS', 'NYQ', 'ASE']:
                return q.get('symbol', '')
        
        # 4. Return first result if nothing specific matched
        return quotes[0].get('symbol', query)
    except:
        return query


def get_mda_text(ticker_symbol: str, processor: ReportProcessor) -> str:
    is_us_stock = not ticker_symbol.endswith(".NS")

    local_files = [
        f for f in os.listdir("reports")
        if f.upper().startswith(ticker_symbol.replace(".NS", "").upper())
    ]
    if local_files:
        pdf_path = os.path.join("reports", local_files[0])
        raw_text = processor.extract_text_from_pdf(pdf_path)
        sections = processor.get_key_sections(raw_text)
        return sections.get("mda", "")

    if is_us_stock:
        return processor.get_sec_mda() or ""

    bse = BSEFetcher()
    report_url = bse.get_latest_annual_report_url(ticker_symbol)

    if not report_url:
        nse = NSEFetcher()
        report_url = nse.get_latest_annual_report_url(ticker_symbol)

    if not report_url:
        return ""

    pdf_path = processor.download_report(report_url)
    if not pdf_path:
        return ""

    raw_text = processor.extract_text_from_pdf(pdf_path)
    sections = processor.get_key_sections(raw_text)
    return sections.get("mda", "")


@app.get("/api/analyze/{ticker}")
async def analyze(ticker: str):
    # Resolve company name to ticker
    ticker_symbol = resolve_ticker(ticker)

    try:
        api_key = os.getenv("GOOGLE_API_KEY")
        ollama_model = os.getenv("OLLAMA_MODEL", "gemma-4-12b-it-qat-q4_0")
        ollama_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        ai_provider = os.getenv("AI_PROVIDER", "auto")

        fetcher = FinancialDataFetcher(ticker_symbol)
        fcf_history = fetcher.get_free_cash_flow()
        shares = fetcher.get_shares_outstanding()
        net_debt = fetcher.get_net_debt()

        if not fcf_history or not shares:
            raise HTTPException(
                status_code=404,
                detail=f"Could not retrieve financial data for {ticker_symbol}. Verify the ticker is valid.",
            )
        if net_debt is None:
            net_debt = 0.0

        latest_date = max(fcf_history.keys())
        initial_fcf = fcf_history[latest_date]

        metrics = fetcher.get_checklist_metrics()
        checklist_obj = ResearchChecklist(metrics)
        checklist_obj.run_quantitative_checks()
        quantitative_checklist = transform_checklist_results(checklist_obj.results)

        processor = ReportProcessor(ticker_symbol)
        ai = AIResearcher(
            api_key=api_key,
            model_name=ollama_model,
            base_url=ollama_url,
            provider=ai_provider
        )

        mda_text = get_mda_text(ticker_symbol, processor)

        if mda_text:
            ai_report = ai.analyze_checklist(mda_text, FULL_CHECKLIST_TEXT)
        else:
            ai_report = AIResearcher.empty_response()

        valuation_impact = ai_report["valuation_impact"]
        stage_1_offset = valuation_impact["stage_1_growth_offset"]
        stage_2_offset = valuation_impact["stage_2_growth_offset"]
        discount_offset = valuation_impact["discount_rate_offset"]

        final_growth_stage_1 = BASE_GROWTH_STAGE_1 + stage_1_offset
        final_growth_stage_2 = BASE_GROWTH_STAGE_2 + stage_2_offset
        final_discount_rate = BASE_DISCOUNT_RATE + discount_offset

        growth_stages = [(5, final_growth_stage_1), (5, final_growth_stage_2)]

        engine = DCFEngine(
            initial_fcf=initial_fcf,
            growth_stages=growth_stages,
            terminal_rate=TERMINAL_RATE,
            discount_rate=final_discount_rate,
        )

        intrinsic_value = engine.calculate_intrinsic_value()
        price_per_share = engine.calculate_price_per_share(intrinsic_value, net_debt, shares)

        currency = "INR" if ticker_symbol.endswith(".NS") or ticker_symbol.endswith(".BO") else "USD"

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
            "valuation": {
                "intrinsic_price_per_share": price_per_share,
            },
        }

        return result

    except HTTPException:
        raise
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
