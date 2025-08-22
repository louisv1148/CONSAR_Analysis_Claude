#!/usr/bin/env python3
"""
Generate AUM Analysis Table from CONSAR Historical Database

Creates a table with:
- Afores in alphabetical order (+ Total row)
- Total AUM (USD)
- Mutual Fund AUM (USD)  
- Mutual Fund AUM as % of Total AUM
"""

import json
import pandas as pd
from datetime import datetime
import argparse
from pathlib import Path

class AUMAnalyzer:
    """Analyzes AUM data from CONSAR database."""
    
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
                record.get('valueUSD') is not None)
        ]
        
        print(f"Filtered to {len(filtered_data)} records for period {target_period}")
        return filtered_data, target_period
        
    def calculate_aum_by_afore(self, data):
        """Calculate total AUM and mutual fund AUM by Afore."""
        aum_data = {}
        
        for record in data:
            afore = record.get('Afore')
            concept = record.get('Concept')
            value_usd = record.get('valueUSD', 0)
            
            if not afore or value_usd is None:
                continue
                
            if afore not in aum_data:
                aum_data[afore] = {
                    'total_aum': 0,
                    'mutual_fund_aum': 0
                }
            
            # Total AUM includes "Total de Activo" concept
            if concept == 'Total de Activo':
                aum_data[afore]['total_aum'] += value_usd
                
            # Mutual Fund AUM includes "Inversión en Fondos Mutuos" concept
            elif concept == 'Inversión en Fondos Mutuos':
                aum_data[afore]['mutual_fund_aum'] += value_usd
        
        return aum_data
        
    def create_summary_table(self, aum_data, period):
        """Create the summary table with totals and percentages."""
        
        # Prepare data for DataFrame
        table_data = []
        total_aum_sum = 0
        total_mf_sum = 0
        
        # Sort Afores alphabetically
        sorted_afores = sorted(aum_data.keys())
        
        for afore in sorted_afores:
            data = aum_data[afore]
            total_aum = data['total_aum']
            mf_aum = data['mutual_fund_aum']
            mf_percentage = (mf_aum / total_aum * 100) if total_aum > 0 else 0
            
            table_data.append({
                'Afore': afore,
                'Total AUM (USD)': total_aum,
                'Mutual Fund AUM (USD)': mf_aum,
                'MF AUM as % of Total': mf_percentage
            })
            
            total_aum_sum += total_aum
            total_mf_sum += mf_aum
        
        # Add totals row
        total_mf_percentage = (total_mf_sum / total_aum_sum * 100) if total_aum_sum > 0 else 0
        table_data.append({
            'Afore': 'TOTAL',
            'Total AUM (USD)': total_aum_sum,
            'Mutual Fund AUM (USD)': total_mf_sum,
            'MF AUM as % of Total': total_mf_percentage
        })
        
        # Create DataFrame
        df = pd.DataFrame(table_data)
        
        return df
        
    def format_table(self, df, period):
        """Format the table for display."""
        print(f"\n" + "="*80)
        print(f"CONSAR AUM ANALYSIS - PERIOD: {period}")
        print(f"="*80)
        
        # Format numbers for display
        df_display = df.copy()
        
        # Format USD amounts with commas and 2 decimal places
        df_display['Total AUM (USD)'] = df_display['Total AUM (USD)'].apply(
            lambda x: f"${x:,.0f}" if pd.notna(x) else "$0"
        )
        df_display['Mutual Fund AUM (USD)'] = df_display['Mutual Fund AUM (USD)'].apply(
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
        
    def save_to_csv(self, df, period, output_file=None):
        """Save table to CSV file."""
        if not output_file:
            output_file = f"output/consar_aum_analysis_{period.replace('-', '_')}.csv"
            
        # Ensure output directory exists
        Path(output_file).parent.mkdir(parents=True, exist_ok=True)
        
        # Save the original numeric data (not the formatted display version)
        df.to_csv(output_file, index=False)
        print(f"\nTable saved to: {output_file}")
        
    def run(self):
        """Run the complete analysis."""
        # Load data
        data = self.load_data()
        
        # Filter for target period
        filtered_data, period = self.filter_data_for_period(data, self.output_period)
        
        if not filtered_data:
            print("ERROR: No data found for the specified period")
            return None
            
        # Calculate AUM by Afore
        aum_data = self.calculate_aum_by_afore(filtered_data)
        
        if not aum_data:
            print("ERROR: No AUM data could be calculated")
            return None
            
        # Create summary table
        df = self.create_summary_table(aum_data, period)
        
        # Display formatted table
        df_display = self.format_table(df, period)
        
        # Save to CSV
        self.save_to_csv(df, period)
        
        return df

def main():
    parser = argparse.ArgumentParser(description='Generate AUM analysis table from CONSAR data')
    parser.add_argument('--database', type=str,
                       default='data/merged_consar_data_2019_2025.json',
                       help='Path to CONSAR database file')
    parser.add_argument('--period', type=str,
                       help='Period to analyze (format: YYYY-MM). If not specified, uses latest period')
    parser.add_argument('--output', type=str,
                       help='Output CSV filename')
    
    args = parser.parse_args()
    
    analyzer = AUMAnalyzer(args.database, args.period)
    analyzer.run()

if __name__ == "__main__":
    main()