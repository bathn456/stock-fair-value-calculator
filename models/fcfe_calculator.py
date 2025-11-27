"""
FCFE (Free Cash Flow to Equity) Calculator
"""
import numpy as np
from typing import Dict, Optional
from utils.helpers import get_logger, safe_divide

logger = get_logger(__name__)

class FCFECalculator:
    """Calculate Free Cash Flow to Equity"""
    
    @staticmethod
    def calculate_fcfe(financial_data: Dict) -> Optional[float]:
        """
        Calculate FCFE using the formula:
        FCFE = Net Income - (CapEx - Depreciation) - Change in NWC + (New Debt - Debt Repayment)
        
        Simplified approach when detailed data unavailable:
        FCFE ≈ Free Cash Flow (from cash flow statement)
        
        Args:
            financial_data: Dict containing financial metrics
            
        Returns:
            FCFE value or None
        """
        try:
            # Try to use Free Cash Flow directly if available
            fcf = financial_data.get('free_cash_flow')
            if fcf and fcf > 0:
                logger.info(f"Using Free Cash Flow as FCFE: ${fcf:,.0f}")
                return fcf
            
            # Alternative: Calculate from components
            net_income = financial_data.get('net_income', 0)
            capex = financial_data.get('capital_expenditure', 0)
            change_nwc = financial_data.get('change_in_nwc', 0)
            
            # Simplified FCFE
            fcfe = net_income + capex - change_nwc  # capex is usually negative
            
            if fcfe > 0:
                logger.info(f"Calculated FCFE from components: ${fcfe:,.0f}")
                return fcfe
            
            # If still no valid FCFE, try operating cash flow minus capex
            operating_cf = financial_data.get('operating_cash_flow', 0)
            if operating_cf and capex:
                fcfe = operating_cf + capex  # capex is negative
                if fcfe > 0:
                    logger.info(f"Calculated FCFE from OCF - CapEx: ${fcfe:,.0f}")
                    return fcfe
            
            logger.warning("Could not calculate valid FCFE")
            return None
            
        except Exception as e:
            logger.error(f"Error calculating FCFE: {str(e)}")
            return None
    
    @staticmethod
    def calculate_cost_of_equity(risk_free_rate: float, beta: float, market_return: float) -> float:
        """
        Calculate Cost of Equity using CAPM:
        Cost of Equity = Risk-Free Rate + Beta × (Market Return - Risk-Free Rate)
        
        Args:
            risk_free_rate: Risk-free rate (e.g., 10-year Treasury)
            beta: Stock beta
            market_return: Expected market return
            
        Returns:
            Cost of equity as decimal
        """
        market_risk_premium = market_return - risk_free_rate
        cost_of_equity = risk_free_rate + (beta * market_risk_premium)
        
        logger.info(f"Cost of Equity (CAPM): {cost_of_equity*100:.2f}%")
        logger.info(f"  Risk-Free Rate: {risk_free_rate*100:.2f}%")
        logger.info(f"  Beta: {beta:.2f}")
        logger.info(f"  Market Risk Premium: {market_risk_premium*100:.2f}%")
        
        return cost_of_equity
    
    @staticmethod
    def project_fcfe(
        current_fcfe: float,
        growth_rate: float,
        years: int = 5
    ) -> list:
        """
        Project FCFE for future years
        
        Args:
            current_fcfe: Current year FCFE
            growth_rate: Annual growth rate (as decimal, e.g., 0.05 for 5%)
            years: Number of years to project
            
        Returns:
            List of projected FCFE values
        """
        projections = []
        fcfe = current_fcfe
        
        for year in range(1, years + 1):
            fcfe = fcfe * (1 + growth_rate)
            projections.append(fcfe)
            logger.debug(f"Year {year} FCFE: ${fcfe:,.0f}")
        
        return projections
    
    @staticmethod
    def calculate_terminal_value(
        final_fcfe: float,
        terminal_growth_rate: float,
        cost_of_equity: float
    ) -> float:
        """
        Calculate terminal value using Gordon Growth Model:
        Terminal Value = Final FCFE × (1 + g) / (r - g)
        
        Args:
            final_fcfe: FCFE in the final projection year
            terminal_growth_rate: Perpetual growth rate
            cost_of_equity: Cost of equity (discount rate)
            
        Returns:
            Terminal value
        """
        if cost_of_equity <= terminal_growth_rate:
            logger.warning("Cost of equity <= terminal growth rate, adjusting terminal growth")
            terminal_growth_rate = cost_of_equity * 0.5
        
        terminal_value = (final_fcfe * (1 + terminal_growth_rate)) / (cost_of_equity - terminal_growth_rate)
        
        logger.info(f"Terminal Value: ${terminal_value:,.0f}")
        logger.info(f"  Terminal Growth Rate: {terminal_growth_rate*100:.2f}%")
        
        return terminal_value
    
    @staticmethod
    def calculate_present_value(
        future_cash_flows: list,
        terminal_value: float,
        cost_of_equity: float
    ) -> float:
        """
        Calculate present value of all future cash flows
        
        Args:
            future_cash_flows: List of projected FCFE values
            terminal_value: Terminal value
            cost_of_equity: Discount rate
            
        Returns:
            Total present value
        """
        pv_cash_flows = 0
        
        for year, fcfe in enumerate(future_cash_flows, start=1):
            pv = fcfe / ((1 + cost_of_equity) ** year)
            pv_cash_flows += pv
            logger.debug(f"PV of Year {year}: ${pv:,.0f}")
        
        # Present value of terminal value
        terminal_year = len(future_cash_flows)
        pv_terminal = terminal_value / ((1 + cost_of_equity) ** terminal_year)
        
        total_pv = pv_cash_flows + pv_terminal
        
        logger.info(f"PV of Cash Flows: ${pv_cash_flows:,.0f}")
        logger.info(f"PV of Terminal Value: ${pv_terminal:,.0f}")
        logger.info(f"Total Present Value: ${total_pv:,.0f}")
        
        return total_pv
    
    @staticmethod
    def calculate_per_share_value(
        total_equity_value: float,
        shares_outstanding: float,
        cash: float = 0,
        debt: float = 0
    ) -> float:
        """
        Calculate fair value per share
        
        For FCFE, we already have equity value, so we don't add cash or subtract debt
        (that's done in FCFF to Enterprise Value conversion)
        
        Args:
            total_equity_value: Total present value of FCFE
            shares_outstanding: Number of shares outstanding
            cash: Cash and equivalents (optional, usually not adjusted in FCFE)
            debt: Total debt (optional, usually not adjusted in FCFE)
            
        Returns:
            Fair value per share
        """
        # FCFE already represents value to equity holders
        equity_value = total_equity_value
        
        per_share_value = safe_divide(equity_value, shares_outstanding)
        
        logger.info(f"Equity Value: ${equity_value:,.0f}")
        logger.info(f"Shares Outstanding: {shares_outstanding:,.0f}")
        logger.info(f"Fair Value Per Share: ${per_share_value:.2f}")
        
        return per_share_value
