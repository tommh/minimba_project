#!/usr/bin/env python3
"""
MinimBA Energy Certificate Data Processing System - Main Entry Point
"""

import sys
import argparse
from pathlib import Path
from src.services.file_downloader import FileDownloader
from src.services.api_client import EnovaApiClient
from src.services.openai_service import OpenAIEnergyService
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

def scan_pdf_files(config, force=False, batch_size=100):
    """Scan PDF directory and populate database table"""
    print(f"Scanning PDF files in {config.DOWNLOAD_PDF_PATH}...")
    
    try:
        from src.services.pdf_scanner import PDFFileScanner
        
        scanner = PDFFileScanner(config)
        result = scanner.scan_and_populate(batch_size=batch_size, skip_existing=not force)
        
        if result['success']:
            print(f"✓ PDF scan completed successfully")
            print(f"  Files processed: {result['files_processed']:,}")
            print(f"  Files added to database: {result['files_added']:,}")
            print(f"  Files skipped (existing): {result['files_skipped']:,}")
            if result.get('files_deleted', 0) > 0:
                print(f"  Files deleted from database: {result['files_deleted']:,}")
            return True
        else:
            print(f"✗ PDF scan failed")
            return False
            
    except ImportError:
        print(f"✗ PDF scanner module not found")
        return False
    except Exception as e:
        print(f"✗ PDF scan error: {str(e)}")
        return False

def download_pdfs(config, count=10, delay=1.0):
    """Download PDF files from certificate URLs"""
    print(f"Downloading up to {count} PDF files...")
    
    try:
        from pdf_downloader import PDFDownloader
        
        downloader = PDFDownloader(config)
        result = downloader.download_batch(top_rows=count, delay_between_downloads=delay)
        
        if result['success']:
            print(f"✓ PDF download completed successfully")
            print(f"  URLs processed: {result['attempted']:,}")
            print(f"  Downloads successful: {result['successful']:,}")
            print(f"  Downloads failed: {result['failed']:,}")
            print(f"  Downloads skipped: {result['skipped']:,}")
            
            # Calculate success rate
            total_attempts = result['successful'] + result['failed']
            if total_attempts > 0:
                success_rate = (result['successful'] / total_attempts) * 100
                print(f"  Success rate: {success_rate:.1f}%")
            
            return True
        else:
            print(f"✗ PDF download failed: {result.get('message', 'Unknown error')}")
            return False
            
    except ImportError:
        print(f"✗ PDF downloader module not found")
        return False
    except Exception as e:
        print(f"✗ PDF download error: {str(e)}")
        return False

def process_pdf_text(config, count=10, use_multiprocess=False, num_processes=None):
    """Extract text from PDF files using Docling"""
    print(f"Processing up to {count} PDF files for text extraction...")
    
    try:
        # Check if docling is available
        try:
            from docling.document_converter import DocumentConverter
        except ImportError:
            print(f"✗ Docling not installed. Please install with: pip install docling")
            return False
        
        if use_multiprocess:
            from src.services.pdf_processor import process_pdfs_multiprocess
            result = process_pdfs_multiprocess(config, count, num_processes)
        else:
            from src.services.pdf_processor import PDFTextProcessor
            processor = PDFTextProcessor(config)
            result = processor.process_batch_single_thread(count)
        
        if result['success']:
            print(f"✓ PDF text extraction completed successfully")
            print(f"  Files processed: {result['files_processed']:,}")
            print(f"  Successful extractions: {result['files_successful']:,}")
            print(f"  Failed extractions: {result['files_failed']:,}")
            print(f"  Processing time: {result['processing_time']:.1f} seconds")
            
            if result['files_processed'] > 0:
                success_rate = (result['files_successful'] / result['files_processed']) * 100
                rate = result['files_processed'] / result['processing_time'] if result['processing_time'] > 0 else 0
                print(f"  Success rate: {success_rate:.1f}%")
                print(f"  Processing rate: {rate:.1f} files/second")
            
            return True
        else:
            print(f"✗ PDF processing failed: {result.get('message', 'Unknown error')}")
            return False
            
    except ImportError:
        print(f"✗ PDF processor module not found")
        return False
    except Exception as e:
        print(f"✗ PDF processing error: {str(e)}")
        return False


