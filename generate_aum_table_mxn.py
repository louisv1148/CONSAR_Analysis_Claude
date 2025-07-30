#!/usr/bin/env python3
"""
Generate AUM Analysis Table with MXN Values

Creates tables with:
- Afores in alphabetical order (+ Total row)
- Total AUM (MXN & USD)
- Mutual Fund AUM (MXN & USD)  
- Mutual Fund AUM as % of Total AUM
- FX rate information
"""

import json
import pandas as pd
from datetime import datetime
import argparse
from pathlib import Path

class AUMAnalyzerMXN:
    """Analyzes AUM data from CONSAR database with MXN support."""
    
    def __init__(self, database_path, output_period=None):
        self.database_path = Path(database_path)
        self.output_period = output_period  # Format: "2025-06" or None for latest
        
    def load_data(self):
        """Load the historical database."""
        print(f"Loading data from: {self.database_path}")
        with open(self.database_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        print(f"Loaded {len(data):,} records")
        return data
        
    def get_latest_period(self, data):
        """Find the most recent period in the data."""
        periods = set()
        for record in data:
            year = record.get('PeriodYear')
            month = record.get('PeriodMonth')
            if year and month:
                periods.add(f"{year}-{month}")
        
        latest = max(periods) if periods else None
        print(f"Latest period found: {latest}")
        return latest
        
    def filter_data_for_period(self, data, target_period):
        """Filter data for a specific period."""
        if not target_period:
            target_period = self.get_latest_period(data)
            
        year, month = target_period.split('-')
        
        filtered_data = [
            record for record in data 
            if (record.get('PeriodYear') == year and 
                record.get('PeriodMonth') == month and
                record.get('valueMXN') is not None)
        ]
        
        print(f"Filtered to {len(filtered_data)} records for period {target_period}")
        return filtered_data, target_period
        
    def get_fx_rate(self, data):
        """Get the FX rate used for this period."""
        fx_rates = [record.get('FX_EOM') for record in data if record.get('FX_EOM')]
        if fx_rates:
            # All records should have the same FX rate for a given period
            fx_rate = fx_rates[0]
            print(f"FX Rate for period: {fx_rate} MXN/USD")
            return fx_rate
        return None
        
    def calculate_aum_by_afore(self, data):
        """Calculate total AUM and mutual fund AUM by Afore in both currencies."""
        aum_data = {}
        
        for record in data:
            afore = record.get('Afore')
            concept = record.get('Concept')
            value_mxn = record.get('valueMXN', 0)
            value_usd = record.get('valueUSD', 0)
            
            if not afore or value_mxn is None:
                continue
                
            if afore not in aum_data:
                aum_data[afore] = {
                    'total_aum_mxn': 0,
                    'total_aum_usd': 0,
                    'mutual_fund_aum_mxn': 0,
                    'mutual_fund_aum_usd': 0
                }
            
            # Total AUM includes "Total de Activo" concept
            if concept == 'Total de Activo':
                aum_data[afore]['total_aum_mxn'] += value_mxn
                aum_data[afore]['total_aum_usd'] += (value_usd or 0)
                
            # Mutual Fund AUM includes "Inversión en Fondos Mutuos" concept
            elif concept == 'Inversión en Fondos Mutuos':
                aum_data[afore]['mutual_fund_aum_mxn'] += value_mxn
                aum_data[afore]['mutual_fund_aum_usd'] += (value_usd or 0)
        
        return aum_data
        
    def create_summary_table_mxn(self, aum_data, period, fx_rate):
        """Create the summary table with MXN values."""
        
        # Prepare data for DataFrame
        table_data = []
        total_aum_mxn_sum = 0
        total_mf_mxn_sum = 0
        
        # Sort Afores alphabetically
        sorted_afores = sorted(aum_data.keys())
        
        for afore in sorted_afores:
            data = aum_data[afore]
            total_aum_mxn = data['total_aum_mxn']
            mf_aum_mxn = data['mutual_fund_aum_mxn']
            mf_percentage = (mf_aum_mxn / total_aum_mxn * 100) if total_aum_mxn > 0 else 0
            
            table_data.append({
                'Afore': afore,
                'Total AUM (MXN)': total_aum_mxn,
                'Mutual Fund AUM (MXN)': mf_aum_mxn,
                'MF AUM as % of Total': mf_percentage
            })
            
            total_aum_mxn_sum += total_aum_mxn
            total_mf_mxn_sum += mf_aum_mxn
        
        # Add totals row
        total_mf_percentage = (total_mf_mxn_sum / total_aum_mxn_sum * 100) if total_aum_mxn_sum > 0 else 0
        table_data.append({
            'Afore': 'TOTAL',
            'Total AUM (MXN)': total_aum_mxn_sum,
            'Mutual Fund AUM (MXN)': total_mf_mxn_sum,
            'MF AUM as % of Total': total_mf_percentage
        })
        
        # Create DataFrame
        df = pd.DataFrame(table_data)
        
        return df
        
    def create_summary_table_combined(self, aum_data, period, fx_rate):
        """Create the summary table with both MXN and USD values."""
        
        # Prepare data for DataFrame
        table_data = []
        total_aum_mxn_sum = 0
        total_aum_usd_sum = 0
        total_mf_mxn_sum = 0
        total_mf_usd_sum = 0
        
        # Sort Afores alphabetically
        sorted_afores = sorted(aum_data.keys())
        
        for afore in sorted_afores:
            data = aum_data[afore]
            total_aum_mxn = data['total_aum_mxn']
            total_aum_usd = data['total_aum_usd']
            mf_aum_mxn = data['mutual_fund_aum_mxn']
            mf_aum_usd = data['mutual_fund_aum_usd']
            mf_percentage = (mf_aum_mxn / total_aum_mxn * 100) if total_aum_mxn > 0 else 0
            
            table_data.append({
                'Afore': afore,
                'Total AUM (MXN)': total_aum_mxn,
                'Total AUM (USD)': total_aum_usd,
                'Mutual Fund AUM (MXN)': mf_aum_mxn,
                'Mutual Fund AUM (USD)': mf_aum_usd,
                'MF AUM as % of Total': mf_percentage
            })
            
            total_aum_mxn_sum += total_aum_mxn
            total_aum_usd_sum += total_aum_usd
            total_mf_mxn_sum += mf_aum_mxn
            total_mf_usd_sum += mf_aum_usd
        
        # Add totals row
        total_mf_percentage = (total_mf_mxn_sum / total_aum_mxn_sum * 100) if total_aum_mxn_sum > 0 else 0
        table_data.append({
            'Afore': 'TOTAL',
            'Total AUM (MXN)': total_aum_mxn_sum,
            'Total AUM (USD)': total_aum_usd_sum,
            'Mutual Fund AUM (MXN)': total_mf_mxn_sum,
            'Mutual Fund AUM (USD)': total_mf_usd_sum,
            'MF AUM as % of Total': total_mf_percentage
        })
        
        # Create DataFrame
        df = pd.DataFrame(table_data)
        
        return df
        
    def format_table_mxn(self, df, period, fx_rate):
        """Format the MXN table for display."""
        print(f"\n" + "="*80)
        print(f"CONSAR AUM ANALYSIS (MXN) - PERIOD: {period}")
        print(f"FX RATE: {fx_rate} MXN/USD")
        print(f"="*80)
        
        # Format numbers for display
        df_display = df.copy()
        
        # Format MXN amounts with commas and no decimals
        df_display['Total AUM (MXN)'] = df_display['Total AUM (MXN)'].apply(
            lambda x: f"${x:,.0f}" if pd.notna(x) else "$0"
        )
        df_display['Mutual Fund AUM (MXN)'] = df_display['Mutual Fund AUM (MXN)'].apply(
            lambda x: f"${x:,.0f}" if pd.notna(x) else "$0"
        )
        
        # Format percentages with 2 decimal places
        df_display['MF AUM as % of Total'] = df_display['MF AUM as % of Total'].apply(
            lambda x: f"{x:.2f}%" if pd.notna(x) else "0.00%"
        )
        
        # Print table
        print(df_display.to_string(index=False, justify='left'))
        print(f"="*80)
        
        return df_display
        
    def format_table_combined(self, df, period, fx_rate):
        """Format the combined table for display."""
        print(f"\n" + "="*120)
        print(f"CONSAR AUM ANALYSIS (MXN & USD) - PERIOD: {period}")
        print(f"FX RATE: {fx_rate} MXN/USD")
        print(f"="*120)
        
        # Format numbers for display
        df_display = df.copy()
        
        # Format MXN amounts
        df_display['Total AUM (MXN)'] = df_display['Total AUM (MXN)'].apply(
            lambda x: f"${x:,.0f}" if pd.notna(x) else "$0"
        )
        df_display['Mutual Fund AUM (MXN)'] = df_display['Mutual Fund AUM (MXN)'].apply(
            lambda x: f"${x:,.0f}" if pd.notna(x) else "$0"
        )
        
        # Format USD amounts
        df_display['Total AUM (USD)'] = df_display['Total AUM (USD)'].apply(
            lambda x: f"${x:,.0f}" if pd.notna(x) else "$0"
        )
        df_display['Mutual Fund AUM (USD)'] = df_display['Mutual Fund AUM (USD)'].apply(
            lambda x: f"${x:,.0f}" if pd.notna(x) else "$0"
        )
        
        # Format percentages
        df_display['MF AUM as % of Total'] = df_display['MF AUM as % of Total'].apply(
            lambda x: f"{x:.2f}%" if pd.notna(x) else "0.00%"
        )
        
        # Print table
        print(df_display.to_string(index=False, justify='left'))
        print(f"="*120)
        
        return df_display
        
    def save_to_csv(self, df, period, suffix="", output_file=None):
        """Save table to CSV file."""
        if not output_file:
            output_file = f"output/consar_aum_analysis_{period.replace('-', '_')}{suffix}.csv"
            
        # Ensure output directory exists
        Path(output_file).parent.mkdir(parents=True, exist_ok=True)
        
        # Save the original numeric data
        df.to_csv(output_file, index=False)
        print(f"Table saved to: {output_file}")
        
    def run(self, show_mxn=True, show_combined=False):
        """Run the complete analysis."""
        # Load data
        data = self.load_data()
        
        # Filter for target period
        filtered_data, period = self.filter_data_for_period(data, self.output_period)
        
        if not filtered_data:
            print("ERROR: No data found for the specified period")
            return None
            
        # Get FX rate
        fx_rate = self.get_fx_rate(filtered_data)
        
        # Calculate AUM by Afore
        aum_data = self.calculate_aum_by_afore(filtered_data)
        
        if not aum_data:
            print("ERROR: No AUM data could be calculated")
            return None
        
        results = {}
        
        # Create and display MXN table
        if show_mxn:
            df_mxn = self.create_summary_table_mxn(aum_data, period, fx_rate)
            df_display_mxn = self.format_table_mxn(df_mxn, period, fx_rate)
            self.save_to_csv(df_mxn, period, "_mxn")
            results['mxn'] = df_mxn
        
        # Create and display combined table
        if show_combined:
            df_combined = self.create_summary_table_combined(aum_data, period, fx_rate)
            df_display_combined = self.format_table_combined(df_combined, period, fx_rate)
            self.save_to_csv(df_combined, period, "_combined")
            results['combined'] = df_combined
            
        return results

def main():
    parser = argparse.ArgumentParser(description='Generate AUM analysis table with MXN values')
    parser.add_argument('--database', type=str,
                       default='data/merged_consar_data_2019_2025.json',
                       help='Path to CONSAR database file')
    parser.add_argument('--period', type=str,
                       help='Period to analyze (format: YYYY-MM). If not specified, uses latest period')
    parser.add_argument('--mxn-only', action='store_true',
                       help='Show only MXN table')
    parser.add_argument('--combined', action='store_true',
                       help='Show combined MXN and USD table')
    
    args = parser.parse_args()
    
    show_mxn = True
    show_combined = args.combined or not args.mxn_only
    
    analyzer = AUMAnalyzerMXN(args.database, args.period)
    analyzer.run(show_mxn=show_mxn, show_combined=show_combined)

if __name__ == "__main__":
    main()