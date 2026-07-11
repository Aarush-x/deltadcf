from src.analysis.research_checklist import ResearchChecklist

def test_quantitative_checks_passing():
    mock_data = {
        'gross_profit': 40,
        'revenue': 100,
        'total_debt': 10,
        'total_assets': 100,
        'operating_cash_flow': 50,
        'return_on_equity': 0.30
    }
    checklist = ResearchChecklist(mock_data)
    checklist.run_quantitative_checks()
    
    assert checklist.results['GPM > 20%']['passed'] is True
    assert checklist.results['Debt Level']['passed'] is True
    assert checklist.results['Positive CFO']['passed'] is True
    assert checklist.results['ROE > 25%']['passed'] is True

def test_quantitative_checks_failing():
    mock_data = {
        'gross_profit': 10,
        'revenue': 100,
        'total_debt': 80,
        'total_assets': 100,
        'operating_cash_flow': -10,
        'return_on_equity': 0.10
    }
    checklist = ResearchChecklist(mock_data)
    checklist.run_quantitative_checks()
    
    assert checklist.results['GPM > 20%']['passed'] is False
    assert checklist.results['Debt Level']['passed'] is False
    assert checklist.results['Positive CFO']['passed'] is False
    assert checklist.results['ROE > 25%']['passed'] is False
