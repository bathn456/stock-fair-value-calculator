import streamlit as st
import pandas as pd
import sys
import os

# Add project root to path to allow imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from data_sources.yahoo_finance import YahooFinanceDataSource
from models.dcf_model import FCFEDCFModel
from data_sources.official_files import OfficialFilesDataSource
from data_sources.web_scraper import FinancialWebScraper
from utils.helpers import validate_ticker, format_number, format_percentage
from utils.firebase_config import initialize_firebase
from datetime import datetime

# Initialize Firebase
db = initialize_firebase()

# Page config
st.set_page_config(
    page_title="FCFE DCF Valuation Tool",
    page_icon="📊",
    layout="wide"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #1E88E5;
        text-align: center;
        margin-bottom: 1rem;
    }
    .sub-header {
        font-size: 1.5rem;
        color: #424242;
        margin-top: 2rem;
        margin-bottom: 1rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        text-align: center;
    }
    .stButton>button {
        width: 100%;
    }
</style>
""", unsafe_allow_html=True)

def main():
    st.markdown('<div class="main-header">FCFE DCF Valuation Analyzer</div>', unsafe_allow_html=True)
    st.markdown('<div style="text-align: center; margin-bottom: 2rem;">Multi-Source Fair Value Calculator</div>', unsafe_allow_html=True)

    # Sidebar for inputs
    with st.sidebar:
        st.header("Analysis Settings")
        user_input = st.text_input("Company Name or Ticker", placeholder="e.g., Apple or AAPL")
        
        st.subheader("Assumptions Override")
        custom_growth_rate = st.number_input("Growth Rate (%)", value=0.0, step=0.1, format="%.1f", help="Leave 0 to use historical rate")
        custom_discount_rate = st.number_input("Discount Rate (%)", value=0.0, step=0.1, format="%.1f", help="Leave 0 to use calculated CAPM")
        custom_terminal_growth = st.number_input("Terminal Growth (%)", value=2.5, step=0.1, format="%.1f")
        
        analyze_btn = st.button("Run Analysis", type="primary")

    if analyze_btn and user_input:
        with st.spinner(f"Analyzing {user_input}..."):
            # Resolve ticker
            if validate_ticker(user_input):
                ticker = user_input.upper()
            else:
                status_text = st.empty()
                status_text.text(f"Searching for ticker for '{user_input}'...")
                ticker = YahooFinanceDataSource.search_company(user_input)
                if not ticker:
                    st.error(f"Could not find ticker for '{user_input}'. Please try entering the ticker symbol directly.")
                    return
                status_text.empty()
            
            st.session_state['current_ticker'] = ticker
            run_analysis(ticker, custom_growth_rate, custom_discount_rate, custom_terminal_growth)

def run_analysis(ticker, custom_growth, custom_discount, custom_terminal):
    # Initialize models
    dcf_model = FCFEDCFModel(terminal_growth_rate=custom_terminal/100)
    
    # 1. Yahoo Finance Analysis
    st.markdown(f"### 📊 Analysis for {ticker}")
    
    yahoo_source = YahooFinanceDataSource(ticker)
    financial_data = yahoo_source.get_financial_data()
    
    if not financial_data:
        st.error("Failed to fetch data from Yahoo Finance")
        return

    # Display Company Info
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Current Price", format_number(financial_data.get('current_price'), '$'))
    with col2:
        st.metric("Market Cap", format_number(financial_data.get('market_cap'), '$', '', 0))
    with col3:
        st.metric("Beta", f"{financial_data.get('beta', 0):.2f}")
    with col4:
        st.metric("Sector", yahoo_source.get_sector())

    # Prepare assumptions
    risk_free_rate = yahoo_source.get_risk_free_rate()
    market_return = yahoo_source.get_market_return()
    
    growth_rate_arg = custom_growth/100 if custom_growth > 0 else None
    
    # Run Calculation
    valuation = dcf_model.calculate_fair_value(
        financial_data,
        risk_free_rate,
        market_return,
        custom_growth_rate=growth_rate_arg
    )
    
    if valuation.get('error'):
        st.error(f"Valuation Error: {valuation['error']}")
        return

    # Display Results
    fair_value = valuation.get('fair_value')
    current_price = financial_data.get('current_price')
    
    if fair_value and current_price:
        upside = ((fair_value - current_price) / current_price) * 100
        
        st.markdown("---")
        res_col1, res_col2, res_col3 = st.columns([1, 2, 1])
        
        with res_col2:
            st.markdown("### Fair Value Estimate")
            st.markdown(f"<h1 style='text-align: center; color: {'#4CAF50' if upside > 0 else '#F44336'}'>{format_number(fair_value, '$')}</h1>", unsafe_allow_html=True)
            
            upside_color = "green" if upside > 0 else "red"
            upside_arrow = "↑" if upside > 0 else "↓"
            st.markdown(f"<h3 style='text-align: center; color: {upside_color}'>{upside_arrow} {format_percentage(upside)} ({'Undervalued' if upside > 0 else 'Overvalued'})</h3>", unsafe_allow_html=True)

            # Save to Firebase Button
            if db:
                if st.button("💾 Save Analysis to Database"):
                    try:
                        doc_ref = db.collection('valuations').add({
                            'ticker': ticker,
                            'company_name': financial_data.get('company_name'),
                            'fair_value': fair_value,
                            'current_price': current_price,
                            'upside_percentage': upside,
                            'timestamp': datetime.now(),
                            'assumptions': valuation.get('assumptions')
                        })
                        st.success(f"Analysis saved successfully!")
                    except Exception as e:
                        st.error(f"Error saving to database: {e}")

    # Detailed Breakdown Tabs
    tab1, tab2, tab3 = st.tabs(["Calculation Details", "Assumptions", "Other Sources"])
    
    with tab1:
        details = valuation.get('details', {})
        st.subheader("DCF Components")
        
        d_col1, d_col2 = st.columns(2)
        with d_col1:
            st.write("**Cash Flow Projections**")
            projections = details.get('projected_fcfe', [])
            proj_df = pd.DataFrame({
                "Year": range(1, len(projections) + 1),
                "Projected FCFE": [format_number(x, '$') for x in projections]
            })
            st.table(proj_df)
            
        with d_col2:
            st.write("**Terminal Value**")
            st.write(f"Terminal Value: {format_number(details.get('terminal_value'), '$')}")
            st.write(f"PV of Terminal Value: {format_number(details.get('terminal_value') / ((1 + valuation['assumptions']['cost_of_equity']/100) ** 5), '$')}") # Approx
            st.write(f"Total Present Value: {format_number(details.get('total_present_value'), '$')}")
            st.write(f"Shares Outstanding: {format_number(details.get('shares_outstanding'), '', '', 0)}")

    with tab2:
        assumptions = valuation.get('assumptions', {})
        st.subheader("Model Assumptions")
        
        a_col1, a_col2 = st.columns(2)
        with a_col1:
            st.info(f"**Growth Rate:** {assumptions.get('growth_rate', 0):.2f}%")
            st.info(f"**Terminal Growth:** {assumptions.get('terminal_growth_rate', 2.5):.2f}%")
        with a_col2:
            st.info(f"**Cost of Equity (WACC):** {assumptions.get('cost_of_equity', 0):.2f}%")
            st.write(f"- Risk Free Rate: {assumptions.get('risk_free_rate', 0):.2f}%")
            st.write(f"- Beta: {assumptions.get('beta', 0):.2f}")
            st.write(f"- Market Return: {assumptions.get('market_return', 0):.2f}%")

    with tab3:
        st.subheader("Comparison with Other Sources")
        
        # SEC Filings
        sec_source = OfficialFilesDataSource(ticker)
        sec_data = sec_source.get_financial_data()
        if sec_data and not sec_data.get('note'):
            sec_val = dcf_model.calculate_fair_value(sec_data)
            st.success(f"SEC Filing Derived Value: {format_number(sec_val.get('fair_value'), '$')}")
        else:
            st.warning("SEC Filing automated analysis unavailable.")
            
        # Web Scraper
        scraper = FinancialWebScraper(ticker)
        web_results = scraper.scrape_all()
        
        if web_results:
            web_df = pd.DataFrame(web_results)
            st.dataframe(web_df[['source', 'fair_value', 'methodology']])
        else:
            st.info("No external analyst estimates found via scraping.")

if __name__ == "__main__":
    main()
