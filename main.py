"""
FCFE DCF Analyzer - Main Application
Calculates FCFE DCF valuations from multiple sources and compares results
"""
import sys
from typing import List, Dict
from data_sources.yahoo_finance import YahooFinanceDataSource
from data_sources.official_files import OfficialFilesDataSource
from data_sources.web_scraper import FinancialWebScraper
from models.dcf_model import FCFEDCFModel
from utils.display import ResultsDisplay
from utils.helpers import get_logger, validate_ticker

logger = get_logger(__name__)

class FCFEDCFAnalyzer:
    """Main analyzer class that orchestrates the entire valuation process"""
    
    def __init__(self, ticker: str):
        """
        Initialize analyzer
        
        Args:
            ticker: Stock ticker symbol
        """
        self.ticker = ticker.upper()
        self.display = ResultsDisplay()
        self.dcf_model = FCFEDCFModel()
        
    def run_analysis(self) -> List[Dict]:
        """
        Run complete FCFE DCF analysis from all sources
        
        Returns:
            List of valuation results from different sources
        """
        all_results = []
        
        print("\n" + "Starting FCFE DCF Analysis...".center(80))
        print("=" * 80 + "\n")
        
        # Source 1: Yahoo Finance
        print("Source 1: Yahoo Finance API")
        print("-" * 80)
        yahoo_result = self._analyze_yahoo_finance()
        if yahoo_result:
            all_results.append(yahoo_result)
            print("Yahoo Finance analysis complete\n")
        else:
            print("Yahoo Finance analysis failed\n")
        
        # Source 2: Official SEC Filings
        print("Source 2: Official SEC Filings")
        print("-" * 80)
        sec_result = self._analyze_sec_filings()
        if sec_result:
            all_results.append(sec_result)
            print("SEC Filing analysis complete\n")
        else:
            print("SEC Filing analysis failed (this is expected for automated SEC parsing)\n")
        
        # Source 3: Web Scraped Values
        print("Source 3: Financial Websites (Web Scraping)")
        print("-" * 80)
        web_results = self._scrape_web_valuations()
        if web_results:
            all_results.extend(web_results)
            print(f"Found {len(web_results)} web-scraped valuations\n")
        else:
            print("No web-scraped valuations available\n")
        
        return all_results
    
    def _analyze_yahoo_finance(self) -> Dict:
        """Analyze using Yahoo Finance data"""
        try:
            # Fetch data
            yahoo_source = YahooFinanceDataSource(self.ticker)
            financial_data = yahoo_source.get_financial_data()
            
            if not financial_data:
                logger.error("Failed to fetch Yahoo Finance data")
                return None
            
            # Store company info
            self.company_name = financial_data.get('company_name', self.ticker)
            self.current_price = financial_data.get('current_price')
            
            # Get risk metrics
            risk_free_rate = yahoo_source.get_risk_free_rate()
            market_return = yahoo_source.get_market_return()
            
            # Run DCF calculation
            valuation = self.dcf_model.calculate_fair_value(
                financial_data,
                risk_free_rate,
                market_return
            )
            
            if valuation.get('error'):
                logger.error(f"Yahoo Finance valuation error: {valuation['error']}")
                return None
            
            return {
                'source': 'Yahoo Finance (yfinance API)',
                'fair_value': valuation.get('fair_value'),
                'methodology': 'FCFE DCF Model',
                'details': valuation.get('details'),
                'assumptions': valuation.get('assumptions')
            }
            
        except Exception as e:
            logger.error(f"Error in Yahoo Finance analysis: {str(e)}")
            return None
    
    def _analyze_sec_filings(self) -> Dict:
        """Analyze using SEC filings"""
        try:
            sec_source = OfficialFilesDataSource(self.ticker)
            financial_data = sec_source.get_financial_data()
            
            # Note: SEC filing parsing is complex and often fails
            # This is a known limitation of automated SEC data extraction
            
            if not financial_data or financial_data.get('note'):
                logger.warning("SEC filing data not available for automated parsing")
                return None
            
            # If we have data, run DCF
            valuation = self.dcf_model.calculate_fair_value(financial_data)
            
            if valuation.get('error'):
                return None
            
            return {
                'source': 'SEC 10-K Filing',
                'fair_value': valuation.get('fair_value'),
                'methodology': 'FCFE DCF Model',
                'details': valuation.get('details')
            }
            
        except Exception as e:
            logger.error(f"Error in SEC filing analysis: {str(e)}")
            return None
    
    def _scrape_web_valuations(self) -> List[Dict]:
        """Scrape valuations from financial websites"""
        try:
            scraper = FinancialWebScraper(self.ticker)
            results = scraper.scrape_all()
            
            # Filter out results without fair values
            valid_results = [r for r in results if r.get('fair_value')]
            
            return valid_results
            
        except Exception as e:
            logger.error(f"Error in web scraping: {str(e)}")
            return []
    
    def display_results(self, results: List[Dict]):
        """Display all results in a formatted table"""
        if not results:
            self.display.display_error("No valuation results available")
            return
        
        # Display header
        company_name = getattr(self, 'company_name', self.ticker)
        current_price = getattr(self, 'current_price', None)
        
        self.display.display_company_header(self.ticker, company_name, current_price)
        
        # Display comparison table
        self.display.display_comparison_table(results, current_price)
        
        # Display detailed calculation for first result (Yahoo Finance)
        if results and results[0].get('details'):
            print("\n")
            self.display.display_calculation_details(results[0]['details'])
        
        if results and results[0].get('assumptions'):
            print("\n")
            print("-" * 80)
            print("  KEY ASSUMPTIONS")
            print("-" * 80)
            assumptions_display = {
                "Growth Rate": f"{results[0]['assumptions'].get('growth_rate', 0):.2f}%",
                "Cost of Equity (Discount Rate)": f"{results[0]['assumptions'].get('cost_of_equity', 0):.2f}%",
                "Terminal Growth Rate": f"{results[0]['assumptions'].get('terminal_growth_rate', 2.5):.2f}%",
                "Beta": f"{results[0]['assumptions'].get('beta', 1.0):.2f}",
                "Risk-Free Rate": f"{results[0]['assumptions'].get('risk_free_rate', 4.5):.2f}%",
            }
            self.display.display_calculation_details(assumptions_display)

