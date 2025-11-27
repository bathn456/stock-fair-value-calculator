"""
Display utilities for formatting and presenting results
"""
from tabulate import tabulate
from typing import List, Dict, Optional
from utils.helpers import format_number, format_percentage

class ResultsDisplay:
    """Format and display FCFE DCF analysis results"""
    
    @staticmethod
    def display_company_header(ticker: str, company_name: str, current_price: Optional[float]):
        """Display company information header"""
        print("\n" + "=" * 80)
        print(f"  FCFE DCF VALUATION ANALYSIS")
        print("=" * 80)
        print(f"Company: {company_name} ({ticker})")
        if current_price:
            print(f"Current Market Price: {format_number(current_price, '$')}")
        print("=" * 80 + "\n")
    
    @staticmethod
    def display_comparison_table(results: List[Dict], current_price: Optional[float]):
        """
        Display comparison table of all FCFE DCF valuations
        
        Args:
            results: List of dicts with keys: source, fair_value, methodology
            current_price: Current market price for comparison
        """
        if not results:
            print("No valuation results available.")
            return
        
        table_data = []
        headers = ["Source", "Fair Value", "Upside/Downside", "Methodology"]
        
        for result in results:
            source = result.get('source', 'Unknown')
            fair_value = result.get('fair_value')
            methodology = result.get('methodology', 'FCFE DCF')
            
            # Format fair value
            fair_value_str = format_number(fair_value, '$') if fair_value else "N/A"
            
            # Calculate upside/downside
            if fair_value and current_price and current_price > 0:
                upside = ((fair_value - current_price) / current_price) * 100
                upside_str = format_percentage(upside)
                
                # Add color coding (basic text indicators)
                if upside > 20:
                    upside_str = f"UP {upside_str} (Undervalued)"
                elif upside < -20:
                    upside_str = f"DOWN {upside_str} (Overvalued)"
                else:
                    upside_str = f"- {upside_str} (Fair)"
            else:
                upside_str = "N/A"
            
            table_data.append([source, fair_value_str, upside_str, methodology])
        
        print(tabulate(table_data, headers=headers, tablefmt="grid"))
        
        # Calculate average if we have multiple results
        if len(results) > 1:
            valid_values = [r['fair_value'] for r in results if r.get('fair_value')]
            if valid_values:
                avg_value = sum(valid_values) / len(valid_values)
                print(f"\nAverage Fair Value: {format_number(avg_value, '$')}")
                
                if current_price and current_price > 0:
                    avg_upside = ((avg_value - current_price) / current_price) * 100
                    print(f"Average Upside/Downside: {format_percentage(avg_upside)}")
    
    @staticmethod
    def display_calculation_details(details: Dict):
        """Display detailed calculation breakdown"""
        print("\n" + "-" * 80)
        print("  CALCULATION DETAILS")
        print("-" * 80)
        
        calc_data = []
        for key, value in details.items():
            if isinstance(value, (int, float)):
                formatted_value = format_number(value, '$')
            else:
                formatted_value = str(value)
            calc_data.append([key, formatted_value])
        
        print(tabulate(calc_data, headers=["Metric", "Value"], tablefmt="simple"))
    
    @staticmethod
    def display_error(message: str):
        """Display error message"""
        print(f"\nERROR: {message}\n")
    
    @staticmethod
    def display_warning(message: str):
        """Display warning message"""
        print(f"\nWARNING: {message}\n")
    
    @staticmethod
    def display_success(message: str):
        """Display success message"""
        print(f"\nSUCCESS: {message}\n")
