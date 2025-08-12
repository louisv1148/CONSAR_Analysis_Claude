#!/usr/bin/env python3
"""
Growth Analysis for CONSAR Active Management Assets

Analyzes growth in:
- Mutual Funds (Inversión en Fondos Mutuos)
- Third Party Mandates (Inversiones Tercerizadas)  
- Total Active Management (sum of both)

Across different time periods: YTD, 1Y, 3Y, 5Y
"""

import json
import pandas as pd
from datetime import datetime, timedelta
from pathlib import Path
import argparse

class GrowthAnalyzer:
    """Analyzes growth in active management assets over different time periods."""
    
    def __init__(self, database_path):
        self.database_path = Path(database_path)
        self.concepts = {
            'mutual_funds': 'Inversión en Fondos Mutuos',
            'third_party': 'Inversiones Tercerizadas'
        }
        
    def load_data(self):
        """Load the historical database."""
        print(f"Loading data from: {self.database_path}")
        with open(self.database_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        print(f"Loaded {len(data):,} records")
        return data
        
    def get_period_data(self, data, year, month):
        """Get aggregated data for a specific period (year-month)."""
        period_data = {}
        
        for record in data:
            if (record.get('PeriodYear') == str(year) and 
                record.get('PeriodMonth') == f"{month:02d}" and
                record.get('valueUSD') is not None):
                
                afore = record.get('Afore', 'Unknown')
                concept = record.get('Concept')
                value_usd = record.get('valueUSD', 0)
                
                if afore not in period_data:
                    period_data[afore] = {
                        'mutual_funds': 0,
                        'third_party': 0,
                        'total_active': 0
                    }
                
                if concept == self.concepts['mutual_funds']:
                    period_data[afore]['mutual_funds'] += value_usd
                elif concept == self.concepts['third_party']:
                    period_data[afore]['third_party'] += value_usd
                    
        # Calculate total active management
        for afore in period_data:
            period_data[afore]['total_active'] = (
                period_data[afore]['mutual_funds'] + 
                period_data[afore]['third_party']
            )
            
        return period_data
        
    def get_latest_period(self, data):
        """Find the most recent period in the data."""
        periods = set()
        for record in data:
            year = record.get('PeriodYear')
            month = record.get('PeriodMonth')
            if year and month:
                periods.add((int(year), int(month)))
        
        if not periods:
            return None, None
            
        latest_year, latest_month = max(periods)
        print(f"Latest period found: {latest_year}-{latest_month:02d}")
        return latest_year, latest_month
        
    def calculate_growth_rates(self, current_data, historical_data, period_name):
        """Calculate growth rates between two periods."""
        growth_data = []
        
        # Get all afores from current period
        all_afores = set(current_data.keys()) | set(historical_data.keys())
        
        for afore in sorted(all_afores):
            current = current_data.get(afore, {'mutual_funds': 0, 'third_party': 0, 'total_active': 0})
            historical = historical_data.get(afore, {'mutual_funds': 0, 'third_party': 0, 'total_active': 0})
            
            row = {'Afore': afore, 'Period': period_name}
            
            for asset_type in ['mutual_funds', 'third_party', 'total_active']:
                current_val = current[asset_type]
                historical_val = historical[asset_type]
                
                # Calculate growth rate and absolute change
                if historical_val > 0:
                    growth_rate = ((current_val - historical_val) / historical_val) * 100
                elif current_val > 0:
                    growth_rate = float('inf')  # New assets appeared
                else:
                    growth_rate = 0  # Both zero
                    
                absolute_change = current_val - historical_val
                
                row.update({
                    f'{asset_type}_current': current_val,
                    f'{asset_type}_historical': historical_val,
                    f'{asset_type}_growth_rate': growth_rate,
                    f'{asset_type}_absolute_change': absolute_change
                })
                
            growth_data.append(row)
            
        return growth_data
        
    def run_analysis(self):
        """Run complete growth analysis."""
        data = self.load_data()
        
        # Get latest period
        latest_year, latest_month = self.get_latest_period(data)
        if not latest_year:
            print("ERROR: No data found")
            return None
            
        current_data = self.get_period_data(data, latest_year, latest_month)
        
        # Define comparison periods
        periods = []
        
        # YTD: December of previous year
        if latest_month != 12:  # If not December, compare to Dec of previous year
            ytd_year = latest_year - 1 if latest_month <= 12 else latest_year
            ytd_month = 12
            periods.append(('YTD', ytd_year, ytd_month))
        
        # 1 Year ago
        one_year_ago_year = latest_year - 1
        one_year_ago_month = latest_month
        periods.append(('1Y', one_year_ago_year, one_year_ago_month))
        
        # 3 Years ago
        three_year_ago_year = latest_year - 3
        three_year_ago_month = latest_month
        periods.append(('3Y', three_year_ago_year, three_year_ago_month))
        
        # 5 Years ago
        five_year_ago_year = latest_year - 5
        five_year_ago_month = latest_month
        periods.append(('5Y', five_year_ago_year, five_year_ago_month))
        
        # Calculate growth for each period
        all_growth_data = []
        
        for period_name, comp_year, comp_month in periods:
            historical_data = self.get_period_data(data, comp_year, comp_month)
            
            if historical_data:  # Only if historical data exists
                growth_data = self.calculate_growth_rates(
                    current_data, historical_data, period_name
                )
                all_growth_data.extend(growth_data)
                print(f"✓ Calculated {period_name} growth (vs {comp_year}-{comp_month:02d})")
            else:
                print(f"✗ No data available for {period_name} comparison ({comp_year}-{comp_month:02d})")
        
        if not all_growth_data:
            print("ERROR: No growth data could be calculated")
            return None
            
        # Convert to DataFrame
        df = pd.DataFrame(all_growth_data)
        
        # Add current period info
        df['current_period'] = f"{latest_year}-{latest_month:02d}"
        
        return df
        
    def format_and_display(self, df):
        """Format and display the growth analysis."""
        if df is None or df.empty:
            print("No data to display")
            return
            
        print(f"\n" + "="*120)
        print("CONSAR ACTIVE MANAGEMENT GROWTH ANALYSIS")
        print(f"Current Period: {df['current_period'].iloc[0]}")
        print("="*120)
        
        # Create summary by period
        periods = df['Period'].unique()
        
        for period in ['YTD', '1Y', '3Y', '5Y']:
            if period not in periods:
                continue
                
            period_df = df[df['Period'] == period].copy()
            
            print(f"\n{period} GROWTH ANALYSIS:")
            print("-" * 80)
            
            # Calculate industry totals
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
            
            print(f"INDUSTRY TOTALS:")
            print(f"  Mutual Funds:       ${total_mf_current:,.0f} ({mf_growth:+.1f}%)")
            print(f"  Third Party:        ${total_tp_current:,.0f} ({tp_growth:+.1f}%)")
            print(f"  Total Active Mgmt:  ${total_active_current:,.0f} ({active_growth:+.1f}%)")
            print()
            
            # Show top performers by total active management growth
            period_df_sorted = period_df.sort_values('total_active_growth_rate', ascending=False)
            
            print("TOP PERFORMERS (by Total Active Management Growth):")
            for _, row in period_df_sorted.head(10).iterrows():
                afore = row['Afore']
                growth = row['total_active_growth_rate']
                current_val = row['total_active_current']
                
                if growth == float('inf'):
                    growth_str = "NEW"
                else:
                    growth_str = f"{growth:+.1f}%"
                    
                print(f"  {afore:12} ${current_val:>12,.0f} ({growth_str:>8})")
                
        return df
        
    def save_to_csv(self, df, output_file=None):
        """Save growth analysis to CSV."""
        if df is None or df.empty:
            return
            
        if not output_file:
            current_period = df['current_period'].iloc[0].replace('-', '_')
            output_file = f"output/consar_growth_analysis_{current_period}.csv"
            
        # Ensure output directory exists
        Path(output_file).parent.mkdir(parents=True, exist_ok=True)
        
        # Round numeric columns for cleaner CSV
        numeric_cols = df.select_dtypes(include=['float64']).columns
        df_save = df.copy()
        for col in numeric_cols:
            if 'growth_rate' in col:
                df_save[col] = df_save[col].round(2)
            else:
                df_save[col] = df_save[col].round(0)
                
        df_save.to_csv(output_file, index=False)
        print(f"\nGrowth analysis saved to: {output_file}")


def main():
    parser = argparse.ArgumentParser(description='Generate growth analysis for CONSAR active management assets')
    parser.add_argument('--database', type=str,
                       default='data/merged_consar_data_2019_2025.json',
                       help='Path to CONSAR database file')
    parser.add_argument('--output', type=str,
                       help='Output CSV filename')
    
    args = parser.parse_args()
    
    analyzer = GrowthAnalyzer(args.database)
    df = analyzer.run_analysis()
    analyzer.format_and_display(df)
    analyzer.save_to_csv(df, args.output)

if __name__ == "__main__":
    main()