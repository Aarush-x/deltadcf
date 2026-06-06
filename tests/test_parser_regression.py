from src.data.report_processor import AIResearcher

def test_parse_adjustments_robustness():
    ai = AIResearcher()
    
    # Test case 1: Gemini's preferred phrasing "Growth Rate Stage 1"
    response1 = """
    [DCF ADJUSTMENTS]
    - Growth Rate Stage 1: +2.0%
    - Growth Rate Stage 2: +1.0%
    - Discount Rate: -0.5%
    """
    adj1 = ai.parse_adjustments(response1)
    assert adj1['growth_rate_stage_1_offset'] == 0.02
    assert adj1['growth_rate_stage_2_offset'] == 0.01
    assert adj1['discount_rate_offset'] == -0.005

    # Test case 2: Bolded and bulleted
    response2 = """
    * **Stage 1 Growth**: **+3.00%**
    * **Stage 2 Growth**: **+0.5%**
    * **WACC**: **-0.25%**
    """
    adj2 = ai.parse_adjustments(response2)
    assert adj2['growth_rate_stage_1_offset'] == 0.03
    assert adj2['growth_rate_stage_2_offset'] == 0.005
    assert adj2['discount_rate_offset'] == -0.0025

    # Test case 3: Minimal labels
    response3 = "Stage 1: +1.5%, Stage 2: -1.0%, Discount Rate: +0.1%"
    adj3 = ai.parse_adjustments(response3)
    assert adj3['growth_rate_stage_1_offset'] == 0.015
    assert adj3['growth_rate_stage_2_offset'] == -0.01
    assert adj3['discount_rate_offset'] == 0.001
