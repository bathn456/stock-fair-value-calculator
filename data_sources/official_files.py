"""
Official financial files data source (SEC filings)
"""
import os
from typing import Dict, Optional
from sec_edgar_downloader import Downloader
import pandas as pd
import re
from utils.helpers import get_logger, handle_errors

logger = get_logger(__name__)

class OfficialFilesDataSource:
    """Retrieve and parse official SEC filings"""
    
    def __init__(self, ticker: str):
        self.ticker = ticker.upper()
        self.download_path = os.path.join(os.path.dirname(__file__), '..', 'sec_filings')
        
    @handle_errors
    def download_latest_10k(self) -> Optional[str]:
        """
        Download the latest 10-K filing
        
        Returns:
            Path to downloaded file or None
        """
        logger.info(f"Downloading SEC 10-K filing for {self.ticker}...")
        
        try:
            dl = Downloader("MyCompany", "my.email@example.com", self.download_path)
            dl.get("10-K", self.ticker, limit=1)
            
            # Find the downloaded file
            ticker_path = os.path.join(self.download_path, 'sec-edgar-filings', self.ticker, '10-K')
            if os.path.exists(ticker_path):
                # Get the most recent filing directory
                filings = [d for d in os.listdir(ticker_path) if os.path.isdir(os.path.join(ticker_path, d))]
                if filings:
                    latest_filing = sorted(filings)[-1]
                    file_path = os.path.join(ticker_path, latest_filing, 'primary-document.html')
                    if os.path.exists(file_path):
                        logger.info(f"Successfully downloaded 10-K for {self.ticker}")
                        return file_path
            
            logger.warning(f"Could not find downloaded 10-K for {self.ticker}")
            return None
            
        except Exception as e:
            logger.error(f"Error downloading 10-K: {str(e)}")
            return None
    
    @handle_errors
    def parse_10k_filing(self, file_path: str) -> Dict:
        """
        Parse 10-K filing to extract financial data
        
        Note: This is a simplified parser. Real-world implementation would need
        more sophisticated parsing using XBRL or detailed HTML parsing.
        
        Returns:
            Dict with extracted financial metrics
        """
        logger.info(f"Parsing 10-K filing for {self.ticker}...")
        
        data = {
            'ticker': self.ticker,
            'source': 'SEC 10-K Filing',
        }
        
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            # Simplified extraction using regex patterns
            # In production, use XBRL parsing for accurate data
            
            # Extract common financial metrics (this is very basic)
            patterns = {
                'net_income': r'Net\s+Income.*?[\$\s]+([\d,]+)',
                'total_debt': r'Total\s+Debt.*?[\$\s]+([\d,]+)',
                'cash': r'Cash\s+and\s+Cash\s+Equivalents.*?[\$\s]+([\d,]+)',
            }
            
            for key, pattern in patterns.items():
                match = re.search(pattern, content, re.IGNORECASE)
                if match:
                    value_str = match.group(1).replace(',', '')
                    try:
                        data[key] = float(value_str) * 1_000_000  # Convert millions to actual value
                    except:
                        pass
            
            logger.info(f"Successfully parsed 10-K for {self.ticker}")
            
        except Exception as e:
            logger.error(f"Error parsing 10-K: {str(e)}")
        
        return data
    
    @handle_errors
    def get_financial_data(self) -> Dict:
        """
        Main method to get financial data from SEC filings
        
        Returns:
            Dict with financial metrics needed for FCFE DCF
        """
        # For demonstration, we'll provide a framework
        # In production, this would parse actual XBRL data from SEC filings
        
        file_path = self.download_latest_10k()
        
        if file_path:
            data = self.parse_10k_filing(file_path)
        else:
            # Return placeholder structure if download fails
            logger.warning(f"Using placeholder data for {self.ticker} - SEC filing could not be retrieved")
            data = {
                'ticker': self.ticker,
                'source': 'SEC Filing (Unavailable)',
                'note': 'SEC filing data could not be retrieved. This is a known limitation of automated SEC data extraction.',
            }
        
        return data
    
    @staticmethod
    def extract_from_excel(file_path: str) -> Dict:
        """
        Alternative method: Extract data from Excel file
        
        Args:
            file_path: Path to Excel file with financial data
            
        Returns:
            Dict with financial metrics
        """
        logger.info(f"Extracting data from Excel file: {file_path}")
        
        try:
            df = pd.read_excel(file_path)
            
            # This would need to be customized based on the Excel format
            # Example structure:
            data = {
                'source': 'Official Excel File',
            }
            
            # Map Excel rows to our data structure
            # This is highly dependent on the actual file format
            for idx, row in df.iterrows():
                metric_name = str(row[0]).lower().strip()
                value = row[1]
                
                if 'net income' in metric_name:
                    data['net_income'] = float(value)
                elif 'free cash flow' in metric_name:
                    data['free_cash_flow'] = float(value)
                # Add more mappings as needed
            
            return data
            
        except Exception as e:
            logger.error(f"Error reading Excel file: {str(e)}")
            return {}