def clean_pdf_text(config, count=10, use_multiprocess=False, num_processes=None, aggressive=False):
    """Clean extracted PDF text using regex patterns"""
    print(f"Cleaning up to {count} extracted PDF text records...")
    
    try:
        if use_multiprocess:
            from src.services.text_cleaner import process_text_cleaning_multiprocess
            result = process_text_cleaning_multiprocess(config, count, num_processes, aggressive)
        else:
            from src.services.text_cleaner import TextCleaningProcessor
            processor = TextCleaningProcessor(config)
            result = processor.process_batch_single_thread(count, aggressive)
        
        if result['success']:
            print(f"✓ PDF text cleaning completed successfully")
            print(f"  Records processed: {result['files_processed']:,}")
            print(f"  Successful cleanings: {result['files_successful']:,}")
            print(f"  Failed cleanings: {result['files_failed']:,}")
            print(f"  Processing time: {result['processing_time']:.1f} seconds")
            
            if result['files_processed'] > 0:
                success_rate = (result['files_successful'] / result['files_processed']) * 100
                rate = result['files_processed'] / result['processing_time'] if result['processing_time'] > 0 else 0
                print(f"  Success rate: {success_rate:.1f}%")
                print(f"  Processing rate: {rate:.1f} records/second")
            
            return True
        else:
            print(f"✗ Text cleaning failed: {result.get('message', 'Unknown error')}")
            return False
            
    except ImportError:
        print(f"✗ Text cleaner module not found")
        return False
    except Exception as e:
        print(f"✗ Text cleaning error: {str(e)}")
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

def process_openai_prompts(config, prompt_column="PROMPT_V1_NOR", limit=10, delay=1.0):
    """Process energy certificate prompts with OpenAI API"""
    print(f"Processing {limit} prompts with OpenAI using column: {prompt_column}")
    
    try:
        openai_service = OpenAIEnergyService(config)
        result = openai_service.process_prompts(
            prompt_column=prompt_column,
            limit=limit,
            delay_between_calls=delay
        )
        
        if result['success']:
            print("✓ OpenAI processing completed successfully")
            print(f"  Total prompts: {result['total_prompts']}")
            print(f"  Successfully processed: {result['prompts_processed']}")
            print(f"  Errors: {result['errors']}")
            print(f"  Processing time: {result['processing_time']:.3f} seconds")
            print(f"  Success rate: {result['success_rate']:.1f}%")
            return True
        else:
            print(f"✗ OpenAI processing failed: {result['message']}")
            return False
            
    except Exception as e:
        print(f"✗ OpenAI processing error: {str(e)}")
        return False

