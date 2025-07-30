#!/usr/bin/env python3
"""
CONSAR Data Analysis Web App

A Streamlit app for generating CONSAR analysis tables with:
- Date selection
- Interactive table display
- Excel and CSV export options
"""

import streamlit as st
import pandas as pd
import json
import io
from datetime import datetime
from pathlib import Path
import sys
import base64

# Add current directory to path for imports
sys.path.append('.')

# Import existing analyzers
from generate_professional_tables import ProfessionalAUMAnalyzer

# Configure Streamlit page
st.set_page_config(
    page_title="CONSAR Data Analysis",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
.main-header {
    font-size: 2.5rem;
    font-weight: bold;
    color: #1f77b4;
    text-align: center;
    margin-bottom: 2rem;
}
.sub-header {
    font-size: 1.5rem;
    font-weight: bold;
    color: #ff7f0e;
    margin-top: 2rem;
    margin-bottom: 1rem;
}
.metric-card {
    background-color: #f0f2f6;
    padding: 1rem;
    border-radius: 0.5rem;
    border-left: 4px solid #1f77b4;
}
</style>
""", unsafe_allow_html=True)


@st.cache_data
def load_consar_data():
    """Load and cache the CONSAR database."""
    database_path = Path('data/merged_consar_data_2019_2025.json')
    if not database_path.exists():
        st.error(f"Database file not found: {database_path}")
        return None
    
    with open(database_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data

@st.cache_data
def get_available_periods(data):
    """Get all available periods from the data."""
    if not data:
        return []
    
    periods = set()
    for record in data:
        year = record.get('PeriodYear')
        month = record.get('PeriodMonth')
        if year and month:
            periods.add(f"{year}-{month}")
    
    return sorted(periods, reverse=True)

def format_number_with_commas(value):
    """Format numbers with commas and no decimals, converting from thousands to millions."""
    if pd.isna(value) or value == 0:
        return "0"
    # Convert from thousands to millions by dividing by 1000
    value_millions = value / 1000
    return f"{value_millions:,.0f}"

def convert_to_millions_for_download(df):
    """Convert numeric columns from thousands to millions for download data."""
    df_millions = df.copy()
    for col in df_millions.columns:
        if col != 'Afore' and 'as %' not in col:
            df_millions[col] = df_millions[col] / 1000
    return df_millions

def format_percentage_with_commas(value):
    """Format percentages with commas and no decimals."""
    if pd.isna(value) or value == 0:
        return "0.0%"
    return f"{value:.1f}%"

def create_download_link(df, filename, file_format="csv"):
    """Create a download link for DataFrame."""
    if file_format == "csv":
        csv = df.to_csv(index=False)
        b64 = base64.b64encode(csv.encode()).decode()
        href = f'<a href="data:file/csv;base64,{b64}" download="{filename}.csv">Download CSV</a>'
    elif file_format == "excel":
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='CONSAR Analysis')
        excel_data = output.getvalue()
        b64 = base64.b64encode(excel_data).decode()
        href = f'<a href="data:application/vnd.openxmlformats-officedocument.spreadsheetml.sheet;base64,{b64}" download="{filename}.xlsx">Download Excel</a>'
    
    return href

def main():
    # App header
    st.markdown('<div class="main-header">📊 CONSAR Data Analysis Dashboard</div>', unsafe_allow_html=True)
    
    # Load data
    data = load_consar_data()
    if not data:
        st.stop()
    
    periods = get_available_periods(data)
    if not periods:
        st.error("No data periods found in the database.")
        st.stop()
    
    # Sidebar controls
    st.sidebar.header("⚙️ Analysis Settings")
    
    # Period selection
    selected_period = st.sidebar.selectbox(
        "Select Analysis Period",
        options=periods,
        index=0,
        help="Choose the period for analysis"
    )
    
    # Note: All tables are converted from thousands to millions for display
    
    # Table type selection
    table_types = st.sidebar.multiselect(
        "Select Tables to Generate",
        options=[
            "Mutual Funds",
            "Third Party Mandates",
            "Total Active Management"
        ],
        default=["Mutual Funds"],
        help="Choose which tables to display"
    )
    
    # Export options
    st.sidebar.markdown("### 📥 Export Options")
    export_format = st.sidebar.radio(
        "Export Format",
        options=["Excel", "CSV"],
        index=0
    )
    
    # Main content
    if st.sidebar.button("🚀 Generate Analysis", type="primary"):
        if not table_types:
            st.warning("Please select at least one table type.")
            st.stop()
        
        # Display selected parameters
        col1, col2 = st.columns(2)
        with col1:
            st.metric("📅 Period", selected_period)
        with col2:
            st.metric("📊 Tables", len(table_types))
        
        # Generate and display tables
        try:
            # Mutual Funds
            if "Mutual Funds" in table_types:
                st.markdown('<div class="sub-header">📈 Mutual Funds</div>', unsafe_allow_html=True)
                
                # Note: Values converted from thousands to millions for display
                try:
                    # Create custom analyzer for the selected period
                    analyzer_pro = ProfessionalAUMAnalyzer('data/merged_consar_data_2019_2025.json')
                    analyzer_pro.load_data()
                    
                    # Create AUM table for selected period
                    aum_df = analyzer_pro.create_aum_table(selected_period)
                    
                    if aum_df is not None:
                        # Format numbers in the dataframe
                        aum_df_formatted = aum_df.copy()
                        for col in aum_df_formatted.columns:
                            if col != 'Afore' and 'as %' not in col:
                                aum_df_formatted[col] = aum_df_formatted[col].apply(format_number_with_commas)
                            elif 'as %' in col:
                                aum_df_formatted[col] = aum_df_formatted[col].apply(format_percentage_with_commas)
                        
                        with st.expander("AUM Breakdown (USD millions)", expanded=True):
                            st.dataframe(aum_df_formatted, use_container_width=True)
                            
                            # Download links (convert to millions for download)
                            st.markdown("**Download Options:**")
                            col1, col2 = st.columns(2)
                            with col1:
                                aum_df_millions = convert_to_millions_for_download(aum_df)
                                csv_link = create_download_link(aum_df_millions, f"mutual_funds_{selected_period.replace('-', '_')}", "csv")
                                st.markdown(csv_link, unsafe_allow_html=True)
                            with col2:
                                excel_link = create_download_link(aum_df_millions, f"mutual_funds_{selected_period.replace('-', '_')}", "excel")
                                st.markdown(excel_link, unsafe_allow_html=True)
                    else:
                        st.error("No mutual funds data available for this period.")
                        
                except Exception as e:
                    st.error(f"Error generating mutual funds table: {str(e)}")
            
            # Third Party Mandates
            if "Third Party Mandates" in table_types:
                st.markdown('<div class="sub-header">🤝 Third Party Mandates</div>', unsafe_allow_html=True)
                
                try:
                    analyzer_pro = ProfessionalAUMAnalyzer('data/merged_consar_data_2019_2025.json')
                    analyzer_pro.load_data()
                    
                    tp_df = analyzer_pro.create_third_party_mandates_table(selected_period)
                    
                    if tp_df is not None:
                        # Format numbers in the dataframe
                        tp_df_formatted = tp_df.copy()
                        for col in tp_df_formatted.columns:
                            if col != 'Afore' and 'as %' not in col:
                                tp_df_formatted[col] = tp_df_formatted[col].apply(format_number_with_commas)
                            elif 'as %' in col:
                                tp_df_formatted[col] = tp_df_formatted[col].apply(format_percentage_with_commas)
                        
                        with st.expander("AUM Breakdown (USD millions)", expanded=True):
                            st.dataframe(tp_df_formatted, use_container_width=True)
                        
                            # Download links (convert to millions for download)
                            st.markdown("**Download Options:**")
                            col1, col2 = st.columns(2)
                            with col1:
                                tp_df_millions = convert_to_millions_for_download(tp_df)
                                csv_link = create_download_link(tp_df_millions, f"third_party_mandates_{selected_period.replace('-', '_')}", "csv")
                                st.markdown(csv_link, unsafe_allow_html=True)
                            with col2:
                                excel_link = create_download_link(tp_df_millions, f"third_party_mandates_{selected_period.replace('-', '_')}", "excel")
                                st.markdown(excel_link, unsafe_allow_html=True)
                    else:
                        st.error("No third party mandates data available for this period.")
                        
                except Exception as e:
                    st.error(f"Error generating third party mandates table: {str(e)}")
            
            # Total Active Management
            if "Total Active Management" in table_types:
                st.markdown('<div class="sub-header">📊 Total Active Management</div>', unsafe_allow_html=True)
                
                try:
                    analyzer_pro = ProfessionalAUMAnalyzer('data/merged_consar_data_2019_2025.json')
                    analyzer_pro.load_data()
                    
                    active_df = analyzer_pro.create_total_active_management_table(selected_period)
                    
                    if active_df is not None:
                        # Format numbers in the dataframe
                        active_df_formatted = active_df.copy()
                        for col in active_df_formatted.columns:
                            if col != 'Afore' and 'as %' not in col:
                                active_df_formatted[col] = active_df_formatted[col].apply(format_number_with_commas)
                            elif 'as %' in col:
                                active_df_formatted[col] = active_df_formatted[col].apply(format_percentage_with_commas)
                        
                        with st.expander("AUM Breakdown (USD millions)", expanded=True):
                            st.dataframe(active_df_formatted, use_container_width=True)
                        
                            # Download links (convert to millions for download)
                            st.markdown("**Download Options:**")
                            col1, col2 = st.columns(2)
                            with col1:
                                active_df_millions = convert_to_millions_for_download(active_df)
                                csv_link = create_download_link(active_df_millions, f"total_active_management_{selected_period.replace('-', '_')}", "csv")
                                st.markdown(csv_link, unsafe_allow_html=True)
                            with col2:
                                excel_link = create_download_link(active_df_millions, f"total_active_management_{selected_period.replace('-', '_')}", "excel")
                                st.markdown(excel_link, unsafe_allow_html=True)
                    else:
                        st.error("No total active management data available for this period.")
                        
                except Exception as e:
                    st.error(f"Error generating total active management table: {str(e)}")
                    
        except Exception as e:
            st.error(f"An error occurred: {str(e)}")
            st.exception(e)
    
    else:
        # Default view - show available data info
        st.info("👆 Configure your analysis settings in the sidebar and click 'Generate Analysis' to begin.")
        
        # Show data overview
        st.markdown("### 📋 Data Overview")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("📊 Total Records", f"{len(data):,}")
        
        with col2:
            st.metric("📅 Available Periods", len(periods))
        
        with col3:
            latest_period = periods[0] if periods else "N/A"
            st.metric("🗓️ Latest Period", latest_period)
        
        # Show available periods
        if periods:
            st.markdown("### 📅 Available Analysis Periods")
            periods_df = pd.DataFrame({
                'Period': periods,
                'Year': [p.split('-')[0] for p in periods],
                'Month': [p.split('-')[1] for p in periods]
            })
            st.dataframe(periods_df, use_container_width=True, hide_index=True)

if __name__ == "__main__":
    main()