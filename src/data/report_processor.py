import os
import requests
from PyPDF2 import PdfReader
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
        """Fetches the real Item 7 (MD&A) from the latest 10-K for US stocks."""
        try:
            print(f"Fetching latest 10-K for {self.ticker} from SEC EDGAR...")
            company = Company(self.ticker)
            filing = company.get_filings(form="10-K").latest()
            if filing:
                tenk = filing.obj()
                mda_text = tenk['Item 7']
                return str(mda_text)[:20000] # Increased limit for Gemini
            return None
        except Exception as e:
            print(f"Error fetching SEC filing for {self.ticker}: {e}")
            return None

    def download_report(self, url: str) -> str:
        """Downloads a PDF report using robust session management."""
        file_path = os.path.join(self.reports_dir, f"{self.ticker.replace('.NS', '')}_annual_report.pdf")
        
        # Check if file already exists (Manual Fallback)
        if os.path.exists(file_path):
            print(f"Found local report for {self.ticker} at {file_path}")
            return file_path
            
        print(f"Attempting to download report for {self.ticker}...")
        try:
            # First, visit the homepage/parent to get cookies if it's a session-link
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
            print(f"💡 Hint: Download the PDF manually, rename it to '{os.path.basename(file_path)}' and place it in the '{self.reports_dir}/' folder.")
            return ""

    def extract_text_from_pdf(self, pdf_path: str) -> str:
        """Extracts text from PDF (reads first 100 pages to find MD&A)."""
        try:
            reader = PdfReader(pdf_path)
            text = ""
            for i in range(min(len(reader.pages), 100)): 
                text += reader.pages[i].extract_text() + "\n"
            return text
        except Exception as e:
            print(f"Error reading PDF {pdf_path}: {e}")
            return ""

    def get_key_sections(self, full_text: str) -> Dict[str, str]:
        """Heuristic section extraction for Indian/Global reports."""
        sections = {"mda": ""}
        patterns = [
            r"Management Discussion and Analysis",
            r"Management's Discussion and Analysis",
            r"Director's Report",
            r"Board's Report"
        ]
        for pattern in patterns:
            match = re.search(f"{pattern}", full_text, re.IGNORECASE)
            if match:
                start = match.start()
                sections["mda"] = full_text[start:start+30000] # Increased for Gemini
                break
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

    def analyze_checklist(self, mda_text: str, checklist: str) -> str:
        """
        Pass 2: Expert Analysis using Gemini.
        """
        if not self.model:
            return "AI Error: GOOGLE_API_KEY not found. Please set the environment variable."

        prompt = f"""
        You are a Senior Equity Researcher. I will provide you with a section of an Annual Report (MD&A).
        Your task is to audit this text against the following Fundamental Analysis Checklist:
        
        {checklist}
        
        Analyze the text thoroughly. For each point, provide a summary of your findings.
        Then, suggest specific adjustments to a 2-stage DCF valuation model:
        1. Growth Rate Stage 1 (Years 1-5) offset (e.g., +2%, -3%)
        2. Growth Rate Stage 2 (Years 6-10) offset
        3. Discount Rate (Risk) offset
        
        ANNUAL REPORT TEXT:
        {mda_text}
        
        OUTPUT FORMAT:
        [CHECKLIST AUDIT]
        - Point 1: ...
        ...
        [DCF ADJUSTMENTS]
        - Stage 1 Growth: +/- X%
        - Stage 2 Growth: +/- X%
        - Discount Rate: +/- X%
        """
        
        try:
            response = self.model.generate_content(prompt)
            return response.text
        except Exception as e:
            return f"AI Generation Error: {e}"

    def parse_adjustments(self, ai_response: str) -> Dict[str, float]:
        """
        Pass 3: Extracts numeric offsets from Gemini's text response.
        """
        adjustments = {
            "growth_rate_stage_1_offset": 0.0,
            "growth_rate_stage_2_offset": 0.0,
            "discount_rate_offset": 0.0
        }
        
        # More robust regex: Look for 'Stage 1/2' and a percentage anywhere in the same line
        try:
            # Stage 1
            s1_match = re.search(r"Stage 1.*?([\+\-][0-9.]+)%", ai_response, re.IGNORECASE)
            # Stage 2
            s2_match = re.search(r"Stage 2.*?([\+\-][0-9.]+)%", ai_response, re.IGNORECASE)
            # Discount Rate / WACC
            dr_match = re.search(r"(?:Discount Rate|WACC).*?([\+\-][0-9.]+)%", ai_response, re.IGNORECASE)
            
            if s1_match: adjustments["growth_rate_stage_1_offset"] = float(s1_match.group(1)) / 100
            if s2_match: adjustments["growth_rate_stage_2_offset"] = float(s2_match.group(1)) / 100
            if dr_match: adjustments["discount_rate_offset"] = float(dr_match.group(1)) / 100
        except Exception:
            pass
            
        return adjustments

if __name__ == "__main__":
    # Example flow
    processor = ReportProcessor("AAPL")
