#!/usr/bin/env python3
"""
MinimBA Energy Certificate Data Processing System - Minimal Entry Point
"""

import sys
from pathlib import Path
from src.services.file_downloader import FileDownloader
from config import Config

def main():
    """Minimal main function to test file downloader"""
    try:
        # Load configuration
        config = Config()
        
        # Create file downloader
        downloader = FileDownloader(config)
        
        # Download year
        year = 2024
        print(f"Downloading data for year {year}...")
        
        result = downloader.download_year_data(year=year)
        
        if result['success']:
            print(f"✓ Success: {result['file_path']}")
            print(f"  Date range: {result['from_date']} to {result['to_date']}")
            print(f"  File size: {result['file_size']:,} bytes")
            if not result.get('downloaded', False):
                print("  (File already existed)")
        else:
            print(f"✗ Failed: {result['error']}")
            return 1
        
        return 0
        
    except Exception as e:
        print(f"Error: {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(main())