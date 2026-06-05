from src.analysis.dcf import DCFEngine

def test_dcf_intrinsic_value_simple():
    # Simple test case: 100 FCF, 10% growth for 5 years, 3% terminal, 8% discount
    stages = [(5, 0.10)]
    engine = DCFEngine(
        initial_fcf=100,
        growth_stages=stages,
        terminal_rate=0.03,
        discount_rate=0.08
    )
    iv = engine.calculate_intrinsic_value()
    assert iv > 0
    assert isinstance(iv, float)

def test_dcf_price_per_share():
    stages = [(5, 0.10)]
    engine = DCFEngine(100, stages, 0.03, 0.08)
    iv = 2500.0
    net_debt = 500.0
    shares = 100
    # (2500 - 500) / 100 = 20.0
    price = engine.calculate_price_per_share(iv, net_debt, shares)
    assert price == 20.0
