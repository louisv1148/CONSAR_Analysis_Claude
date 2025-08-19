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
from growth_analysis import GrowthAnalyzer

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
    
    # Analysis type selection
    analysis_type = st.sidebar.radio(
        "Analysis Type",
        options=["Current Period Analysis", "Growth Analysis"],
        index=0,
        help="Choose between current period data or growth analysis across time periods"
    )
    
    if analysis_type == "Current Period Analysis":
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
    else:
        # Growth analysis doesn't need table selection - shows all categories
        table_types = ["Growth Analysis"]
    
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
            if analysis_type == "Growth Analysis":
                # Growth Analysis Section
                st.markdown('<div class="sub-header">📈 Active Management Growth Analysis</div>', unsafe_allow_html=True)
                st.markdown("Comparing mutual funds, third party mandates, and total active management across different time periods.")
                
                with st.spinner("Calculating growth rates..."):
                    try:
                        analyzer_growth = GrowthAnalyzer('data/merged_consar_data_2019_2025.json')
                        growth_df = analyzer_growth.run_analysis()
                        
                        if growth_df is not None and not growth_df.empty:
                            # Current period info
                            current_period = growth_df['current_period'].iloc[0]
                            st.info(f"📊 **Current Period**: {current_period}")
                            
                            # Industry totals for each period
                            periods = growth_df['Period'].unique()
                            
                            # Create tabs for different time periods
                            available_periods = [period for period in ['MoM', 'YTD', '1Y', '3Y', '5Y'] if period in periods]
                            tab_cols = st.tabs([f"{period} Growth" for period in available_periods])
                            
                            for i, period in enumerate(available_periods):
                                with tab_cols[i]:
                                        period_df = growth_df[growth_df['Period'] == period].copy()
                                        
                                        # Industry totals
                                        st.markdown(f"#### 🏢 Industry Totals - {period}")
                                        
                                        total_mf_current = period_df['mutual_funds_current'].sum()
                                        total_mf_historical = period_df['mutual_funds_historical'].sum()
                                        total_tp_current = period_df['third_party_current'].sum()
                                        total_tp_historical = period_df['third_party_historical'].sum()
                                        total_active_current = period_df['total_active_current'].sum()
                                        total_active_historical = period_df['total_active_historical'].sum()
                                        
                                        # Calculate industry growth rates
                                        mf_growth = ((total_mf_current - total_mf_historical) / total_mf_historical * 100) if total_mf_historical > 0 else 0
                                        tp_growth = ((total_tp_current - total_tp_historical) / total_tp_historical * 100) if total_tp_historical > 0 else 0
                                        active_growth = ((total_active_current - total_active_historical) / total_active_historical * 100) if total_active_historical > 0 else 0
                                        
                                        col1, col2, col3 = st.columns(3)
                                        
                                        with col1:
                                            st.metric(
                                                "💰 Mutual Funds", 
                                                f"${total_mf_current/1e6:,.0f}M",
                                                f"{mf_growth:+.1f}%"
                                            )
                                        
                                        with col2:
                                            st.metric(
                                                "🤝 Third Party", 
                                                f"${total_tp_current/1e6:,.0f}M",
                                                f"{tp_growth:+.1f}%"
                                            )
                                        
                                        with col3:
                                            st.metric(
                                                "📊 Total Active", 
                                                f"${total_active_current/1e6:,.0f}M",
                                                f"{active_growth:+.1f}%"
                                            )
                                        
                                        # Separate tables for each concept
                                        st.markdown(f"#### 🏦 Afore Performance - {period}")
                                        
                                        # 1. Mutual Funds Table
                                        st.markdown("##### 💰 Mutual Funds")
                                        mf_df = period_df[['Afore', 'mutual_funds_current', 'mutual_funds_absolute_change', 'mutual_funds_growth_rate']].copy()
                                        mf_df.columns = ['Afore', 'Current (USD)', 'Change (USD)', 'Growth %']
                                        
                                        # Format columns
                                        mf_df['Current (USD)'] = mf_df['Current (USD)'].apply(lambda x: f"${x/1e6:,.0f}M" if x > 0 else "$0")
                                        mf_df['Change (USD)'] = mf_df['Change (USD)'].apply(lambda x: f"${x/1e6:+,.0f}M" if abs(x) > 0 else "$0")
                                        mf_df['Growth %'] = mf_df['Growth %'].apply(lambda x: "NEW" if x == float('inf') else f"{x:+.1f}%" if pd.notna(x) else "0.0%")
                                        
                                        # Sort by growth rate and show all Afores
                                        # Sort by original numeric growth rate from period_df
                                        period_df_mf = period_df.sort_values('mutual_funds_growth_rate', ascending=False)
                                        mf_df_sorted = mf_df.loc[period_df_mf.index]
                                        
                                        # Add industry total row
                                        total_mf_current = period_df['mutual_funds_current'].sum()
                                        total_mf_change = period_df['mutual_funds_absolute_change'].sum()
                                        total_mf_growth = ((total_mf_current - (total_mf_current - total_mf_change)) / (total_mf_current - total_mf_change) * 100) if (total_mf_current - total_mf_change) > 0 else 0
                                        
                                        industry_row_mf = pd.DataFrame({
                                            'Afore': ['**INDUSTRY TOTAL**'],
                                            'Current (USD)': [f"${total_mf_current/1e6:,.0f}M"],
                                            'Change (USD)': [f"${total_mf_change/1e6:+,.0f}M" if abs(total_mf_change) > 0 else "$0"],
                                            'Growth %': [f"{total_mf_growth:+.1f}%" if total_mf_growth != 0 else "0.0%"]
                                        })
                                        
                                        mf_df_with_total = pd.concat([mf_df_sorted, industry_row_mf], ignore_index=True)
                                        st.dataframe(mf_df_with_total, use_container_width=True, hide_index=True)
                                        
                                        # 2. Third Party Mandates Table  
                                        st.markdown("##### 🤝 Third Party Mandates")
                                        tp_df = period_df[['Afore', 'third_party_current', 'third_party_absolute_change', 'third_party_growth_rate']].copy()
                                        tp_df.columns = ['Afore', 'Current (USD)', 'Change (USD)', 'Growth %']
                                        
                                        # Format columns
                                        tp_df['Current (USD)'] = tp_df['Current (USD)'].apply(lambda x: f"${x/1e6:,.0f}M" if x > 0 else "$0")
                                        tp_df['Change (USD)'] = tp_df['Change (USD)'].apply(lambda x: f"${x/1e6:+,.0f}M" if abs(x) > 0 else "$0")
                                        tp_df['Growth %'] = tp_df['Growth %'].apply(lambda x: "NEW" if x == float('inf') else f"{x:+.1f}%" if pd.notna(x) else "0.0%")
                                        
                                        # Sort by growth rate and show all Afores
                                        # Sort by original numeric growth rate from period_df
                                        period_df_tp = period_df.sort_values('third_party_growth_rate', ascending=False)
                                        tp_df_sorted = tp_df.loc[period_df_tp.index]
                                        
                                        # Add industry total row
                                        total_tp_current = period_df['third_party_current'].sum()
                                        total_tp_change = period_df['third_party_absolute_change'].sum()
                                        total_tp_growth = ((total_tp_current - (total_tp_current - total_tp_change)) / (total_tp_current - total_tp_change) * 100) if (total_tp_current - total_tp_change) > 0 else 0
                                        
                                        industry_row_tp = pd.DataFrame({
                                            'Afore': ['**INDUSTRY TOTAL**'],
                                            'Current (USD)': [f"${total_tp_current/1e6:,.0f}M"],
                                            'Change (USD)': [f"${total_tp_change/1e6:+,.0f}M" if abs(total_tp_change) > 0 else "$0"],
                                            'Growth %': [f"{total_tp_growth:+.1f}%" if total_tp_growth != 0 else "0.0%"]
                                        })
                                        
                                        tp_df_with_total = pd.concat([tp_df_sorted, industry_row_tp], ignore_index=True)
                                        st.dataframe(tp_df_with_total, use_container_width=True, hide_index=True)
                                        
                                        # 3. Total Active Management Table
                                        st.markdown("##### 📊 Total Active Management")
                                        total_df = period_df[['Afore', 'total_active_current', 'total_active_absolute_change', 'total_active_growth_rate']].copy()
                                        total_df.columns = ['Afore', 'Current (USD)', 'Change (USD)', 'Growth %']
                                        
                                        # Format columns
                                        total_df['Current (USD)'] = total_df['Current (USD)'].apply(lambda x: f"${x/1e6:,.0f}M" if x > 0 else "$0")
                                        total_df['Change (USD)'] = total_df['Change (USD)'].apply(lambda x: f"${x/1e6:+,.0f}M" if abs(x) > 0 else "$0")
                                        total_df['Growth %'] = total_df['Growth %'].apply(lambda x: "NEW" if x == float('inf') else f"{x:+.1f}%" if pd.notna(x) else "0.0%")
                                        
                                        # Sort by growth rate and show all Afores
                                        # Sort by original numeric growth rate from period_df
                                        period_df_total = period_df.sort_values('total_active_growth_rate', ascending=False)
                                        total_df_sorted = total_df.loc[period_df_total.index]
                                        
                                        # Add industry total row
                                        total_active_current = period_df['total_active_current'].sum()
                                        total_active_change = period_df['total_active_absolute_change'].sum()
                                        total_active_growth = ((total_active_current - (total_active_current - total_active_change)) / (total_active_current - total_active_change) * 100) if (total_active_current - total_active_change) > 0 else 0
                                        
                                        industry_row_total = pd.DataFrame({
                                            'Afore': ['**INDUSTRY TOTAL**'],
                                            'Current (USD)': [f"${total_active_current/1e6:,.0f}M"],
                                            'Change (USD)': [f"${total_active_change/1e6:+,.0f}M" if abs(total_active_change) > 0 else "$0"],
                                            'Growth %': [f"{total_active_growth:+.1f}%" if total_active_growth != 0 else "0.0%"]
                                        })
                                        
                                        total_df_with_total = pd.concat([total_df_sorted, industry_row_total], ignore_index=True)
                                        st.dataframe(total_df_with_total, use_container_width=True, hide_index=True)
                                        
                                        # Download option for this period
                                        st.markdown("**Download:**")
                                        csv_data = period_df.to_csv(index=False)
                                        st.download_button(
                                            f"📥 Download {period} Growth Data (CSV)",
                                            csv_data,
                                            f"growth_analysis_{period}_{current_period.replace('-', '_')}.csv",
                                            "text/csv"
                                        )
                            
                            # Overall download
                            st.markdown("### 📥 Complete Growth Analysis")
                            csv_data_all = growth_df.to_csv(index=False)
                            st.download_button(
                                "📥 Download Complete Growth Analysis (CSV)",
                                csv_data_all,
                                f"complete_growth_analysis_{current_period.replace('-', '_')}.csv",
                                "text/csv"
                            )
                        
                        else:
                            st.error("No growth data could be calculated.")
                            
                    except Exception as e:
                        st.error(f"Error in growth analysis: {str(e)}")
                        st.exception(e)
            
            else:
                # Current Period Analysis (existing code)
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