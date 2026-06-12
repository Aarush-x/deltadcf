from src.data.fetcher import FinancialDataFetcher
from src.analysis.dcf import DCFEngine
from src.analysis.research_checklist import ResearchChecklist
from src.data.report_processor import ReportProcessor, AIResearcher
from src.data.nse_fetcher import NSEFetcher
from src.data.bse_fetcher import BSEFetcher
import sys
import os
import json
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

def main():
    if len(sys.argv) < 2:
        print("Usage: python main.py <TICKER>")
        sys.exit(1)

    ticker_symbol = sys.argv[1].upper()
    api_key = os.getenv("GOOGLE_API_KEY")

    print(f"--- ANALYZING {ticker_symbol} ---")
    
    # 1. Fetch Financial Data (Quant-First)
    fetcher = FinancialDataFetcher(ticker_symbol)
    fcf_history = fetcher.get_free_cash_flow()
    shares = fetcher.get_shares_outstanding()
    net_debt = fetcher.get_net_debt()
    
    if not fcf_history or not shares or net_debt is None:
        print("Error: Could not retrieve necessary financial data.")
        sys.exit(1)
        
    latest_date = max(fcf_history.keys())
    initial_fcf = fcf_history[latest_date]
    
    # 2. Run Quantitative Research Checklist
    print("\n[STEP 1] Running Quantitative Checklist...")
    metrics = fetcher.get_checklist_metrics()
    checklist_obj = ResearchChecklist(metrics)
    checklist_obj.run_quantitative_checks()
    
    for check, res in checklist_obj.results.items():
        status = "✅ PASS" if res['passed'] else "❌ FAIL"
        print(f"  {status} | {check}: {res['value']}")

    # 3. AI Layer (Qualitative Analysis)
    print("\n[STEP 2] Running Expert AI Qualitative Analysis (Gemini 3.5 Flash)...")
    processor = ReportProcessor(ticker_symbol)
    ai = AIResearcher(api_key=api_key)

    mda_text = ""
    is_us_stock = not ticker_symbol.endswith(".NS")

    # --- FLEXIBLE LOCAL DETECTION ---
    local_files = [f for f in os.listdir("reports") if f.upper().startswith(ticker_symbol.replace(".NS", "").upper())]
    if local_files:
        pdf_path = os.path.join("reports", local_files[0])
        print(f"  ✅ Local report detected: {pdf_path}")
        raw_text = processor.extract_text_from_pdf(pdf_path)
        sections = processor.get_key_sections(raw_text)
        mda_text = sections.get("mda", "")
    elif is_us_stock:
        mda_text = processor.get_sec_mda()
    else:
        # Try BSE first (dynamic resolution)
        bse = BSEFetcher()
        report_url = bse.get_latest_annual_report_url(ticker_symbol)

        # Fallback to NSE if BSE fails
        if not report_url:
            print("  BSE dynamic search failed. Trying NSE...")
            nse = NSEFetcher()
            report_url = nse.get_latest_annual_report_url(ticker_symbol)

        if report_url:
            pdf_path = processor.download_report(report_url)
            if pdf_path:
                raw_text = processor.extract_text_from_pdf(pdf_path)
                sections = processor.get_key_sections(raw_text)
                mda_text = sections.get("mda", "")
        else:
            print(f"  ❌ Could not find report URL for {ticker_symbol} on BSE or NSE.")
            print(f"  💡 Hint: Place the PDF in 'reports/' and name it '{ticker_symbol.replace('.NS','')}_annual_report.pdf'")


    adjustments = {"growth_rate_stage_1_offset": 0, "growth_rate_stage_2_offset": 0, "discount_rate_offset": 0}
    
    if mda_text:
        # Full Checklist for Gemini
        full_checklist_text = """
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
        
        ai_report = ai.analyze_checklist(mda_text, full_checklist_text)
        print("\n[AI RESEARCHER REPORT]")
        print(json.dumps(ai_report, indent=2))

        valuation_impact = ai_report["valuation_impact"]
        adjustments = {
            "growth_rate_stage_1_offset": valuation_impact["stage_1_growth_offset"],
            "growth_rate_stage_2_offset": valuation_impact["stage_2_growth_offset"],
            "discount_rate_offset": valuation_impact["discount_rate_offset"],
        }
    else:
        print("  Warning: No MD&A text found for qualitative analysis. Using base assumptions.")

    # 4. Multi-Stage DCF Valuation
    base_growth_stage_1 = 0.18
    base_growth_stage_2 = 0.10
    base_discount_rate = 0.09
    
    final_growth_stage_1 = base_growth_stage_1 + adjustments['growth_rate_stage_1_offset']
    final_growth_stage_2 = base_growth_stage_2 + adjustments['growth_rate_stage_2_offset']
    final_discount_rate = base_discount_rate + adjustments['discount_rate_offset']
    
    print(f"\n[STEP 3] Final DCF Parameters (after AI Audit):")
    print(f"  Stage 1 Growth: {final_growth_stage_1:.1%} (Base: {base_growth_stage_1:.1%})")
    print(f"  Stage 2 Growth: {final_growth_stage_2:.1%} (Base: {base_growth_stage_2:.1%})")
    print(f"  Discount Rate:  {final_discount_rate:.1%} (Base: {base_discount_rate:.1%})")

    growth_stages = [(5, final_growth_stage_1), (5, final_growth_stage_2)]
    terminal_rate = 0.03
    
    engine = DCFEngine(
        initial_fcf=initial_fcf,
        growth_stages=growth_stages,
        terminal_rate=terminal_rate,
        discount_rate=final_discount_rate
    )
    
    intrinsic_value = engine.calculate_intrinsic_value()
    price_per_share = engine.calculate_price_per_share(intrinsic_value, net_debt, shares)
    
    print(f"\n--- VALUATION RESULTS ---")
    print(f"Intrinsic Price per Share: {price_per_share:,.2f}")

if __name__ == "__main__":
    main()
