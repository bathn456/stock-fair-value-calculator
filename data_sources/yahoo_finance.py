"""
Yahoo Finance data source for FCFE DCF calculation
"""
import yfinance as yf
import pandas as pd
import numpy as np
from typing import Dict, Optional
from utils.helpers import get_logger, handle_errors

logger = get_logger(__name__)

class YahooFinanceDataSource:
    """Retrieve financial data from Yahoo Finance"""
    
    def __init__(self, ticker: str):
        self.ticker = ticker.upper()
        self.stock = None
        self.info = None
        
    @staticmethod
    def search_company(query: str) -> Optional[str]:
        """Search for company ticker by name"""
        try:
            # Yahoo Finance Autocomplete API
            url = f"https://query2.finance.yahoo.com/v1/finance/search?q={query}"
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
            response = requests.get(url, headers=headers, timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                if 'quotes' in data and len(data['quotes']) > 0:
                    # Return the first equity result
                    for quote in data['quotes']:
                        if quote.get('quoteType') == 'EQUITY' and quote.get('isYahooFinance', True):
                            return quote['symbol']
                    # Fallback to first result if no equity found
                    return data['quotes'][0]['symbol']
            return None
        except Exception as e:
            logger.error(f"Error searching for company: {str(e)}")
            return None
        
    @handle_errors
    def fetch_data(self) -> bool:
        """Fetch stock data from Yahoo Finance"""
        logger.info(f"Fetching data for {self.ticker} from Yahoo Finance...")
        self.stock = yf.Ticker(self.ticker)
        self.info = self.stock.info
        return self.info is not None
    
    def get_company_name(self) -> str:
        """Get company name"""
        return self.info.get('longName', self.ticker) if self.info else self.ticker
    
    def get_current_price(self) -> Optional[float]:
        """Get current stock price"""
        if self.info:
            return self.info.get('currentPrice') or self.info.get('regularMarketPrice')
        return None
    
    def get_shares_outstanding(self) -> Optional[float]:
        """Get shares outstanding"""
        if self.info:
            return self.info.get('sharesOutstanding')
        return None
    
    @handle_errors
    def get_financial_data(self) -> Dict:
        """
        Extract comprehensive financial data for FCFE calculation
        
        Returns:
            Dict with financial metrics needed for FCFE DCF
        """
        if not self.stock:
            self.fetch_data()
        
        # Get financial statements
        cash_flow = self.stock.cashflow
        balance_sheet = self.stock.balance_sheet
        income_stmt = self.stock.income_stmt
        
        data = {
            'ticker': self.ticker,
            'company_name': self.get_company_name(),
            'current_price': self.get_current_price(),
            'shares_outstanding': self.get_shares_outstanding(),
        }
        
        # Extract cash flow metrics (most recent year)
        if cash_flow is not None and not cash_flow.empty:
            latest_cf = cash_flow.iloc[:, 0]  # Most recent column
            
            data['free_cash_flow'] = latest_cf.get('Free Cash Flow', 
                                                   latest_cf.get('FreeCashFlow'))
            data['operating_cash_flow'] = latest_cf.get('Operating Cash Flow',
                                                         latest_cf.get('TotalCashFromOperatingActivities'))
            data['capital_expenditure'] = latest_cf.get('Capital Expenditure',
                                                         latest_cf.get('CapitalExpenditures'))
        
        # Extract balance sheet metrics
        if balance_sheet is not None and not balance_sheet.empty:
            latest_bs = balance_sheet.iloc[:, 0]
            previous_bs = balance_sheet.iloc[:, 1] if len(balance_sheet.columns) > 1 else None
            
            data['total_debt'] = latest_bs.get('Total Debt', 
                                               latest_bs.get('LongTermDebt', 0))
            data['cash'] = latest_bs.get('Cash', 
                                         latest_bs.get('CashAndCashEquivalents', 0))
            
            # Calculate change in net working capital
            if previous_bs is not None:
                current_nwc = latest_bs.get('Working Capital', 0)
                previous_nwc = previous_bs.get('Working Capital', 0)
                data['change_in_nwc'] = current_nwc - previous_nwc
            else:
                data['change_in_nwc'] = 0
        
        # Extract income statement metrics
        if income_stmt is not None and not income_stmt.empty:
            latest_is = income_stmt.iloc[:, 0]
            
            data['net_income'] = latest_is.get('Net Income', 
                                               latest_is.get('NetIncome'))
            data['revenue'] = latest_is.get('Total Revenue',
                                            latest_is.get('TotalRevenue'))
        
        # Get beta and other risk metrics
        if self.info:
            data['beta'] = self.info.get('beta', 1.0)
            data['market_cap'] = self.info.get('marketCap')
        
        # Calculate historical growth rate
        if cash_flow is not None and len(cash_flow.columns) >= 3:
            try:
                fcf_values = []
                for col in range(min(5, len(cash_flow.columns))):
                    fcf = cash_flow.iloc[:, col].get('Free Cash Flow',
                                                      cash_flow.iloc[:, col].get('FreeCashFlow'))
                    if fcf and not pd.isna(fcf):
                        fcf_values.append(fcf)
                
                if len(fcf_values) >= 2:
                    # Calculate CAGR
                    years = len(fcf_values) - 1
                    if fcf_values[-1] > 0 and fcf_values[0] > 0:
                        growth_rate = (pow(fcf_values[0] / fcf_values[-1], 1/years) - 1) * 100
                        data['historical_growth_rate'] = max(min(growth_rate, 30), -10)  # Cap between -10% and 30%
                    else:
                        data['historical_growth_rate'] = 5.0  # Default
                else:
                    data['historical_growth_rate'] = 5.0
            except:
                data['historical_growth_rate'] = 5.0
        else:
            data['historical_growth_rate'] = 5.0
        
        logger.info(f"Successfully extracted financial data for {self.ticker}")
        return data
    
    @handle_errors
    def get_risk_free_rate(self) -> float:
        """
        Get risk-free rate (10-year Treasury yield)
        Returns approximate rate if unable to fetch
        """
        try:
            treasury = yf.Ticker("^TNX")
            tnx_info = treasury.info
            rate = tnx_info.get('regularMarketPrice', 4.5)  # Default to 4.5% if not available
            return rate / 100 if rate > 1 else rate  # Convert to decimal if needed
        except:
            logger.warning("Could not fetch risk-free rate, using default 4.5%")
            return 0.045
    
    @handle_errors
    def get_market_return(self) -> float:
        """
        Get expected market return
        Historical S&P 500 average is ~10%
        """
        return 0.10
