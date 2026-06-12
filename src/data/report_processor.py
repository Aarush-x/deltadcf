import json
import os
import re
import requests
import fitz  # PyMuPDF
from typing import List, Dict, Optional
from edgar import Company, set_identity
from google import genai

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
    Pass 2 & 3: The Researcher and The Adjuster using Gemini 2.0 Flash.
    """
    
    def __init__(self, api_key: Optional[str] = None):
        if api_key:
            self.client = genai.Client(api_key=api_key)
        else:
            self.client = None

    @staticmethod
    def empty_response() -> Dict:
        return {
            "core_business_audit": [],
            "management_integrity": [],
            "valuation_impact": {
                "stage_1_growth_offset": 0.0,
                "stage_2_growth_offset": 0.0,
                "discount_rate_offset": 0.0,
            },
        }

    def parse_structured_response(self, raw: str) -> Dict:
        """Parse JSON from Gemini response, stripping markdown fences if present."""
        text = raw.strip()
        if text.startswith("```"):
            text = re.sub(r"^```(?:json)?\s*", "", text)
            text = re.sub(r"\s*```$", "", text)
        parsed = json.loads(text)
        return {
            "core_business_audit": parsed.get("core_business_audit", []),
            "management_integrity": parsed.get("management_integrity", []),
            "valuation_impact": {
                "stage_1_growth_offset": float(
                    parsed.get("valuation_impact", {}).get("stage_1_growth_offset", 0.0)
                ),
                "stage_2_growth_offset": float(
                    parsed.get("valuation_impact", {}).get("stage_2_growth_offset", 0.0)
                ),
                "discount_rate_offset": float(
                    parsed.get("valuation_impact", {}).get("discount_rate_offset", 0.0)
                ),
            },
        }

    def analyze_checklist(self, context_text: str, checklist: str) -> Dict:
        """
        Expert Analysis with 'Red Flag Filter' and Governance Audit.
        Returns structured JSON matching the valuation schema.
        """
        if not self.client:
            return self.empty_response()

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

        Respond ONLY with a valid JSON object. No Markdown fences, no preamble, no explanation.
        Use this exact schema:
        {{
          "core_business_audit": [
            {{ "id": 1, "title": "string", "status": "PASS" | "FAIL" | "MONITOR", "description": "string" }}
          ],
          "management_integrity": [
            {{ "title": "string", "severity": "Red Flag" | "Caution" | "Pass", "description": "string" }}
          ],
          "valuation_impact": {{
            "stage_1_growth_offset": 0.03,
            "stage_2_growth_offset": 0.01,
            "discount_rate_offset": -0.005
          }}
        }}

        Offset values are decimal fractions (e.g. 0.03 means +3%, -0.005 means -0.5%).
        Include all 10 checklist items in core_business_audit with ids 1 through 10.
        """
        
        try:
            response = self.client.models.generate_content(
                model="gemini-flash-latest",
                contents=prompt,
            )
            return self.parse_structured_response(response.text)
        except Exception as e:
            print(f"AI Analysis Error: {e}")
            return self.empty_response()

if __name__ == "__main__":
    processor = ReportProcessor("AAPL")
