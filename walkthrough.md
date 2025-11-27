# FCFE DCF Valuation Tool - Walkthrough

This document demonstrates how to use the FCFE DCF Valuation Tool to calculate the fair value of a company using multiple data sources.

## Prerequisites

Ensure you have installed the required dependencies:

```bash
pip install -r requirements.txt
```

## Running the Analysis

To run the analysis for a specific company, use the following command:

```bash
python main.py [TICKER]
```

Example for Apple Inc. (AAPL):

```bash
python main.py AAPL
```

## Understanding the Output

The tool provides a comprehensive analysis including:

1.  **Data Sources**:
    *   **Yahoo Finance**: Uses real-time market data and financial statements.
    *   **SEC Filings**: Attempts to download and parse official 10-K filings.
    *   **Web Scraping**: Checks financial websites for analyst estimates.

2.  **Valuation Results**:
    *   **Fair Value**: The calculated intrinsic value per share.
    *   **Upside/Downside**: The percentage difference between the fair value and the current market price.
    *   **Methodology**: The specific model used (e.g., FCFE DCF).

3.  **Calculation Details**:
    *   **Current FCFE**: Free Cash Flow to Equity for the most recent period.
    *   **Projected FCFE**: Future cash flow projections based on growth assumptions.
    *   **Terminal Value**: The value of the company beyond the projection period.
    *   **Present Value**: The discounted value of all future cash flows.

4.  **Key Assumptions**:
    *   **Growth Rate**: The assumed annual growth rate for the projection period.
    *   **Cost of Equity**: The discount rate used (based on CAPM).
    *   **Terminal Growth Rate**: The long-term growth rate for the terminal value.

## Example Output

```text
================================================================================
                          FCFE DCF VALUATION ANALYZER                           
                       Multi-Source Fair Value Calculator                       
================================================================================

Starting FCFE DCF Analysis...
================================================================================

Source 1: Yahoo Finance API
--------------------------------------------------------------------------------
Yahoo Finance analysis complete

Source 2: Official SEC Filings
--------------------------------------------------------------------------------
SEC Filing analysis failed (this is expected for automated SEC parsing)

Source 3: Financial Websites (Web Scraping)
--------------------------------------------------------------------------------
No web-scraped valuations available

================================================================================
  FCFE DCF VALUATION ANALYSIS
================================================================================
Company: Apple Inc. (AAPL)
Current Market Price: $234.93
================================================================================

+--------------------------------+--------------+-------------------+----------------+
| Source                         | Fair Value   | Upside/Downside   | Methodology    |
+================================+==============+===================+================+
| Yahoo Finance (yfinance API)   | $150.25      | DOWN -36.05%      | FCFE DCF Model |
+--------------------------------+--------------+-------------------+----------------+

Average Fair Value: $150.25
Average Upside/Downside: -36.05%
```

## Troubleshooting

*   **Import Errors**: If you see import errors, ensure you are running the script from the project root directory.
*   **SEC Parsing Failures**: Automated parsing of SEC filings is complex and may fail for some companies. This is expected behavior.
*   **Web Scraping**: Web scraping relies on the structure of third-party websites, which may change. If scraping fails, the tool will simply skip that source.
