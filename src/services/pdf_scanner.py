#!/usr/bin/env python3
"""
PDF File Scanner and Database Populator
Scans data/downloads/pdfs directory and populates [ev_enova].[EnergylabelIDFiles] table
"""

import os
import sys
from pathlib import Path
from datetime import datetime
import pyodbc
import logging

# Add project root to path (go up two levels from src/services/)
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from config import Config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class PDFFileScanner:
    """Scans PDF directory and populates database table"""
    
    def __init__(self, config):
        self.config = config
        self.pdf_directory = Path(config.DOWNLOAD_PDF_PATH)
        self.files_processed = 0
        self.files_skipped = 0
        self.files_added = 0
        
    def get_database_connection(self):
        """Get database connection"""
        if self.config.DATABASE_TRUSTED_CONNECTION:
            conn_str = (
                f"DRIVER={{{self.config.DATABASE_DRIVER}}};"
                f"SERVER={self.config.DATABASE_SERVER};"
                f"DATABASE={self.config.DATABASE_NAME};"
                f"Trusted_Connection=yes;"
            )
        else:
            conn_str = (
                f"DRIVER={{{self.config.DATABASE_DRIVER}}};"
                f"SERVER={self.config.DATABASE_SERVER};"
                f"DATABASE={self.config.DATABASE_NAME};"
                f"UID={self.config.DATABASE_USERNAME};"
                f"PWD={self.config.DATABASE_PASSWORD};"
            )
        
        return pyodbc.connect(conn_str)
    
    def get_existing_files(self):
        """Get set of filenames already in database"""
        conn = None
        try:
            conn = self.get_database_connection()
            cursor = conn.cursor()
            
            cursor.execute("SELECT filename FROM [ev_enova].[EnergylabelIDFiles]")
            existing_files = {row.filename for row in cursor.fetchall()}
            
            logger.info(f"Found {len(existing_files)} files already in database")
            return existing_files
            
        except Exception as e:
            logger.error(f"Error getting existing files: {str(e)}")
            return set()
        finally:
            if conn:
                conn.close()
    
    def scan_pdf_directory(self):
        """Scan PDF directory and return file information"""
        if not self.pdf_directory.exists():
            logger.error(f"PDF directory does not exist: {self.pdf_directory}")
            return []
        
        logger.info(f"Scanning directory: {self.pdf_directory}")
        
        pdf_files = []
        for file_path in self.pdf_directory.rglob("*.pdf"):  # Recursive search for PDFs
            try:
                stat = file_path.stat()
                file_info = {
                    'filename': file_path.name,
                    'full_path': str(file_path),
                    'file_size': stat.st_size,
                    'file_extension': file_path.suffix.lower(),
                    'modified_date': datetime.fromtimestamp(stat.st_mtime)
                }
                pdf_files.append(file_info)
                
            except Exception as e:
                logger.warning(f"Error processing file {file_path}: {str(e)}")
                continue
        
        logger.info(f"Found {len(pdf_files)} PDF files in directory")
        return pdf_files
    
    def insert_file_batch(self, files_to_insert):
        """Insert batch of files into database"""
        if not files_to_insert:
            return 0
        
        conn = None
        try:
            conn = self.get_database_connection()
            cursor = conn.cursor()
            
            # Prepare batch insert with IGNORE duplicates approach
            insert_sql = """
                INSERT INTO [ev_enova].[EnergylabelIDFiles] 
                (filename, full_path, file_size, file_extension, sync_date)
                VALUES (?, ?, ?, ?, ?)
            """
            
            batch_data = []
            sync_date = datetime.now()
            
            for file_info in files_to_insert:
                batch_data.append((
                    file_info['filename'],
                    file_info['full_path'], 
                    file_info['file_size'],
                    file_info['file_extension'],
                    sync_date
                ))
            
            # Try individual inserts if batch fails (to handle duplicates gracefully)
            successful_inserts = 0
            try:
                # Try batch insert first
                cursor.executemany(insert_sql, batch_data)
                conn.commit()
                successful_inserts = len(batch_data)
                logger.info(f"Batch insert successful: {successful_inserts} files")
                
            except Exception as batch_error:
                logger.warning(f"Batch insert failed ({str(batch_error)}), trying individual inserts...")
                conn.rollback()
                
                # Fall back to individual inserts
                for i, data_row in enumerate(batch_data):
                    try:
                        cursor.execute(insert_sql, data_row)
                        conn.commit()
                        successful_inserts += 1
                    except Exception as row_error:
                        conn.rollback()
                        filename = data_row[0]
                        if "duplicate" in str(row_error).lower() or "unique" in str(row_error).lower():
                            logger.debug(f"Skipping duplicate file: {filename}")
                        else:
                            logger.warning(f"Failed to insert {filename}: {str(row_error)}")
            
            logger.info(f"Successfully inserted {successful_inserts} out of {len(batch_data)} files")
            return successful_inserts
            
        except Exception as e:
            logger.error(f"Error in insert_file_batch: {str(e)}")
            if conn:
                conn.rollback()
            return 0
        finally:
            if conn:
                conn.close()
    
    def cleanup_deleted_files(self):
        """
        Remove database records for files that no longer exist on disk
        
        Returns:
            Number of records deleted
        """
        conn = None
        try:
            conn = self.get_database_connection()
            cursor = conn.cursor()
            
            # Get all files from database
            cursor.execute("SELECT file_id, filename, full_path FROM [ev_enova].[EnergylabelIDFiles]")
            db_files = cursor.fetchall()
            
            files_to_delete = []
            
            logger.info(f"Checking {len(db_files)} database records against disk...")
            
            for db_file in db_files:
                file_id, filename, full_path = db_file.file_id, db_file.filename, db_file.full_path
                
                # Check if file still exists on disk
                if full_path and Path(full_path).exists():
                    continue  # File exists, keep it
                
                # File doesn't exist, mark for deletion
                files_to_delete.append((file_id, filename, full_path))
            
            if not files_to_delete:
                logger.info("No deleted files found - all database records have corresponding files on disk")
                return 0
            
            logger.info(f"Found {len(files_to_delete)} files that no longer exist on disk")
            
            # Delete records in batches
            batch_size = 100
            deleted_count = 0
            
            for i in range(0, len(files_to_delete), batch_size):
                batch = files_to_delete[i:i + batch_size]
                file_ids = [str(item[0]) for item in batch]
                
                # Create parameterized query for batch delete
                placeholders = ','.join(['?' for _ in file_ids])
                delete_sql = f"DELETE FROM [ev_enova].[EnergylabelIDFiles] WHERE file_id IN ({placeholders})"
                
                cursor.execute(delete_sql, file_ids)
                batch_deleted = cursor.rowcount
                deleted_count += batch_deleted
                
                # Log some examples from this batch
                for file_id, filename, full_path in batch[:3]:  # Show first 3
                    logger.info(f"  Deleted: {filename} (was: {full_path})")
                if len(batch) > 3:
                    logger.info(f"  ... and {len(batch) - 3} more in this batch")
            
            conn.commit()
            logger.info(f"Successfully deleted {deleted_count} records for files no longer on disk")
            return deleted_count
            
        except Exception as e:
            logger.error(f"Error cleaning up deleted files: {str(e)}")
            if conn:
                conn.rollback()
            return 0
        finally:
            if conn:
                conn.close()
    
    def scan_and_populate(self, batch_size=100, skip_existing=True, cleanup_deleted=True):
        """Main function to scan directory and populate database"""
        logger.info("Starting PDF file scan and database population")
        
        # Step 0: Clean up deleted files if requested
        deleted_count = 0
        if cleanup_deleted:
            logger.info("Step 1: Cleaning up records for deleted files...")
            deleted_count = self.cleanup_deleted_files()
        
        # Get existing files if we want to skip them
        existing_files = set()
        if skip_existing:
            existing_files = self.get_existing_files()
        
        # Step 2: Scan directory
        all_pdf_files = self.scan_pdf_directory()
        
        if not all_pdf_files:
            logger.warning("No PDF files found to process")
            return {
                'success': True,
                'files_processed': 0,
                'files_added': 0,
                'files_skipped': 0,
                'files_deleted': deleted_count
            }
        
        # Filter out existing files
        files_to_insert = []
        for file_info in all_pdf_files:
            self.files_processed += 1
            
            if skip_existing and file_info['filename'] in existing_files:
                self.files_skipped += 1
                if self.files_processed % 100 == 0:
                    logger.info(f"Processed {self.files_processed} files, skipped {self.files_skipped} existing files")
                continue
            
            files_to_insert.append(file_info)
        
        logger.info(f"Files to insert: {len(files_to_insert)}")
        logger.info(f"Files skipped (already exist): {self.files_skipped}")
        
        # Insert files in batches
        if files_to_insert:
            logger.info(f"Starting batch insertion of {len(files_to_insert)} files...")
            for i in range(0, len(files_to_insert), batch_size):
                batch = files_to_insert[i:i + batch_size]
                batch_inserted = self.insert_file_batch(batch)
                self.files_added += batch_inserted
                
                logger.info(f"Batch {i//batch_size + 1}: Attempted {len(batch)} files, inserted {batch_inserted}, total added so far: {self.files_added}")
        else:
            logger.info("No new files to insert")
        
        # Final summary
        logger.info("=" * 50)
        logger.info("PDF File Scan Complete")
        logger.info("=" * 50)
        logger.info(f"Total files processed: {self.files_processed}")
        logger.info(f"Files added to database: {self.files_added}")
        logger.info(f"Files skipped (existing): {self.files_skipped}")
        if deleted_count > 0:
            logger.info(f"Files deleted (no longer on disk): {deleted_count}")
        
        return {
            'success': True,
            'files_processed': self.files_processed,
            'files_added': self.files_added,
            'files_skipped': self.files_skipped,
            'files_deleted': deleted_count
        }
    
    def show_directory_stats(self):
        """Show statistics about the PDF directory"""
        if not self.pdf_directory.exists():
            print(f"❌ PDF directory does not exist: {self.pdf_directory}")
            return
        
        print(f"📁 PDF Directory: {self.pdf_directory}")
        print("=" * 60)
        
        # Count files by extension
        file_counts = {}
        total_size = 0
        
        for file_path in self.pdf_directory.rglob("*"):
            if file_path.is_file():
                ext = file_path.suffix.lower()
                size = file_path.stat().st_size
                
                file_counts[ext] = file_counts.get(ext, 0) + 1
                total_size += size
        
        print("File counts by extension:")
        for ext, count in sorted(file_counts.items()):
            print(f"  {ext or '(no extension)'}: {count:,} files")
        
        print(f"\nTotal files: {sum(file_counts.values()):,}")
        print(f"Total size: {total_size:,} bytes ({total_size / 1024 / 1024:.1f} MB)")
        
        # PDF specific stats
        pdf_count = file_counts.get('.pdf', 0)
        print(f"\n📄 PDF files: {pdf_count:,}")
        
        if pdf_count > 0:
            print("\nSample PDF files:")
            pdf_files = list(self.pdf_directory.rglob("*.pdf"))[:5]
            for pdf_file in pdf_files:
                size_mb = pdf_file.stat().st_size / 1024 / 1024
                print(f"  {pdf_file.name} ({size_mb:.1f} MB)")
            
            if len(list(self.pdf_directory.rglob("*.pdf"))) > 5:
                print("  ... and more")

