#!/usr/bin/env python3
"""
Validate Definitive Database Integrity

Quick validation script to ensure the definitive database maintains its integrity.
Run this before using the database for analysis or after any updates.
"""

import json
from pathlib import Path
import sys

def validate_definitive_database():
    """Validate the definitive database integrity."""
    
    # Find the project root directory (where data folder is located)
    script_dir = Path(__file__).parent
    project_root = script_dir.parent.parent
    database_path = project_root / 'data/merged_consar_data_2019_2025.json'
    
    print("🔍 VALIDATING DEFINITIVE CONSAR DATABASE")
    print("=" * 50)
    
    # Check if file exists
    if not database_path.exists():
        print("❌ CRITICAL: Database file not found!")
        return False
    
    try:
        # Load database
        with open(database_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        print(f"📊 Records loaded: {len(data):,}")
        
        # Test 1: Check scaling consistency
        print("\n1️⃣ Testing scaling consistency...")
        period_totals = {}
        for record in data:
            if record.get('Concept') == 'Total de Activo':
                period = f"{record.get('PeriodYear')}-{record.get('PeriodMonth')}"
                value_mxn = record.get('valueMXN', 0)
                
                if period not in period_totals:
                    period_totals[period] = 0
                period_totals[period] += value_mxn
        
        # Check critical periods that had scaling issues
        critical_periods = ['2024-12', '2025-05', '2025-06']
        scaling_ok = True
        
        for period in critical_periods:
            if period in period_totals:
                total = period_totals[period]
                if total < 1_000_000_000_000:  # Less than 1 trillion
                    print(f"   ❌ {period}: {total:,.0f} MXN (TOO SMALL)")
                    scaling_ok = False
                else:
                    print(f"   ✅ {period}: {total:,.0f} MXN")
            else:
                print(f"   ⚠️  {period}: No data found")
        
        if scaling_ok:
            print("   ✅ Scaling consistency: PASSED")
        else:
            print("   ❌ Scaling consistency: FAILED")
            return False
        
        # Test 2: Check USD coverage
        print("\n2️⃣ Testing USD coverage...")
        usd_count = sum(1 for r in data if 'valueUSD' in r and r['valueUSD'] is not None)
        coverage_pct = usd_count / len(data) * 100
        
        print(f"   USD records: {usd_count:,} / {len(data):,} ({coverage_pct:.1f}%)")
        
        if coverage_pct >= 99.0:
            print("   ✅ USD coverage: EXCELLENT")
        elif coverage_pct >= 95.0:
            print("   ⚠️  USD coverage: GOOD (but not optimal)")
        else:
            print("   ❌ USD coverage: POOR")
            return False
        
        # Test 3: Check FX rate presence
        print("\n3️⃣ Testing FX rate coverage...")
        fx_count = sum(1 for r in data if r.get('FX_EOM') is not None)
        fx_coverage_pct = fx_count / len(data) * 100
        
        print(f"   FX records: {fx_count:,} / {len(data):,} ({fx_coverage_pct:.1f}%)")
        
        if fx_coverage_pct == 100.0:
            print("   ✅ FX coverage: PERFECT")
        else:
            print("   ❌ FX coverage: INCOMPLETE")
            return False
        
        # Test 4: Mathematical consistency check
        print("\n4️⃣ Testing USD calculation accuracy...")
        math_errors = 0
        sample_size = min(1000, len(data))
        
        for i, record in enumerate(data[:sample_size]):
            value_mxn = record.get('valueMXN')
            value_usd = record.get('valueUSD')
            fx_rate = record.get('FX_EOM')
            
            if value_mxn is not None and value_usd is not None and fx_rate is not None and fx_rate > 0:
                calculated_usd = value_mxn / fx_rate
                if abs(value_usd - calculated_usd) > 1.0:  # Allow 1 USD difference for rounding
                    math_errors += 1
        
        if math_errors == 0:
            print(f"   ✅ Mathematical accuracy: PERFECT (tested {sample_size:,} records)")
        else:
            print(f"   ❌ Mathematical accuracy: {math_errors} errors in {sample_size:,} records")
            return False
        
        # Test 5: Required fields check
        print("\n5️⃣ Testing required fields...")
        required_fields = ['Afore', 'Siefore', 'Concept', 'valueMXN', 'PeriodYear', 'PeriodMonth', 'FX_EOM']
        missing_fields = 0
        
        for record in data:
            for field in required_fields:
                if field not in record or record[field] is None:
                    missing_fields += 1
                    break
        
        if missing_fields == 0:
            print("   ✅ Required fields: ALL PRESENT")
        else:
            print(f"   ❌ Required fields: {missing_fields} records missing fields")
            return False
        
        print("\n🎉 VALIDATION RESULT: DATABASE IS VALID")
        print("=" * 50)
        print("✅ This database is ready for production use")
        print("✅ All consistency checks passed")
        print("✅ Safe to use for analysis and reporting")
        
        return True
        
    except json.JSONDecodeError:
        print("❌ CRITICAL: Database file is corrupted (invalid JSON)")
        return False
    except Exception as e:
        print(f"❌ CRITICAL: Validation failed with error: {str(e)}")
        return False

def main():
    """Main validation function."""
    if validate_definitive_database():
        print("\n🚀 Ready to run CONSAR analysis!")
        sys.exit(0)
    else:
        print("\n💥 Database validation failed!")
        print("⚠️  DO NOT use this database for analysis")
        print("🔧 Run fix_database_consistency.py to repair")
        sys.exit(1)

if __name__ == "__main__":
    main()