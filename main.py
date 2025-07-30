#!/usr/bin/env python3
"""
MinimBA Energy Certificate Data Processing System - Main Entry Point
"""

import sys
import argparse
from pathlib import Path
from src.services.file_downloader import FileDownloader
from config import Config

def download_year_data(config, year, force=False):
    """Download CSV data for a specific year"""
    downloader = FileDownloader(config)
    print(f"Downloading data for year {year}...")
    
    result = downloader.download_year_data(year=year, force_download=force)
    
    if result['success']:
        print(f"✓ Success: {result['file_path']}")
        print(f"  Date range: {result['from_date']} to {result['to_date']}")
        print(f"  File size: {result['file_size']:,} bytes")
        if not result.get('downloaded', False):
            print("  (File already existed)")
        return True
    else:
        print(f"✗ Failed: {result['error']}")
        return False

def download_multiple_years(config, start_year, end_year, force=False):
    """Download CSV data for multiple years"""
    success_count = 0
    total_count = end_year - start_year + 1
    
    for year in range(start_year, end_year + 1):
        if download_year_data(config, year, force):
            success_count += 1
        print()  # Empty line between years
    
    print(f"Downloaded {success_count}/{total_count} years successfully")
    return success_count == total_count

def list_downloaded_files(config):
    """List all downloaded CSV files"""
    csv_path = Path(config.DOWNLOAD_CSV_PATH)
    if not csv_path.exists():
        print(f"Download directory does not exist: {csv_path}")
        return
    
    csv_files = list(csv_path.glob("enova_data_*.csv"))
    if not csv_files:
        print("No CSV files found")
        return
    
    print(f"Found {len(csv_files)} CSV files:")
    total_size = 0
    
    for file_path in sorted(csv_files):
        size = file_path.stat().st_size
        total_size += size
        year = file_path.stem.replace('enova_data_', '')
        print(f"  {year}: {file_path.name} ({size:,} bytes)")
    
    print(f"\nTotal size: {total_size:,} bytes ({total_size/1024/1024:.1f} MB)")

def show_config(config):
    """Show current configuration"""
    print("Current Configuration:")
    print("=" * 50)
    summary = config.get_config_summary()
    for key, value in summary.items():
        print(f"{key}: {value}")
    print("=" * 50)

def main():
    """Main function with command line argument parsing"""
    parser = argparse.ArgumentParser(
        description='MinimBA Energy Certificate Data Processing System',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py download 2025                    # Download 2025 data
  python main.py download 2020 2025               # Download 2020-2025 data
  python main.py download 2025 --force            # Force re-download 2025
  python main.py list                             # List downloaded files
  python main.py config                           # Show configuration
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Download command
    download_parser = subparsers.add_parser('download', help='Download CSV data')
    download_parser.add_argument('year', type=int, help='Year to download (or start year if end_year specified)')
    download_parser.add_argument('end_year', type=int, nargs='?', help='End year for range download')
    download_parser.add_argument('--force', action='store_true', help='Force re-download even if file exists')
    
    # List command
    subparsers.add_parser('list', help='List downloaded files')
    
    # Config command
    subparsers.add_parser('config', help='Show current configuration')
    
    args = parser.parse_args()
    
    # Load configuration
    try:
        config = Config()
        if not config.validate_config():
            print("Configuration validation failed. Please check your .env file.")
            return 1
    except Exception as e:
        print(f"Configuration error: {str(e)}")
        return 1
    
    # Handle commands
    try:
        if args.command == 'download':
            if args.end_year:
                success = download_multiple_years(config, args.year, args.end_year, args.force)
            else:
                success = download_year_data(config, args.year, args.force)
            return 0 if success else 1
            
        elif args.command == 'list':
            list_downloaded_files(config)
            return 0
            
        elif args.command == 'config':
            show_config(config)
            return 0
            
        else:
            # Default behavior - download current year
            from datetime import datetime
            current_year = datetime.now().year
            success = download_year_data(config, current_year)
            return 0 if success else 1
        
    except KeyboardInterrupt:
        print("\nOperation cancelled by user")
        return 1
    except Exception as e:
        print(f"Error: {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(main())