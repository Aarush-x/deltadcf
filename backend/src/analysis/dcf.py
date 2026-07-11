from typing import List, Tuple

class DCFEngine:
    """
    Calculates intrinsic value using a Multi-Stage Discounted Cash Flow (DCF) model.
    """
    
    def __init__(self, 
                 initial_fcf: float, 
                 growth_stages: List[Tuple[int, float]], # List of (years, rate)
                 terminal_rate: float, 
                 discount_rate: float):
        if discount_rate <= terminal_rate:
            raise ValueError("Discount rate must be strictly greater than the terminal rate to calculate a stable terminal value.")
        self.initial_fcf = initial_fcf
        self.growth_stages = growth_stages
        self.terminal_rate = terminal_rate
        self.discount_rate = discount_rate

    def calculate_intrinsic_value(self) -> float:
        """
        Performs the DCF calculation.
        Intrinsic Value = PV of Projected FCF + PV of Terminal Value
        """
        projected_fcfs = []
        current_fcf = self.initial_fcf
        
        # 1. Project FCF for each growth stage
        for years, rate in self.growth_stages:
            for _ in range(years):
                current_fcf *= (1 + rate)
                projected_fcfs.append(current_fcf)
            
        # 2. Discount FCFs to Present Value
        pv_fcfs = sum([fcf / (1 + self.discount_rate)**(i+1) 
                       for i, fcf in enumerate(projected_fcfs)])
        
        # 3. Calculate Terminal Value
        # TV = FCF_n * (1 + g) / (WACC - g)
        terminal_value = (projected_fcfs[-1] * (1 + self.terminal_rate)) / \
                         (self.discount_rate - self.terminal_rate)
        
        # 4. Discount Terminal Value to Present Value
        total_years = sum(years for years, _ in self.growth_stages)
        pv_terminal_value = terminal_value / (1 + self.discount_rate)**total_years
        
        return pv_fcfs + pv_terminal_value

    def calculate_price_per_share(self, 
                                  intrinsic_value: float, 
                                  net_debt: float, 
                                  shares_outstanding: int) -> float:
        """Calculates price per share: (Equity Value) / Shares."""
        if not shares_outstanding or shares_outstanding <= 0:
            raise ValueError("Shares outstanding must be greater than zero.")
        equity_value = intrinsic_value - net_debt
        return equity_value / shares_outstanding

if __name__ == "__main__":
    # Example calculation: 18% for 5 years, then 10% for 5 years
    stages = [(5, 0.18), (5, 0.10)]
    engine = DCFEngine(initial_fcf=100, growth_stages=stages, terminal_rate=0.03, discount_rate=0.08)
    iv = engine.calculate_intrinsic_value()
    print(f"Intrinsic Value (Multi-Stage): {iv:.2f}")
