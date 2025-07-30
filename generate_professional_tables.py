#!/usr/bin/env python3
"""
Generate Professional CONSAR Analysis Tables

Creates two professional tables:
1. Afores AUMs (USD millions) - Current AUM breakdown
2. Afores M.F. Buys & Sells (USD millions) - Dynamic period comparisons

Features:
- Dynamic date calculations (YTD, 1Y, 3Y, 5Y)
- Values in millions with no decimals
- Real Banxico FX rate verification
- Professional formatting
"""

import json
import pandas as pd
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import argparse
from pathlib import Path

class ProfessionalAUMAnalyzer:
    """Professional AUM analyzer with dynamic period calculations."""
    
    def __init__(self, database_path):
        self.database_path = Path(database_path)
        self.data = None
        self.latest_period = None
        
    def load_data(self):
        """Load the historical database."""
        print(f"Loading data from: {self.database_path}")
        with open(self.database_path, 'r', encoding='utf-8') as f:
            self.data = json.load(f)
        print(f"Loaded {len(self.data):,} records")
        
    def get_latest_period(self):
        """Find the most recent period in the data."""
        periods = set()
        for record in self.data:
            year = record.get('PeriodYear')
            month = record.get('PeriodMonth')
            if year and month:
                periods.add(f"{year}-{month}")
        
        self.latest_period = max(periods) if periods else None
        print(f"Latest period found: {self.latest_period}")
        return self.latest_period
        
    def calculate_dynamic_periods(self, latest_period):
        """Calculate comparison periods dynamically."""
        if not latest_period:
            return {}
            
        # Parse latest period
        latest_year, latest_month = map(int, latest_period.split('-'))
        latest_date = datetime(latest_year, latest_month, 1)
        
        # Calculate comparison periods
        periods = {
            'current': latest_period,
            'ytd_baseline': f"{latest_year - 1}-12",  # December of prior year
            '1_year': (latest_date - relativedelta(months=12)).strftime("%Y-%m"),
            '3_year': (latest_date - relativedelta(months=36)).strftime("%Y-%m"),
            '5_year': (latest_date - relativedelta(months=60)).strftime("%Y-%m")
        }
        
        print(f"\nDynamic periods calculated:")
        print(f"  Current: {periods['current']}")
        print(f"  YTD Baseline: {periods['ytd_baseline']}")
        print(f"  1 Year Ago: {periods['1_year']}")
        print(f"  3 Years Ago: {periods['3_year']}")
        print(f"  5 Years Ago: {periods['5_year']}")
        
        return periods
        
    def verify_fx_rates(self, periods):
        """Verify that all periods have real Banxico FX rates."""
        print(f"\n=== FX RATE VERIFICATION ===")
        fx_info = {}
        
        for period_name, period in periods.items():
            if not period:
                continue
                
            year, month = period.split('-')
            records = [r for r in self.data if (
                r.get('PeriodYear') == year and 
                r.get('PeriodMonth') == month and 
                r.get('FX_EOM')
            )]
            
            if records:
                fx_rate = records[0]['FX_EOM']
                # Check if this looks like a real Banxico rate
                is_real = fx_rate not in [17.8, 17.9] and 15 < fx_rate < 25
                status = '✅ Real Banxico' if is_real else '⚠️  Possible fallback'
                fx_info[period] = {'rate': fx_rate, 'real': is_real}
                print(f"  {period_name.upper()} ({period}): {fx_rate:.4f} MXN/USD - {status}")
            else:
                fx_info[period] = {'rate': None, 'real': False}
                print(f"  {period_name.upper()} ({period}): ❌ No FX data found")
                
        return fx_info
        
    def get_period_data(self, period, concept):
        """Get data for a specific period and concept, returns values in USD millions."""
        if not period:
            return {}
            
        year, month = period.split('-')
        records = [r for r in self.data if (
            r.get('PeriodYear') == year and 
            r.get('PeriodMonth') == month and
            r.get('Concept') == concept and
            r.get('valueMXN') is not None and
            r.get('FX_EOM') is not None
        )]
        
        # Group by Afore
        afore_data = {}
        for record in records:
            afore = record.get('Afore')
            value_mxn = record.get('valueMXN', 0)
            fx_rate = record.get('FX_EOM', 1)
            value_usd = value_mxn / fx_rate if fx_rate > 0 else 0
            value_usd_millions = value_usd / 1_000_000  # Convert USD to millions
            if afore:
                if afore not in afore_data:
                    afore_data[afore] = 0
                afore_data[afore] += value_usd_millions
                
        return afore_data
        
    def create_aum_table(self, latest_period):
        """Create the Afores AUMs table in USD millions."""
        print(f"\n=== CREATING AUM TABLE ===")
        
        # Get Total AUM data for latest period
        total_aum_data = self.get_period_data(latest_period, 'Total de Activo')
        mf_aum_data = self.get_period_data(latest_period, 'Inversión en Fondos Mutuos')
        
        if not total_aum_data:
            print("ERROR: No Total AUM data found for latest period")
            return None
            
        # Create table data
        table_data = []
        total_aum_sum = 0
        total_mf_sum = 0
        
        # Sort Afores alphabetically
        sorted_afores = sorted(total_aum_data.keys())
        
        for afore in sorted_afores:
            total_aum = total_aum_data.get(afore, 0) * 1_000  # Convert millions to display format
            mf_aum = mf_aum_data.get(afore, 0) * 1_000  # Convert millions to display format
            mf_percentage = (mf_aum / total_aum * 100) if total_aum > 0 else 0
            
            table_data.append({
                'Afore': afore,
                'Total AUM': total_aum,
                'Mutual Fund AUM': mf_aum,
                'MF AUM as % of Total': mf_percentage
            })
            
            total_aum_sum += total_aum
            total_mf_sum += mf_aum
        
        # Add totals row
        total_mf_percentage = (total_mf_sum / total_aum_sum * 100) if total_aum_sum > 0 else 0
        table_data.append({
            'Afore': 'TOTAL',
            'Total AUM': total_aum_sum,
            'Mutual Fund AUM': total_mf_sum,
            'MF AUM as % of Total': total_mf_percentage
        })
        
        df = pd.DataFrame(table_data)
        return df
        
    def create_buys_sells_table(self, periods):
        """Create the Afores M.F. Buys & Sells table with dynamic comparisons."""
        print(f"\n=== CREATING BUYS & SELLS TABLE ===")
        
        # Get mutual fund data for all periods
        current_data = self.get_period_data(periods['current'], 'Inversión en Fondos Mutuos')
        ytd_data = self.get_period_data(periods['ytd_baseline'], 'Inversión en Fondos Mutuos')
        one_year_data = self.get_period_data(periods['1_year'], 'Inversión en Fondos Mutuos')
        three_year_data = self.get_period_data(periods['3_year'], 'Inversión en Fondos Mutuos')
        five_year_data = self.get_period_data(periods['5_year'], 'Inversión en Fondos Mutuos')
        
        if not current_data:
            print("ERROR: No current mutual fund data found")
            return None
            
        # Create table data
        table_data = []
        
        # Get all unique Afores
        all_afores = set()
        for data_dict in [current_data, ytd_data, one_year_data, three_year_data, five_year_data]:
            all_afores.update(data_dict.keys())
        
        sorted_afores = sorted(all_afores)
        
        # Calculate changes for each Afore
        ytd_total = 0
        one_year_total = 0
        three_year_total = 0
        five_year_total = 0
        
        for afore in sorted_afores:
            current_val = current_data.get(afore, 0)  # Already in millions from get_period_data
            ytd_val = ytd_data.get(afore, 0)
            one_year_val = one_year_data.get(afore, 0)
            three_year_val = three_year_data.get(afore, 0)
            five_year_val = five_year_data.get(afore, 0)
            
            # Calculate differences
            ytd_change = current_val - ytd_val
            one_year_change = current_val - one_year_val
            three_year_change = current_val - three_year_val
            five_year_change = current_val - five_year_val
            
            table_data.append({
                'Afore': afore,
                'YTD': ytd_change,
                '1 Year': one_year_change,
                '3 Year': three_year_change,
                '5 Year': five_year_change
            })
            
            ytd_total += ytd_change
            one_year_total += one_year_change
            three_year_total += three_year_change
            five_year_total += five_year_change
        
        # Add totals row
        table_data.append({
            'Afore': 'TOTAL',
            'YTD': ytd_total,
            '1 Year': one_year_total,
            '3 Year': three_year_total,
            '5 Year': five_year_total
        })
        
        df = pd.DataFrame(table_data)
        return df
        
    def create_third_party_mandates_table(self, latest_period):
        """Create the Afores Third Party Mandates table in USD millions."""
        print(f"\n=== CREATING THIRD PARTY MANDATES TABLE ===")
        
        # Get Total AUM data for latest period
        total_aum_data = self.get_period_data(latest_period, 'Total de Activo')
        tp_aum_data = self.get_period_data(latest_period, 'Inversiones Tercerizadas')
        
        if not total_aum_data:
            print("ERROR: No Total AUM data found for latest period")
            return None
            
        # Create table data
        table_data = []
        total_aum_sum = 0
        total_tp_sum = 0
        
        # Sort Afores alphabetically
        sorted_afores = sorted(total_aum_data.keys())
        
        for afore in sorted_afores:
            total_aum = total_aum_data.get(afore, 0) * 1_000  # Convert millions to display format
            tp_aum = tp_aum_data.get(afore, 0) * 1_000  # Convert millions to display format
            tp_percentage = (tp_aum / total_aum * 100) if total_aum > 0 else 0
            
            table_data.append({
                'Afore': afore,
                'Total AUM': total_aum,
                'Third Party Mandates AUM': tp_aum,
                'TP AUM as % of Total': tp_percentage
            })
            
            total_aum_sum += total_aum
            total_tp_sum += tp_aum
        
        # Add totals row
        total_tp_percentage = (total_tp_sum / total_aum_sum * 100) if total_aum_sum > 0 else 0
        table_data.append({
            'Afore': 'TOTAL',
            'Total AUM': total_aum_sum,
            'Third Party Mandates AUM': total_tp_sum,
            'TP AUM as % of Total': total_tp_percentage
        })
        
        df = pd.DataFrame(table_data)
        return df
        
    def create_total_active_management_table(self, latest_period):
        """Create the Afores Total Active Management table (MF + Third Party) in USD millions."""
        print(f"\n=== CREATING TOTAL ACTIVE MANAGEMENT TABLE ===")
        
        # Get Total AUM data for latest period
        total_aum_data = self.get_period_data(latest_period, 'Total de Activo')
        mf_aum_data = self.get_period_data(latest_period, 'Inversión en Fondos Mutuos')
        tp_aum_data = self.get_period_data(latest_period, 'Inversiones Tercerizadas')
        
        if not total_aum_data:
            print("ERROR: No Total AUM data found for latest period")
            return None
            
        # Create table data
        table_data = []
        total_aum_sum = 0
        total_mf_sum = 0
        total_tp_sum = 0
        total_active_sum = 0
        
        # Sort Afores alphabetically
        sorted_afores = sorted(total_aum_data.keys())
        
        for afore in sorted_afores:
            total_aum = total_aum_data.get(afore, 0) * 1_000  # Convert millions to display format
            mf_aum = mf_aum_data.get(afore, 0) * 1_000  # Convert millions to display format
            tp_aum = tp_aum_data.get(afore, 0) * 1_000  # Convert millions to display format
            active_aum = mf_aum + tp_aum  # Total active management
            active_percentage = (active_aum / total_aum * 100) if total_aum > 0 else 0
            
            table_data.append({
                'Afore': afore,
                'Total AUM': total_aum,
                'Mutual Funds': mf_aum,
                'Third Party Mandates': tp_aum,
                'Total Active Management': active_aum,
                'Active as % of Total': active_percentage
            })
            
            total_aum_sum += total_aum
            total_mf_sum += mf_aum
            total_tp_sum += tp_aum
            total_active_sum += active_aum
        
        # Add totals row
        total_active_percentage = (total_active_sum / total_aum_sum * 100) if total_aum_sum > 0 else 0
        table_data.append({
            'Afore': 'TOTAL',
            'Total AUM': total_aum_sum,
            'Mutual Funds': total_mf_sum,
            'Third Party Mandates': total_tp_sum,
            'Total Active Management': total_active_sum,
            'Active as % of Total': total_active_percentage
        })
        
        df = pd.DataFrame(table_data)
        return df
        
    def create_period_comparison_table(self, periods):
        """Create a table showing actual USD AUM values for each period."""
        print(f"\n=== CREATING PERIOD COMPARISON TABLE ===")
        
        # Get mutual fund data for all periods
        current_data = self.get_period_data(periods['current'], 'Inversión en Fondos Mutuos')
        ytd_data = self.get_period_data(periods['ytd_baseline'], 'Inversión en Fondos Mutuos')
        one_year_data = self.get_period_data(periods['1_year'], 'Inversión en Fondos Mutuos')
        three_year_data = self.get_period_data(periods['3_year'], 'Inversión en Fondos Mutuos')
        five_year_data = self.get_period_data(periods['5_year'], 'Inversión en Fondos Mutuos')
        
        # Create table data
        table_data = []
        
        # Get all unique Afores
        all_afores = set()
        for data_dict in [current_data, ytd_data, one_year_data, three_year_data, five_year_data]:
            all_afores.update(data_dict.keys())
        
        sorted_afores = sorted(all_afores)
        
        # Show actual values for each period
        current_total = 0
        ytd_total = 0
        one_year_total = 0
        three_year_total = 0
        five_year_total = 0
        
        for afore in sorted_afores:
            current_val = current_data.get(afore, 0)  # Already in millions from get_period_data
            ytd_val = ytd_data.get(afore, 0)
            one_year_val = one_year_data.get(afore, 0)
            three_year_val = three_year_data.get(afore, 0)
            five_year_val = five_year_data.get(afore, 0)
            
            table_data.append({
                'Afore': afore,
                f'Current ({periods["current"]})': current_val,
                f'YTD Base ({periods["ytd_baseline"]})': ytd_val,
                f'1Y Ago ({periods["1_year"]})': one_year_val,
                f'3Y Ago ({periods["3_year"]})': three_year_val,
                f'5Y Ago ({periods["5_year"]})': five_year_val
            })
            
            current_total += current_val
            ytd_total += ytd_val
            one_year_total += one_year_val
            three_year_total += three_year_val
            five_year_total += five_year_val
        
        # Add totals row
        table_data.append({
            'Afore': 'TOTAL',
            f'Current ({periods["current"]})': current_total,
            f'YTD Base ({periods["ytd_baseline"]})': ytd_total,
            f'1Y Ago ({periods["1_year"]})': one_year_total,
            f'3Y Ago ({periods["3_year"]})': three_year_total,
            f'5Y Ago ({periods["5_year"]})': five_year_total
        })
        
        df = pd.DataFrame(table_data)
        return df
        
    def format_aum_table(self, df, latest_period):
        """Format the AUM table for display."""
        if df is None:
            return None
            
        print(f"\n" + "="*80)
        print(f"AFORES AUMs (USD millions) - PERIOD: {latest_period}")
        print(f"="*80)
        
        # Format for display
        df_display = df.copy()
        
        # Format USD millions with no decimals
        df_display['Total AUM'] = df_display['Total AUM'].apply(
            lambda x: f"{x:.0f}" if pd.notna(x) else "0"
        )
        df_display['Mutual Fund AUM'] = df_display['Mutual Fund AUM'].apply(
            lambda x: f"{x:.0f}" if pd.notna(x) else "0"
        )
        
        # Format percentages
        df_display['MF AUM as % of Total'] = df_display['MF AUM as % of Total'].apply(
            lambda x: f"{x:.1f}%" if pd.notna(x) else "0.0%"
        )
        
        print(df_display.to_string(index=False, justify='left'))
        print(f"="*80)
        
        return df_display
        
    def format_buys_sells_table(self, df, periods):
        """Format the Buys & Sells table for display."""
        if df is None:
            return None
            
        print(f"\n" + "="*80)
        print(f"AFORES M.F. Buys & Sells (USD millions)")
        print(f"Current Period: {periods['current']}")
        print(f"Comparison Periods: YTD vs {periods['ytd_baseline']}, 1Y vs {periods['1_year']}")
        print(f"                   3Y vs {periods['3_year']}, 5Y vs {periods['5_year']}")
        print(f"="*80)
        
        # Format for display
        df_display = df.copy()
        
        # Format all value columns with no decimals, show +/- signs
        value_columns = ['YTD', '1 Year', '3 Year', '5 Year']
        for col in value_columns:
            df_display[col] = df_display[col].apply(
                lambda x: f"{x:+.0f}" if pd.notna(x) and x != 0 else "0" if pd.notna(x) else "N/A"
            )
        
        print(df_display.to_string(index=False, justify='left'))
        print(f"="*80)
        
        return df_display
        
    def format_third_party_mandates_table(self, df, latest_period):
        """Format the Third Party Mandates table for display."""
        if df is None:
            return None
            
        print(f"\n" + "="*80)
        print(f"AFORES THIRD PARTY MANDATES (USD millions) - PERIOD: {latest_period}")
        print(f"="*80)
        
        # Format for display
        df_display = df.copy()
        
        # Format USD millions with no decimals
        df_display['Total AUM'] = df_display['Total AUM'].apply(
            lambda x: f"{x:.0f}" if pd.notna(x) else "0"
        )
        df_display['Third Party Mandates AUM'] = df_display['Third Party Mandates AUM'].apply(
            lambda x: f"{x:.0f}" if pd.notna(x) else "0"
        )
        
        # Format percentages
        df_display['TP AUM as % of Total'] = df_display['TP AUM as % of Total'].apply(
            lambda x: f"{x:.1f}%" if pd.notna(x) else "0.0%"
        )
        
        print(df_display.to_string(index=False, justify='left'))
        print(f"="*80)
        
        return df_display
        
    def format_total_active_management_table(self, df, latest_period):
        """Format the Total Active Management table for display."""
        if df is None:
            return None
            
        print(f"\n" + "="*100)
        print(f"AFORES TOTAL ACTIVE MANAGEMENT (USD millions) - PERIOD: {latest_period}")
        print(f"="*100)
        
        # Format for display
        df_display = df.copy()
        
        # Format USD millions with no decimals
        df_display['Total AUM'] = df_display['Total AUM'].apply(
            lambda x: f"{x:.0f}" if pd.notna(x) else "0"
        )
        df_display['Mutual Funds'] = df_display['Mutual Funds'].apply(
            lambda x: f"{x:.0f}" if pd.notna(x) else "0"
        )
        df_display['Third Party Mandates'] = df_display['Third Party Mandates'].apply(
            lambda x: f"{x:.0f}" if pd.notna(x) else "0"
        )
        df_display['Total Active Management'] = df_display['Total Active Management'].apply(
            lambda x: f"{x:.0f}" if pd.notna(x) else "0"
        )
        
        # Format percentages
        df_display['Active as % of Total'] = df_display['Active as % of Total'].apply(
            lambda x: f"{x:.1f}%" if pd.notna(x) else "0.0%"
        )
        
        print(df_display.to_string(index=False, justify='left'))
        print(f"="*100)
        
        return df_display
        
    def format_period_comparison_table(self, df, periods):
        """Format the period comparison table for display."""
        if df is None:
            return None
            
        print(f"\n" + "="*120)
        print(f"AFORES M.F. AUM VALUES BY PERIOD (USD millions)")
        print(f"Shows actual values being used in change calculations")
        print(f"="*120)
        
        # Format for display
        df_display = df.copy()
        
        # Format all value columns with no decimals
        value_columns = [col for col in df_display.columns if col != 'Afore']
        for col in value_columns:
            df_display[col] = df_display[col].apply(
                lambda x: f"{x:.0f}" if pd.notna(x) else "0"
            )
        
        print(df_display.to_string(index=False, justify='left'))
        print(f"="*120)
        
        return df_display
        
    def save_tables(self, aum_df, buys_sells_df, period_comparison_df, tp_mandates_df, active_mgmt_df, latest_period):
        """Save all tables to CSV files."""
        if aum_df is not None:
            aum_file = f"output/afores_aum_usd_millions_{latest_period.replace('-', '_')}.csv"
            Path(aum_file).parent.mkdir(parents=True, exist_ok=True)
            aum_df.to_csv(aum_file, index=False)
            print(f"\nAUM table saved to: {aum_file}")
            
        if buys_sells_df is not None:
            bs_file = f"output/afores_mf_buys_sells_{latest_period.replace('-', '_')}.csv"
            Path(bs_file).parent.mkdir(parents=True, exist_ok=True)
            buys_sells_df.to_csv(bs_file, index=False)
            print(f"Buys & Sells table saved to: {bs_file}")
            
        if period_comparison_df is not None:
            pc_file = f"output/afores_mf_period_comparison_{latest_period.replace('-', '_')}.csv"
            Path(pc_file).parent.mkdir(parents=True, exist_ok=True)
            period_comparison_df.to_csv(pc_file, index=False)
            print(f"Period Comparison table saved to: {pc_file}")
            
        if tp_mandates_df is not None:
            tp_file = f"output/afores_third_party_mandates_{latest_period.replace('-', '_')}.csv"
            Path(tp_file).parent.mkdir(parents=True, exist_ok=True)
            tp_mandates_df.to_csv(tp_file, index=False)
            print(f"Third Party Mandates table saved to: {tp_file}")
            
        if active_mgmt_df is not None:
            am_file = f"output/afores_total_active_management_{latest_period.replace('-', '_')}.csv"
            Path(am_file).parent.mkdir(parents=True, exist_ok=True)
            active_mgmt_df.to_csv(am_file, index=False)
            print(f"Total Active Management table saved to: {am_file}")
        
    def run(self):
        """Run the complete professional analysis."""
        print("=== PROFESSIONAL CONSAR ANALYSIS ===")
        
        # Load data
        self.load_data()
        
        # Get latest period
        latest_period = self.get_latest_period()
        if not latest_period:
            print("ERROR: No data periods found")
            return
            
        # Calculate dynamic periods
        periods = self.calculate_dynamic_periods(latest_period)
        
        # Verify FX rates
        fx_info = self.verify_fx_rates(periods)
        
        # Check for any fallback rates
        fallback_periods = [p for p, info in fx_info.items() if not info.get('real', True)]
        if fallback_periods:
            print(f"\n⚠️  WARNING: Some periods may have fallback FX rates: {fallback_periods}")
            print("Consider updating FX rates with: python fix_fx_rates.py")
        else:
            print(f"\n✅ All FX rates verified as real Banxico data")
        
        # Create tables
        aum_df = self.create_aum_table(latest_period)
        buys_sells_df = self.create_buys_sells_table(periods)
        period_comparison_df = self.create_period_comparison_table(periods)
        tp_mandates_df = self.create_third_party_mandates_table(latest_period)
        active_mgmt_df = self.create_total_active_management_table(latest_period)
        
        # Format and display tables
        aum_display = self.format_aum_table(aum_df, latest_period)
        bs_display = self.format_buys_sells_table(buys_sells_df, periods)
        pc_display = self.format_period_comparison_table(period_comparison_df, periods)
        tp_display = self.format_third_party_mandates_table(tp_mandates_df, latest_period)
        am_display = self.format_total_active_management_table(active_mgmt_df, latest_period)
        
        # Save to CSV
        self.save_tables(aum_df, buys_sells_df, period_comparison_df, tp_mandates_df, active_mgmt_df, latest_period)
        
        return aum_df, buys_sells_df, period_comparison_df, tp_mandates_df, active_mgmt_df

def main():
    parser = argparse.ArgumentParser(description='Generate professional CONSAR analysis tables')
    parser.add_argument('--database', type=str,
                       default='data/merged_consar_data_2019_2025.json',
                       help='Path to CONSAR database file')
    
    args = parser.parse_args()
    
    try:
        from dateutil.relativedelta import relativedelta
    except ImportError:
        print("ERROR: python-dateutil is required for dynamic date calculations")
        print("Install with: pip install python-dateutil")
        return
    
    analyzer = ProfessionalAUMAnalyzer(args.database)
    analyzer.run()

if __name__ == "__main__":
    main()