def show_openai_statistics(config, prompt_version=None):
    """Show OpenAI processing statistics"""
    try:
        openai_service = OpenAIEnergyService(config)
        stats = openai_service.get_processing_statistics(prompt_version)
        
        if not stats:
            print("No OpenAI processing statistics found")
            return True
        
        print("OpenAI Processing Statistics:")
        print("=" * 50)
        
        for prompt_ver, stat_data in stats.items():
            print(f"\nPrompt Version: {prompt_ver}")
            print(f"  Total responses: {stat_data['total_responses']}")
            print(f"  First processed: {stat_data['first_processed']}")
            print(f"  Last processed: {stat_data['last_processed']}")
            print(f"  Completion rates:")
            print(f"    About Estate: {stat_data['completion_rate']['about_estate']:.1f}%")
            print(f"    Positives: {stat_data['completion_rate']['positives']:.1f}%")
            print(f"    Evaluation: {stat_data['completion_rate']['evaluation']:.1f}%")
        
        return True
        
    except Exception as e:
        print(f"✗ Error getting statistics: {str(e)}")
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
  python main.py scan-pdf                         # Scan PDF directory and populate database
      python main.py scan-pdf --force                 # Force scan all PDFs (including existing)
    python main.py download-pdf --count 20          # Download 20 PDF files from URLs
    python main.py process-pdf --count 50           # Extract text from 50 PDF files
    python main.py process-pdf --multiprocess       # Use multiprocessing for faster extraction
    python main.py clean-text --count 100           # Clean 100 extracted text records
    python main.py clean-text --multiprocess        # Use multiprocessing for faster cleaning
    python main.py openai --limit 20                # Process 20 prompts with OpenAI
    python main.py openai --prompt-column PROMPT_V2_NOR --limit 10  # Use different prompt column
    python main.py openai-stats                     # Show OpenAI processing statistics
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
    
    # Scan PDF command
    scan_parser = subparsers.add_parser('scan-pdf', help='Scan PDF directory and populate database')
    scan_parser.add_argument('--force', action='store_true', 
                            help='Insert all files, even if they already exist in database')
    scan_parser.add_argument('--batch-size', type=int, default=100,
                            help='Number of files to insert per batch (default: 100)')
    
    # Download PDF command
    download_parser = subparsers.add_parser('download-pdf', help='Download PDF files from certificate URLs')
    download_parser.add_argument('--count', type=int, default=10,
                                help='Number of PDFs to download (default: 10)')
    download_parser.add_argument('--delay', type=float, default=1.0,
                                help='Delay between downloads in seconds (default: 1.0)')
    
    # Process PDF text command
    process_parser = subparsers.add_parser('process-pdf', help='Extract text from PDF files using Docling')
    process_parser.add_argument('--count', type=int, default=10,
                               help='Number of PDFs to process (default: 10)')
    process_parser.add_argument('--multiprocess', action='store_true',
                               help='Use multiprocessing for faster extraction')
    process_parser.add_argument('--processes', type=int, default=None,
                               help='Number of processes to use (default: auto-detect)')
    
    # Clean PDF text command
    clean_parser = subparsers.add_parser('clean-text', help='Clean extracted PDF text using regex patterns')
    clean_parser.add_argument('--count', type=int, default=10,
                             help='Number of records to clean (default: 10)')
    clean_parser.add_argument('--multiprocess', action='store_true',
                             help='Use multiprocessing for faster cleaning')
    clean_parser.add_argument('--processes', type=int, default=None,
                             help='Number of processes to use (default: auto-detect)')
    clean_parser.add_argument('--aggressive', action='store_true',
                             help='Use aggressive cleaning (removes more content)')
    
    # OpenAI command
    openai_parser = subparsers.add_parser('openai', help='Process energy certificates with OpenAI API')
    openai_parser.add_argument('--limit', type=int, default=10,
                              help='Number of prompts to process (default: 10)')
    openai_parser.add_argument('--prompt-column', type=str, default='PROMPT_V1_NOR',
                              help='Prompt column to use (default: PROMPT_V1_NOR)')
    openai_parser.add_argument('--delay', type=float, default=1.0,
                              help='Delay between API calls in seconds (default: 1.0)')
    
    # OpenAI statistics command
    subparsers.add_parser('openai-stats', help='Show OpenAI processing statistics')
    
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
            
        elif args.command == 'scan-pdf':
            success = scan_pdf_files(config, args.force, args.batch_size)
            return 0 if success else 1
            
        elif args.command == 'download-pdf':
            success = download_pdfs(config, args.count, args.delay)
            return 0 if success else 1
            
        elif args.command == 'process-pdf':
            success = process_pdf_text(config, args.count, args.multiprocess, args.processes)
            return 0 if success else 1
            
        elif args.command == 'clean-text':
            success = clean_pdf_text(config, args.count, args.multiprocess, args.processes, args.aggressive)
            return 0 if success else 1
            
        elif args.command == 'openai':
            success = process_openai_prompts(config, args.prompt_column, args.limit, args.delay)
            return 0 if success else 1
            
        elif args.command == 'openai-stats':
            success = show_openai_statistics(config)
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