#!/usr/bin/env python3
"""
MinimBA Energy Certificate Data Processing System - Main Entry Point
"""

import sys
import argparse
from pathlib import Path
from src.services.file_downloader import FileDownloader
from src.services.api_client import EnovaApiClient
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

def cleanup_pending_records(config, hours=24):
    """Clean up old pending records"""
    print(f"Cleaning up pending records older than {hours} hours...")
    
    try:
        client = EnovaApiClient(config)
        cleanup_count = client.cleanup_old_pending_records(hours)
        
        if cleanup_count > 0:
            print(f"✓ Cleaned up {cleanup_count} old pending records")
        else:
            print("✓ No old pending records found")
        
        return True
        
    except Exception as e:
        print(f"✗ Cleanup failed: {str(e)}")
        return False

def process_api_certificates(config, rows=10):
    """Process energy certificates through API"""
    print(f"Processing {rows} certificates through API...")
    
    try:
        client = EnovaApiClient(config)
        result = client.process_certificates(rows)
        
        if result['success']:
            print(f"✓ API processing completed successfully")
            print(f"  Parameters logged: {result['parameters_logged']}")
            print(f"  API calls made: {result['api_calls']}")
            print(f"  Records inserted: {result['records_inserted']}")
            print(f"  Processing time: {result['processing_time']:.3f} seconds")
            if result['api_calls'] > 0:
                print(f"  Avg time per API call: {result['avg_time_per_api_call']:.4f} seconds")
            
            # Show status breakdown if available
            if 'status_breakdown' in result and result['status_breakdown']:
                print("\n  📊 Status breakdown:")
                for status, info in result['status_breakdown'].items():
                    if status != '_totals':
                        print(f"    {status}: {info['count']} calls → {info['records']} records returned")
            return True
        else:
            print(f"✗ API processing failed: {result['message']}")
            return False
            
    except Exception as e:
        print(f"✗ API processing error: {str(e)}")
        return False

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
  python main.py api --rows 5                     # Process 5 certificates through API
  python main.py cleanup --hours 1                # Clean up pending records older than 1 hour
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
    
    # API command
    api_parser = subparsers.add_parser('api', help='Process certificates through API')
    api_parser.add_argument('--rows', type=int, default=10, 
                           help='Number of certificate rows to process (default: 10)')
    
    # Cleanup command
    cleanup_parser = subparsers.add_parser('cleanup', help='Clean up old pending records')
    cleanup_parser.add_argument('--hours', type=int, default=24, 
                               help='Age in hours for records to be considered stale (default: 24)')
    
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
            
        elif args.command == 'api':
            success = process_api_certificates(config, args.rows)
            return 0 if success else 1
            
        elif args.command == 'cleanup':
            success = cleanup_pending_records(config, args.hours)
            return 0 if success else 1
            
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