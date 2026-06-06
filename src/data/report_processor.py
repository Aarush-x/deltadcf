import os
import requests
import fitz  # PyMuPDF
from typing import List, Dict, Optional
import re
from edgar import Company, set_identity
import google.generativeai as genai

class ReportProcessor:
    """
    Pass 1 (The Sorter): Downloads and extracts key sections from real reports.
    Supports SEC (US) via edgartools and PDF (Global/Nifty 50) via scraping.
    """
    
    def __init__(self, ticker: str, reports_dir: str = "reports"):
        self.ticker = ticker
        self.reports_dir = reports_dir
        os.makedirs(reports_dir, exist_ok=True)
        # Required by SEC
        set_identity("Gemini Analyst analyst@gemini-cli.ai")
        # Session for robust downloads
        self.session = requests.Session()
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }

    def get_sec_mda(self) -> Optional[str]:
        """Fetches MD&A and Proxy Statement (for governance) from SEC."""
        try:
            print(f"Fetching SEC filings for {self.ticker}...")
            company = Company(self.ticker)
            tenk = company.get_filings(form="10-K").latest().obj()
            mda_text = tenk['Item 7']
            
            # Try to get Governance/Compensation (often in Item 11/13)
            gov_text = ""
            try:
                gov_text = f"\n[GOVERNANCE DATA]\n{tenk['Item 11']}\n{tenk['Item 13']}"
            except:
                pass
                
            return (str(mda_text) + gov_text)[:30000]
        except Exception as e:
            print(f"Error fetching SEC filings: {e}")
            return None

    def download_report(self, url: str) -> str:
        """Downloads a PDF report using robust session management."""
        file_path = os.path.join(self.reports_dir, f"{self.ticker.replace('.NS', '')}_annual_report.pdf")
        if os.path.exists(file_path):
            return file_path
        try:
            parent_url = "/".join(url.split("/")[:-1])
            self.session.get(parent_url, headers=self.headers, timeout=10)
            response = self.session.get(url, stream=True, timeout=30, headers=self.headers)
            response.raise_for_status()
            with open(file_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            return file_path
        except Exception as e:
            print(f"Error downloading report: {e}")
            return ""

    def extract_text_from_pdf(self, pdf_path: str) -> str:
        """Extracts text from PDF (reads first 150 pages to cover MD&A and Governance)."""
        try:
            doc = fitz.open(pdf_path)
            text = ""
            for i in range(min(len(doc), 150)): 
                text += doc[i].get_text() + "\n"
            doc.close()
            return text
        except Exception as e:
            print(f"Error reading PDF: {e}")
            return ""

    def get_key_sections(self, full_text: str) -> Dict[str, str]:
        """Heuristic section extraction for Indian/Global reports."""
        sections = {"mda": ""}
        patterns = [
            r"Management\s+Discussion\s+(?:and|&)\s+Analysis",
            r"Director's\s+Report",
            r"Corporate\s+Governance\s+Report",
            r"Board's\s+Report"
        ]
        
        extracted_content = []
        for pattern in patterns:
            for match in re.finditer(pattern, full_text, re.IGNORECASE | re.MULTILINE):
                start = match.start()
                extracted_content.append(full_text[start:start+15000])
        
        sections["mda"] = "\n---\n".join(extracted_content)[:50000]
        return sections

class AIResearcher:
    """
    Pass 2 & 3: The Researcher and The Adjuster using Gemini 3.5 Flash.
    """
    
    def __init__(self, api_key: Optional[str] = None):
        if api_key:
            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel('gemini-3.5-flash')
        else:
            self.model = None

    def analyze_checklist(self, context_text: str, checklist: str) -> str:
        """
        Expert Analysis with 'Red Flag Filter' and Governance Audit.
        """
        if not self.model:
            return "AI Error: GOOGLE_API_KEY not found."

        prompt = f"""
        You are a Senior Equity Researcher and Governance Expert. 
        Audit the provided text from an Annual Report against this checklist:
        
        {checklist}
        
        CRITICAL INSTRUCTIONS:
        1. NOISE REDUCTION: Discard marketing fluff, award lists, and generic "vision" statements.
        2. RED FLAG FILTER: Actively look for:
           - Related-party transactions (siphoning risk).
           - High CEO pay vs Profit growth.
           - Frequent Auditor or Management changes.
           - Promoter share pledging.
           - Legal friction or regulatory investigations.
        3. JUDGMENT: Be skeptical. If data is missing or opaque, note it as a risk.

        TEXT FOR ANALYSIS:
        {context_text}
        
        OUTPUT FORMAT:
        ### [CORE BUSINESS AUDIT]
        - (Checklist results here)

        ### [MANAGEMENT INTEGRITY REPORT]
        - (Integrity findings here)

        ### [VALUATION IMPACT]
        - Stage 1 Growth: +/- X%
        - Stage 2 Growth: +/- X%
        - Discount Rate: +/- X% (Include a 'Governance Tax' if integrity is poor)
        """
        
        try:
            response = self.model.generate_content(prompt)
            return response.text
        except Exception as e:
            return f"AI Generation Error: {e}"

    def parse_adjustments(self, ai_response: str) -> Dict[str, float]:
        """Extracts numeric offsets from Gemini's response."""
        adjustments = {
            "growth_rate_stage_1_offset": 0.0,
            "growth_rate_stage_2_offset": 0.0,
            "discount_rate_offset": 0.0
        }
        try:
            s1_match = re.search(r"Stage 1.*?([\+\-][0-9.]+)%", ai_response, re.IGNORECASE)
            s2_match = re.search(r"Stage 2.*?([\+\-][0-9.]+)%", ai_response, re.IGNORECASE)
            dr_match = re.search(r"(?:Discount Rate|WACC).*?([\+\-][0-9.]+)%", ai_response, re.IGNORECASE)
            
            if s1_match: adjustments["growth_rate_stage_1_offset"] = float(s1_match.group(1)) / 100
            if s2_match: adjustments["growth_rate_stage_2_offset"] = float(s2_match.group(1)) / 100
            if dr_match: adjustments["discount_rate_offset"] = float(dr_match.group(1)) / 100
        except Exception:
            pass
        return adjustments

if __name__ == "__main__":
    processor = ReportProcessor("AAPL")
