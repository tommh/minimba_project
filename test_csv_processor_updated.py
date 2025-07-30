#!/usr/bin/env python3
"""
Test script for CSV processor with duplicate handling - Updated for SQL Server 2025
"""

import sys
import logging
from pathlib import Path
from src.services.csv_processor import CSVProcessor, test_database_connection
from config import Config

# Setup logging for better error visibility
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def main():
    """Test CSV processing with detailed output"""
    try:
        # Load configuration
        config = Config()
        print("✓ Configuration loaded")
        print(f"  Server: {config.DATABASE_SERVER}")
        print(f"  Database: {config.DATABASE_NAME}")
        print(f"  Driver: {config.DATABASE_DRIVER}")
        
        # Test database connection first
        print("\n=== Testing Database Connection ===")
        if not test_database_connection(config):
            print("❌ Database connection failed. Check your .env file database settings.")
            print("Required settings:")
            print("  DATABASE_SERVER=TH\\\\SQL2025")
            print("  DATABASE_NAME=EnergyCertificate")
            print("  DATABASE_DRIVER=ODBC Driver 17 for SQL Server")
            print("  DATABASE_TRUSTED_CONNECTION=yes")
            print("\nTry running: python debug_db_connection.py")
            return 1
        
        print("✅ Database connection successful!")
        
        # Find CSV file
        csv_file = Path("data/downloads/csv/enova_data_2024.csv")
        if not csv_file.exists():
            print(f"\n❌ CSV file not found: {csv_file}")
            print("Make sure you've downloaded the data first with:")
            print("  python main.py download --year 2025")
            print("  OR python main.py both --year 2025")
            return 1
        
        print(f"\n✓ Found CSV file: {csv_file}")
        print(f"  File size: {csv_file.stat().st_size:,} bytes")
        
        # Create processor
        processor = CSVProcessor(config)
        
        # Step 1: Analyze CSV structure
        print("\n=== Analyzing CSV Structure ===")
        try:
            analysis = processor.analyze_csv_structure(str(csv_file))
        except Exception as e:
            print(f"❌ Failed to analyze CSV: {e}")
            return 1
        
        print(f"✓ CSV Analysis Results:")
        print(f"  - Separator: '{analysis['separator']}'")
        print(f"  - Encoding: {analysis['encoding']}")
        print(f"  - Total columns: {analysis['total_columns']}")
        print(f"  - Total rows: {analysis['total_rows']:,}")
        
        print(f"\n  Column names (showing first 10):")
        for i, col in enumerate(analysis['columns'][:10]):
            print(f"    {i+1:2d}: {col}")
        if len(analysis['columns']) > 10:
            print(f"    ... and {len(analysis['columns']) - 10} more columns")
        
        print(f"\n  Sample data (first row):")
        if analysis.get('sample_data') and len(analysis['sample_data']) > 0:
            sample = analysis['sample_data'][0]
            for key, value in list(sample.items())[:5]:  # Show first 5 fields
                print(f"    {key}: {value}")
            print("    ...")
        
        # Step 2: Check for existing records
        print("\n=== Checking for Existing Records ===")
        
        try:
            # Read the CSV to check duplicates
            import pandas as pd
            df = pd.read_csv(str(csv_file), sep=analysis['separator'], encoding=analysis['encoding'])
            
            duplicate_check = processor.check_existing_records(df)
            
            print(f"✓ Duplicate Check Results:")
            print(f"  - Total records in CSV: {len(df):,}")
            print(f"  - Already in database: {duplicate_check['existing_count']:,}")
            print(f"  - New records to import: {duplicate_check['new_count']:,}")
            
            if duplicate_check.get('check_error'):
                print(f"  ⚠️  Warning during duplicate check: {duplicate_check['check_error']}")
            
            if duplicate_check['existing_count'] > 0:
                print(f"\n  Sample existing Attestnummer values:")
                existing_sample = duplicate_check['existing_attestnummer'][:5]
                for i, attestnr in enumerate(existing_sample, 1):
                    print(f"    {i}: {attestnr}")
                if len(duplicate_check['existing_attestnummer']) > 5:
                    print(f"    ... and {len(duplicate_check['existing_attestnummer']) - 5} more")
        
        except Exception as e:
            print(f"❌ Error during duplicate checking: {e}")
            print("Will proceed with import (duplicates may be rejected)")
            duplicate_check = {'new_count': len(df) if 'df' in locals() else 0}
        
        # Step 3: Ask user what to do
        print(f"\n=== Processing Options ===")
        if duplicate_check.get('new_count', 0) == 0:
            print("ℹ️  All records already exist in database - nothing to import")
            return 0
        
        print(f"Ready to import {duplicate_check.get('new_count', 'unknown'):,} new records")
        print("Options:")
        print("  1. Import only NEW records (skip duplicates) - RECOMMENDED")
        print("  2. Try to import ALL records (may fail on duplicates)")
        print("  3. Just show analysis (don't import anything)")
        
        while True:
            choice = input("\nEnter your choice (1/2/3): ").strip()
            if choice in ['1', '2', '3']:
                break
            print("Please enter 1, 2, or 3")
        
        if choice == '3':
            print("Analysis complete - no import performed")
            return 0
        
        # Step 4: Process the CSV
        skip_duplicates = (choice == '1')
        
        print(f"\n=== Starting CSV Import ===")
        print(f"Mode: {'Skip duplicates' if skip_duplicates else 'Import all (may fail on duplicates)'}")
        print("Processing...")
        
        try:
            result = processor.process_csv_file(
                str(csv_file), 
                batch_size=500, 
                skip_duplicates=skip_duplicates
            )
        except Exception as e:
            print(f"❌ CSV processing failed: {e}")
            import traceback
            print("\nFull error details:")
            print(traceback.format_exc())
            return 1
        
        # Step 5: Show results
        print(f"\n=== Import Results ===")
        if result.get('success', False):
            print("✅ CSV import completed successfully!")
            print(f"   Total rows in CSV: {result.get('total_processed', 0):,}")
            print(f"   Records inserted: {result.get('total_inserted', 0):,}")
            print(f"   Records skipped: {result.get('total_skipped', 0):,}")
            
            insert_result = result.get('database_insert', {})
            failed_rows = insert_result.get('failed_rows', 0)
            if failed_rows > 0:
                print(f"   Records failed: {failed_rows:,}")
            
            if insert_result.get('errors'):
                print(f"\n⚠️  Warnings/Errors ({len(insert_result['errors'])}):")
                for i, error in enumerate(insert_result['errors'][:3], 1):
                    print(f"   {i}: {error}")
                if len(insert_result['errors']) > 3:
                    print(f"   ... and {len(insert_result['errors']) - 3} more errors")
            
            # Show column mapping used
            if 'column_mapping' in result and result['column_mapping']:
                print(f"\n📋 Column Mappings Used ({len(result['column_mapping'])}):")
                for csv_col, db_col in list(result['column_mapping'].items())[:5]:
                    print(f"   {csv_col} -> {db_col}")
                if len(result['column_mapping']) > 5:
                    print(f"   ... and {len(result['column_mapping']) - 5} more mappings")
            
            print(f"\n🎉 Import completed successfully!")
            print(f"\nNext steps:")
            print(f"1. Data is now in [ev_enova].[EnovaApi_ImpHist] table")
            print(f"2. You can proceed to Step 3: API processing")
            print(f"3. Run CSV import again anytime - it will skip duplicates")
            
        else:
            print("❌ CSV import failed!")
            error_msg = result.get('error', 'Unknown error')
            print(f"Error: {error_msg}")
            
            # Show any partial results
            if 'database_insert' in result:
                insert_result = result['database_insert']
                if insert_result.get('inserted_rows', 0) > 0:
                    print(f"Partial success: {insert_result['inserted_rows']} rows were inserted")
            
            # Check if it's a table missing error
            if "invalid object name" in error_msg.lower() or "table" in error_msg.lower():
                print(f"\n💡 Looks like the target table doesn't exist.")
                print(f"   Create the [ev_enova].[EnovaApi_ImpHist] table first:")
                print(f"   1. Connect to SQL Server Management Studio")
                print(f"   2. Use the EnergyCertificate database")
                print(f"   3. Create schema: CREATE SCHEMA ev_enova;")
                print(f"   4. Create the table with your table definition")
            
            return 1
        
        return 0
        
    except KeyboardInterrupt:
        print("\n\n⏹️  Import cancelled by user")
        return 1
    except Exception as e:
        print(f"\n❌ Unexpected error: {str(e)}")
        import traceback
        print("\nFull error details:")
        print(traceback.format_exc())
        return 1

if __name__ == "__main__":
    sys.exit(main())