def main():
    """Main entry point"""
    print("\n" + "=" * 80)
    print("  FCFE DCF VALUATION ANALYZER".center(80))
    print("  Multi-Source Fair Value Calculator".center(80))
    print("=" * 80)
    
    # Get input from user
    if len(sys.argv) > 1:
        user_input = sys.argv[1]
    else:
        user_input = input("\nEnter company name or ticker symbol: ").strip()
    
    # Check if input looks like a ticker (short, no spaces)
    if validate_ticker(user_input):
        ticker = user_input.upper()
    else:
        print(f"\nSearching for ticker for '{user_input}'...")
        ticker = YahooFinanceDataSource.search_company(user_input)
        
        if ticker:
            print(f"Found ticker: {ticker}")
        else:
            print(f"\nError: Could not find ticker for '{user_input}'. Please try entering the ticker symbol directly.")
            return

    # Validate ticker again just in case
    if not validate_ticker(ticker):
        print("\nError: Invalid ticker symbol found. Please use 1-5 letter ticker (e.g., AAPL, MSFT)")
        return
    
    # Run analysis
    analyzer = FCFEDCFAnalyzer(ticker)
    results = analyzer.run_analysis()
    
    # Display results
    analyzer.display_results(results)
    
    print("\n" + "=" * 80)
    print("  Analysis Complete".center(80))
    print("=" * 80 + "\n")
    
    # Disclaimer
    print("DISCLAIMER: This analysis is for educational purposes only.")
    print("   Always conduct thorough research before making investment decisions.\n")

if __name__ == "__main__":
    main()
