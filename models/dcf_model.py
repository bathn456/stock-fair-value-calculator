"""
DCF Model for FCFE valuation
"""
from typing import Dict, Optional
from models.fcfe_calculator import FCFECalculator
from utils.helpers import get_logger

logger = get_logger(__name__)

class FCFEDCFModel:
    """Complete FCFE DCF valuation model"""
    
    def __init__(
        self,
        projection_years: int = 5,
        terminal_growth_rate: float = 0.025,  # 2.5% perpetual growth
    ):
        """
        Initialize DCF model
        
        Args:
            projection_years: Number of years to project (default 5)
            terminal_growth_rate: Perpetual growth rate (default 2.5%)
        """
        self.projection_years = projection_years
        self.terminal_growth_rate = terminal_growth_rate
        self.calculator = FCFECalculator()
    
    def calculate_fair_value(
        self,
        financial_data: Dict,
        risk_free_rate: float = 0.045,
        market_return: float = 0.10,
        custom_growth_rate: Optional[float] = None
    ) -> Dict:
        """
        Calculate fair value using FCFE DCF methodology
        
        Args:
            financial_data: Dict containing financial metrics
            risk_free_rate: Risk-free rate (default 4.5%)
            market_return: Expected market return (default 10%)
            custom_growth_rate: Override growth rate (optional)
            
        Returns:
            Dict with fair value and calculation details
        """
        logger.info("=" * 60)
        logger.info("FCFE DCF VALUATION CALCULATION")
        logger.info("=" * 60)
        
        result = {
            'fair_value': None,
            'details': {},
            'assumptions': {},
            'error': None
        }
        
        try:
            # Step 1: Calculate current FCFE
            current_fcfe = self.calculator.calculate_fcfe(financial_data)
            if not current_fcfe or current_fcfe <= 0:
                result['error'] = "Could not calculate valid FCFE"
                return result
            
            result['details']['current_fcfe'] = current_fcfe
            
            # Step 2: Determine growth rate
            growth_rate = custom_growth_rate
            if growth_rate is None:
                growth_rate = financial_data.get('historical_growth_rate', 5.0) / 100
                # Cap growth rate at reasonable levels
                growth_rate = max(min(growth_rate, 0.25), -0.05)  # Between -5% and 25%
            
            result['assumptions']['growth_rate'] = growth_rate * 100  # Store as percentage
            
            # Step 3: Calculate cost of equity
            beta = financial_data.get('beta', 1.0)
            cost_of_equity = self.calculator.calculate_cost_of_equity(
                risk_free_rate, beta, market_return
            )
            
            result['assumptions']['cost_of_equity'] = cost_of_equity * 100
            result['assumptions']['beta'] = beta
            result['assumptions']['risk_free_rate'] = risk_free_rate * 100
            result['assumptions']['market_return'] = market_return * 100
            
            # Step 4: Project future FCFE
            projected_fcfe = self.calculator.project_fcfe(
                current_fcfe, growth_rate, self.projection_years
            )
            
            result['details']['projected_fcfe'] = projected_fcfe
            
            # Step 5: Calculate terminal value
            terminal_value = self.calculator.calculate_terminal_value(
                projected_fcfe[-1],
                self.terminal_growth_rate,
                cost_of_equity
            )
            
            result['details']['terminal_value'] = terminal_value
            result['assumptions']['terminal_growth_rate'] = self.terminal_growth_rate * 100
            
            # Step 6: Calculate present value
            total_pv = self.calculator.calculate_present_value(
                projected_fcfe,
                terminal_value,
                cost_of_equity
            )
            
            result['details']['total_present_value'] = total_pv
            
            # Step 7: Calculate per-share value
            shares_outstanding = financial_data.get('shares_outstanding')
            if not shares_outstanding or shares_outstanding <= 0:
                result['error'] = "Invalid shares outstanding"
                return result
            
            fair_value = self.calculator.calculate_per_share_value(
                total_pv,
                shares_outstanding
            )
            
            result['fair_value'] = fair_value
            result['details']['shares_outstanding'] = shares_outstanding
            
            # Add current price for comparison
            current_price = financial_data.get('current_price')
            if current_price:
                result['details']['current_price'] = current_price
                result['details']['upside_percentage'] = ((fair_value - current_price) / current_price * 100)
            
            logger.info("=" * 60)
            logger.info(f"FAIR VALUE PER SHARE: ${fair_value:.2f}")
            logger.info("=" * 60)
            
        except Exception as e:
            logger.error(f"Error in DCF calculation: {str(e)}")
            result['error'] = str(e)
        
        return result
    
    def sensitivity_analysis(
        self,
        financial_data: Dict,
        risk_free_rate: float = 0.045,
        market_return: float = 0.10,
        growth_rates: list = None,
        discount_rates: list = None
    ) -> Dict:
        """
        Perform sensitivity analysis on key assumptions
        
        Args:
            financial_data: Dict containing financial metrics
            risk_free_rate: Risk-free rate
            market_return: Expected market return
            growth_rates: List of growth rates to test
            discount_rates: List of discount rates to test
            
        Returns:
            Dict with sensitivity analysis results
        """
        if growth_rates is None:
            growth_rates = [0.03, 0.05, 0.07, 0.10, 0.15]
        
        results = {
            'growth_sensitivity': [],
            'base_case': None
        }
        
        # Test different growth rates
        for gr in growth_rates:
            valuation = self.calculate_fair_value(
                financial_data,
                risk_free_rate,
                market_return,
                custom_growth_rate=gr
            )
            
            results['growth_sensitivity'].append({
                'growth_rate': gr * 100,
                'fair_value': valuation.get('fair_value')
            })
            
            if gr == 0.05:  # Base case at 5%
                results['base_case'] = valuation
        
        return results
