"""
Helper utilities for data validation and formatting
"""
import logging
from functools import wraps
from typing import Optional

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def get_logger(name: str):
    """Get a logger instance"""
    return logging.getLogger(name)

def handle_errors(func):
    """Decorator to handle errors gracefully"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        logger = get_logger(func.__module__)
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logger.error(f"Error in {func.__name__}: {str(e)}")
            return None
    return wrapper

def format_number(value: Optional[float], prefix: str = "", suffix: str = "", decimals: int = 2) -> str:
    """Format a number with prefix and suffix"""
    if value is None:
        return "N/A"
    return f"{prefix}{value:,.{decimals}f}{suffix}"

def format_percentage(value: Optional[float], decimals: int = 2) -> str:
    """Format a value as percentage"""
    if value is None:
        return "N/A"
    return f"{value:.{decimals}f}%"

def safe_divide(numerator: float, denominator: float, default: float = 0.0) -> float:
    """Safely divide two numbers"""
    try:
        if denominator == 0:
            return default
        return numerator / denominator
    except:
        return default

def validate_ticker(ticker: str) -> bool:
    """Validate ticker symbol format"""
    if not ticker:
        return False
    # Basic validation: 1-5 uppercase letters
    return ticker.isalpha() and 1 <= len(ticker) <= 5
