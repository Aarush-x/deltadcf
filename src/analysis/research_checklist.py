from typing import Dict, Any, List

class ResearchChecklist:
    """
    Implements the 10-point Fundamental Analysis checklist.
    Categorizes checks into 'Quantitative' (Data-driven) and 'Qualitative' (AI-driven).
    """
    
    def __init__(self, ticker_data: Dict[str, Any]):
        self.data = ticker_data
        self.results = {}

    def run_quantitative_checks(self):
        """Checks based on structured data (yfinance/edgartools)."""
        
        # 1. Gross Profit Margin > 20%
        gp = self.data.get('gross_profit')
        rev = self.data.get('revenue')
        if gp and rev:
            gpm = gp / rev
            self.results['GPM > 20%'] = {
                'passed': gpm > 0.20,
                'value': f"{gpm:.1%}",
                'insight': "High margin suggests a sustainable moat." if gpm > 0.20 else "Low margin suggests high competition or low pricing power."
            }

        # 4. Debt Level (Leverage)
        total_debt = self.data.get('total_debt', 0)
        total_assets = self.data.get('total_assets', 1)
        debt_to_assets = total_debt / total_assets
        self.results['Debt Level'] = {
            'passed': debt_to_assets < 0.5, # Rule of thumb
            'value': f"D/A: {debt_to_assets:.2f}",
            'insight': "Low leverage is safer." if debt_to_assets < 0.5 else "High leverage increases financial risk."
        }

        # 7. Positive Cash Flow from Operations
        cfo = self.data.get('operating_cash_flow', 0)
        self.results['Positive CFO'] = {
            'passed': cfo > 0,
            'value': f"{cfo:,.0f}",
            'insight': "Generating cash from operations is healthy." if cfo > 0 else "Operating stress detected (negative CFO)."
        }

        # 8. Return on Equity > 25%
        roe = self.data.get('return_on_equity')
        if roe:
            self.results['ROE > 25%'] = {
                'passed': roe > 0.25,
                'value': f"{roe:.1%}",
                'insight': "High ROE is great for investors." if roe > 0.25 else "ROE is below target threshold."
            }

    def get_ai_research_prompts(self) -> List[str]:
        """Generates prompts for the AI to extract qualitative data from MD&A."""
        return [
            "Analyze the business segments: Does the company operate in 1 or 2 simple business lines, or are they overly diversified?",
            "Count the subsidiaries mentioned: Are there an excessive number of subsidiaries that might suggest siphoning of money?",
            "Look for 'Sales vs Receivables' commentary: Is revenue growth backed by actual cash collections or just increasing receivables?",
            "Check inventory trends: Is inventory growing alongside PAT margins? Note the inventory days if mentioned."
        ]

if __name__ == "__main__":
    # Mock data check
    mock_data = {
        'gross_profit': 40,
        'revenue': 100,
        'total_debt': 10,
        'total_assets': 100,
        'operating_cash_flow': 50,
        'return_on_equity': 0.28
    }
    checklist = ResearchChecklist(mock_data)
    checklist.run_quantitative_checks()
    import json
    print(json.dumps(checklist.results, indent=2))
