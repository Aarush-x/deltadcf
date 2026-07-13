import pytest
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


def test_dcf_regression_baseline_is_unchanged():
    engine = DCFEngine(
        initial_fcf=100.0,
        growth_stages=[(5, 0.18), (5, 0.10)],
        terminal_rate=0.03,
        discount_rate=0.09,
    )

    assert engine.calculate_intrinsic_value() == pytest.approx(4074.259247636977)

def test_dcf_price_per_share():
    stages = [(5, 0.10)]
    engine = DCFEngine(100, stages, 0.03, 0.08)
    iv = 2500.0
    net_debt = 500.0
    shares = 100
    # (2500 - 500) / 100 = 20.0
    price = engine.calculate_price_per_share(iv, net_debt, shares)
    assert price == 20.0

def test_dcf_discount_rate_guard():
    stages = [(5, 0.10)]
    with pytest.raises(ValueError) as excinfo:
        DCFEngine(100, stages, 0.03, 0.03)
    assert "strictly greater than the terminal rate" in str(excinfo.value)
    
    with pytest.raises(ValueError) as excinfo2:
        DCFEngine(100, stages, 0.03, 0.02)
    assert "strictly greater than the terminal rate" in str(excinfo2.value)

def test_dcf_shares_outstanding_guard():
    stages = [(5, 0.10)]
    engine = DCFEngine(100, stages, 0.03, 0.08)
    with pytest.raises(ValueError) as excinfo:
        engine.calculate_price_per_share(2500.0, 500.0, 0)
    assert "greater than zero" in str(excinfo.value)

    with pytest.raises(ValueError) as excinfo2:
        engine.calculate_price_per_share(2500.0, 500.0, -10)
    assert "greater than zero" in str(excinfo2.value)