def main():
    """Main function with command line options"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Scan PDF directory and populate database table',
        epilog="""
Examples:
  python src/services/pdf_scanner.py                     # Scan and populate (skip existing)
  python src/services/pdf_scanner.py --force             # Scan and populate (include existing)  
  python src/services/pdf_scanner.py --stats             # Show directory statistics only
  python src/services/pdf_scanner.py --batch-size 50     # Use smaller batch size
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument('--force', action='store_true',
                       help='Insert all files, even if they already exist in database')
    parser.add_argument('--no-cleanup', action='store_true',
                       help='Skip cleanup of deleted files (default: cleanup enabled)')
    parser.add_argument('--cleanup-only', action='store_true',
                       help='Only cleanup deleted files, do not scan for new files')
    parser.add_argument('--stats', action='store_true',
                       help='Show directory statistics only (no database operations)')
    parser.add_argument('--batch-size', type=int, default=100,
                       help='Number of files to insert per batch (default: 100)')
    parser.add_argument('--verbose', action='store_true',
                       help='Enable verbose logging')
    
    args = parser.parse_args()
    
    # Set logging level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Load configuration
    try:
        config = Config()
        if not config.validate_config():
            print("❌ Configuration validation failed. Please check your .env file.")
            return 1
    except Exception as e:
        print(f"❌ Configuration error: {str(e)}")
        return 1
    
    # Create scanner
    scanner = PDFFileScanner(config)
    
    # Show stats only
    if args.stats:
        scanner.show_directory_stats()
        return 0
    
    # Cleanup only
    if args.cleanup_only:
        try:
            deleted_count = scanner.cleanup_deleted_files()
            print(f"\n✓ Cleanup completed successfully!")
            print(f"   Files deleted from database: {deleted_count:,}")
            return 0
        except Exception as e:
            print(f"\n✗ Cleanup failed: {str(e)}")
            return 1
    
    # Run scan and populate
    try:
        result = scanner.scan_and_populate(
            batch_size=args.batch_size,
            skip_existing=not args.force,
            cleanup_deleted=not args.no_cleanup
        )
        
        if result['success']:
            print("\n✅ Scan completed successfully!")
            print(f"   Files processed: {result['files_processed']:,}")
            print(f"   Files added: {result['files_added']:,}")
            print(f"   Files skipped: {result['files_skipped']:,}")
            if result.get('files_deleted', 0) > 0:
                print(f"   Files deleted: {result['files_deleted']:,}")
            return 0
        else:
            print("\n❌ Scan failed!")
            return 1
            
    except KeyboardInterrupt:
        print("\n⏹️  Scan interrupted by user")
        return 1
    except Exception as e:
        print(f"\n❌ Scan failed with error: {str(e)}")
        logger.exception("Detailed error information:")
        return 1

if __name__ == "__main__":
    sys.exit(main())