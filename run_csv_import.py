#!/usr/bin/env python3
"""
Simple wrapper script to run CSV imports for different years
"""

import subprocess
import sys
from pathlib import Path

def run_csv_import(year, auto_import=True):
    """
    Run CSV import for a specific year
    
    Args:
        year (int): Year to import (e.g., 2010, 2011, 2012)
        auto_import (bool): Whether to use auto-import mode (default: True)
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

if __name__ == "__main__":
    # You can also run individual years
    if len(sys.argv) > 1:
        year = int(sys.argv[1])
        auto_import = "--no-auto" not in sys.argv
        run_csv_import(year, auto_import)
    else:
        main() 