#!/usr/bin/env python3
"""
Simple wrapper script to run CSV imports for different years
"""

import subprocess
import sys
import argparse
from pathlib import Path

def run_csv_import(year, auto_import=True):
    """
    Run CSV import for a specific year
    
    Args:
        year (int): Year to import (e.g., 2010, 2011, 2012)
        auto_import (bool): Whether to use auto-import mode (default: True)


     eg. python run_csv_import.py --start-year 2013 --end-year 2014   
    """
    print(f"🔄 Starting CSV import for year {year}...")
    
    # Build the command
    cmd = [sys.executable, "tests/test_csv_processor.py", "--year", str(year)]
    
    if auto_import:
        cmd.append("--auto-import")
    
    # Run the command
    try:
        result = subprocess.run(cmd, capture_output=False, text=True)
        return result.returncode == 0
    except Exception as e:
        print(f"❌ Error running import: {e}")
        return False

def main():
    """Main function to demonstrate usage"""
    print("📊 CSV Import Runner")
    print("=" * 50)
    
    # Example usage
    years_to_import = [2010, 2011, 2012]  # Add more years as needed
    
    for year in years_to_import:
        print(f"\n🎯 Processing year {year}...")
        success = run_csv_import(year, auto_import=True)
        
        if success:
            print(f"✅ Year {year} completed successfully")
        else:
            print(f"❌ Year {year} failed")
        
        print("-" * 30)

def run_year_range(start_year, end_year, auto_import=True):
    """
    Run CSV import for a range of years
    
    Args:
        start_year (int): Starting year (inclusive)
        end_year (int): Ending year (inclusive)
        auto_import (bool): Whether to use auto-import mode
    """
    print(f"🔄 Starting CSV import for years {start_year} to {end_year}...")
    
    successful_years = []
    failed_years = []
    
    for year in range(start_year, end_year + 1):
        print(f"\n🎯 Processing year {year}...")
        success = run_csv_import(year, auto_import)
        
        if success:
            successful_years.append(year)
            print(f"✅ Year {year} completed successfully")
        else:
            failed_years.append(year)
            print(f"❌ Year {year} failed")
        
        print("-" * 30)
    
    # Summary
    print(f"\n📊 Import Summary:")
    print(f"✅ Successful: {len(successful_years)} years - {successful_years}")
    print(f"❌ Failed: {len(failed_years)} years - {failed_years}")
    
    return len(failed_years) == 0

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Run CSV imports for specific years or year ranges')
    parser.add_argument('--start-year', type=int, help='Starting year for range import')
    parser.add_argument('--end-year', type=int, help='Ending year for range import')
    parser.add_argument('--year', type=int, help='Single year to import')
    parser.add_argument('--no-auto', action='store_true', help='Disable auto-import mode')
    
    args = parser.parse_args()
    
    auto_import = not args.no_auto
    
    if args.start_year and args.end_year:
        # Range import
        run_year_range(args.start_year, args.end_year, auto_import)
    elif args.year:
        # Single year import
        run_csv_import(args.year, auto_import)
    else:
        # Default behavior - run example years
        main() 