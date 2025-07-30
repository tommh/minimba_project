#!/usr/bin/env python3
"""
Fix integer overflow issues in CSV data
"""

import pandas as pd
import sys
from pathlib import Path

def analyze_csv_data_types():
    """Analyze the CSV to find problematic integer values"""
    
    csv_file = Path("data/downloads/csv/enova_data_2024.csv")
    if not csv_file.exists():
        print("❌ CSV file not found")
        return
    
    print("=== Analyzing CSV Data Types ===")
    
    # Read CSV
    df = pd.read_csv(csv_file)
    print(f"Total rows: {len(df):,}")
    
    # Check integer fields that might overflow
    int_fields = ['Knr', 'Gnr', 'Bnr', 'Snr', 'Fnr', 'Andelsnummer', 
                 'Bygningsnummer', 'Postnummer', 'Organisasjonsnummer', 'Byggear']
    
    print(f"\nChecking numeric fields for overflow:")
    
    overflow_fields = []
    
    for field in int_fields:
        if field in df.columns:
            # Convert to numeric, replacing empty strings with NaN
            df[field] = df[field].replace('', pd.NA)
            numeric_series = pd.to_numeric(df[field], errors='coerce')
            
            # Remove NaN values for analysis
            valid_values = numeric_series.dropna()
            
            if len(valid_values) > 0:
                max_val = valid_values.max()
                min_val = valid_values.min()
                
                # SQL Server int range: -2,147,483,648 to 2,147,483,647
                sql_int_max = 2147483647
                sql_int_min = -2147483648
                
                overflow = max_val > sql_int_max or min_val < sql_int_min
                
                print(f"\n{field}:")
                print(f"  Max value: {max_val:,}")
                print(f"  Min value: {min_val:,}")
                print(f"  SQL int range exceeded: {'YES' if overflow else 'NO'}")
                
                if overflow:
                    overflow_fields.append(field)
                    
                    # Show some example values that would overflow
                    overflow_values = valid_values[(valid_values > sql_int_max) | (valid_values < sql_int_min)]
                    print(f"  Example overflow values: {overflow_values.head().tolist()}")
    
    if overflow_fields:
        print(f"\n⚠️  Fields that exceed SQL int range: {overflow_fields}")
        print(f"\nSolution: Change these fields to BIGINT or VARCHAR in database")
        
        # Show SQL to fix the table
        print(f"\n=== SQL Commands to Fix Table ===")
        for field in overflow_fields:
            print(f"ALTER TABLE [ev_enova].[EnovaApi_ImpHist] ALTER COLUMN [{field}] BIGINT;")
    else:
        print(f"\n✅ All numeric fields fit within SQL int range")

def create_fixed_csv():
    """Create a CSV with problematic values handled"""
    
    csv_file = Path("data/downloads/csv/enova_data_2024.csv")
    if not csv_file.exists():
        print("❌ CSV file not found")
        return
    
    print(f"\n=== Creating Fixed CSV ===")
    
    # Read original CSV
    df = pd.read_csv(csv_file)
    
    # Fields that commonly overflow
    bigint_fields = ['Bygningsnummer', 'Organisasjonsnummer']
    
    # Convert problematic fields to string to avoid overflow
    for field in bigint_fields:
        if field in df.columns:
            # Keep as string - don't convert to numeric
            df[field] = df[field].astype(str)
            df[field] = df[field].replace('nan', '')  # Clean up
            print(f"  Converted {field} to string")
    
    # Save fixed CSV
    fixed_file = Path("data/downloads/csv/enova_data_2024_fixed.csv")
    df.to_csv(fixed_file, index=False)
    
    print(f"✅ Fixed CSV saved to: {fixed_file}")
    print(f"   Use this file for import to avoid overflow errors")

def main():
    analyze_csv_data_types()
    
    response = input(f"\nCreate a fixed CSV file? (y/n): ").lower()
    if response == 'y':
        create_fixed_csv()
    
    print(f"\n" + "="*60)
    print("SOLUTIONS:")
    print("1. CHANGE TABLE COLUMNS TO BIGINT (Recommended):")
    print("   ALTER TABLE [ev_enova].[EnovaApi_ImpHist] ALTER COLUMN [Bygningsnummer] BIGINT;")
    print("   ALTER TABLE [ev_enova].[EnovaApi_ImpHist] ALTER COLUMN [Organisasjonsnummer] BIGINT;")
    print("")
    print("2. OR USE FIXED CSV FILE:")
    print("   Use enova_data_2024_fixed.csv which handles large numbers as strings")
    print("")
    print("3. OR UPDATE CSV PROCESSOR:")
    print("   Modify the processor to handle large integers properly")
    print("="*60)

if __name__ == "__main__":
    main()
