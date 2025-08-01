#!/usr/bin/env python3
"""
CSV Import Service for Energy Certificate Data
Provides batch import functionality for multiple years of data
"""

import subprocess
import sys
import argparse
from pathlib import Path
import logging

# Add the project root to the Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from config import Config
from src.services.csv_processor import CSVProcessor

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class CSVImportService:
    """Service for managing CSV imports across multiple years"""
    
    def __init__(self, config=None):
        self.config = config or Config()
        self.csv_processor = CSVProcessor(self.config)
    
    def import_year_data(self, year: int, auto_import: bool = True, batch_size: int = 1000) -> bool:
        """
        Import CSV data for a specific year
        
        Args:
            year (int): Year to import (e.g., 2010, 2011, 2012)
            auto_import (bool): Whether to use auto-import mode (default: True)
            batch_size (int): Batch size for processing (default: 1000)
        
        Returns:
            bool: True if successful, False otherwise
        """
        logger.info(f"🔄 Starting CSV import for year {year}...")
        
        try:
            # Build the CSV file path
            csv_file = Path(self.config.DOWNLOAD_CSV_PATH) / f"enova_data_{year}.csv"
            
            if not csv_file.exists():
                logger.error(f"❌ CSV file not found: {csv_file}")
                return False
            
            # Process the CSV file
            result = self.csv_processor.process_csv_file(
                str(csv_file), 
                batch_size=batch_size, 
                skip_duplicates=auto_import
            )
            
            if result['success']:
                logger.info(f"✅ Year {year} import completed successfully")
                logger.info(f"   Records processed: {result.get('total_records', 0):,}")
                logger.info(f"   Records inserted: {result.get('inserted_records', 0):,}")
                logger.info(f"   Records skipped: {result.get('skipped_records', 0):,}")
                return True
            else:
                logger.error(f"❌ Year {year} import failed: {result.get('error', 'Unknown error')}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error importing year {year}: {e}")
            return False
    
    def import_year_range(self, start_year: int, end_year: int, auto_import: bool = True, 
                         batch_size: int = 1000) -> dict:
        """
        Import CSV data for a range of years
        
        Args:
            start_year (int): Starting year (inclusive)
            end_year (int): Ending year (inclusive)
            auto_import (bool): Whether to use auto-import mode
            batch_size (int): Batch size for processing
            
        Returns:
            dict: Summary of import results
        """
        logger.info(f"🔄 Starting CSV import for years {start_year} to {end_year}...")
        
        successful_years = []
        failed_years = []
        
        for year in range(start_year, end_year + 1):
            logger.info(f"\n🎯 Processing year {year}...")
            success = self.import_year_data(year, auto_import, batch_size)
            
            if success:
                successful_years.append(year)
            else:
                failed_years.append(year)
            
            logger.info("-" * 30)
        
        # Summary
        logger.info(f"\n📊 Import Summary:")
        logger.info(f"✅ Successful: {len(successful_years)} years - {successful_years}")
        logger.info(f"❌ Failed: {len(failed_years)} years - {failed_years}")
        
        return {
            'successful_years': successful_years,
            'failed_years': failed_years,
            'total_success': len(failed_years) == 0
        }

# Legacy wrapper functions for backward compatibility
def run_csv_import(year, auto_import=True):
    """
    Legacy wrapper function for backward compatibility
    
    Args:
        year (int): Year to import (e.g., 2010, 2011, 2012)
        auto_import (bool): Whether to use auto-import mode (default: True)
    """
    service = CSVImportService()
    return service.import_year_data(year, auto_import)

def run_year_range(start_year, end_year, auto_import=True):
    """
    Legacy wrapper function for backward compatibility
    
    Args:
        start_year (int): Starting year (inclusive)
        end_year (int): Ending year (inclusive)
        auto_import (bool): Whether to use auto-import mode
    """
    service = CSVImportService()
    result = service.import_year_range(start_year, end_year, auto_import)
    return result['total_success']

def main():
    """Main function for command-line usage"""
    logger.info("📊 CSV Import Service")
    logger.info("=" * 50)
    
    # Example usage - default years
    years_to_import = [2010, 2011, 2012]  # Add more years as needed
    
    service = CSVImportService()
    
    for year in years_to_import:
        logger.info(f"\n🎯 Processing year {year}...")
        success = service.import_year_data(year, auto_import=True)
        
        if success:
            logger.info(f"✅ Year {year} completed successfully")
        else:
            logger.info(f"❌ Year {year} failed")
        
        logger.info("-" * 30)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Run CSV imports for specific years or year ranges')
    parser.add_argument('--start-year', type=int, help='Starting year for range import')
    parser.add_argument('--end-year', type=int, help='Ending year for range import')
    parser.add_argument('--year', type=int, help='Single year to import')
    parser.add_argument('--no-auto', action='store_true', help='Disable auto-import mode')
    parser.add_argument('--batch-size', type=int, default=1000, help='Batch size for processing (default: 1000)')
    
    args = parser.parse_args()
    
    auto_import = not args.no_auto
    service = CSVImportService()
    
    if args.start_year and args.end_year:
        # Range import
        result = service.import_year_range(args.start_year, args.end_year, auto_import, args.batch_size)
        sys.exit(0 if result['total_success'] else 1)
    elif args.year:
        # Single year import
        success = service.import_year_data(args.year, auto_import, args.batch_size)
        sys.exit(0 if success else 1)
    else:
        # Default behavior - run example years
        main() 