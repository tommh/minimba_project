#!/usr/bin/env python3
"""
PDF Text Processor using Docling
Extracts text from PDF files and stores results in database
"""

import os
import sys
from pathlib import Path
from datetime import datetime
import pyodbc
import logging
from multiprocessing import Pool, cpu_count
import time

# Add project root to path
project_root = Path(__file__).parent.parent.parent  # Go up from src/services/ to project root
sys.path.insert(0, str(project_root))

from config import Config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class PDFTextProcessor:
    """Processes PDF files to extract text using Docling"""
    
    def __init__(self, config):
        self.config = config
        self.files_processed = 0
        self.files_successful = 0
        self.files_failed = 0
        
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
    
    def get_connection_string(self):
        """Get connection string for multiprocessing"""
        if self.config.DATABASE_TRUSTED_CONNECTION:
            return (
                f"DRIVER={{{self.config.DATABASE_DRIVER}}};"
                f"SERVER={self.config.DATABASE_SERVER};"
                f"DATABASE={self.config.DATABASE_NAME};"
                f"Trusted_Connection=yes;"
            )
        else:
            return (
                f"DRIVER={{{self.config.DATABASE_DRIVER}}};"
                f"SERVER={self.config.DATABASE_SERVER};"
                f"DATABASE={self.config.DATABASE_NAME};"
                f"UID={self.config.DATABASE_USERNAME};"
                f"PWD={self.config.DATABASE_PASSWORD};"
            )
    
    def get_pdf_files_to_process(self, top_rows=10):
        """Get PDF files that need text extraction"""
        conn = None
        try:
            conn = self.get_database_connection()
            cursor = conn.cursor()
            
            cursor.execute("{CALL ev_enova.Get_PDF_for_Extract (?)}", top_rows)
            rows = cursor.fetchall()
            
            files = []
            for row in rows:
                files.append({
                    'file_id': row.file_id,
                    'filename': row.filename,
                    'full_path': row.full_path
                })
            
            logger.info(f"Retrieved {len(files)} PDF files to process")
            return files
            
        except Exception as e:
            logger.error(f"Error getting PDF files from database: {str(e)}")
            return []
        finally:
            if conn:
                conn.close()
    
    def log_extraction_result(self, file_id, filename, extracted_text=None, page_count=None, 
                             status="SUCCESS", error_message=None):
        """Log extraction result to database"""
        conn = None
        try:
            conn = self.get_database_connection()
            cursor = conn.cursor()
            
            extraction_date = datetime.now()
            extraction_method = "docling.document_converter"
            
            if status == "SUCCESS" and extracted_text:
                character_count = len(extracted_text)
                final_text = extracted_text
            else:
                character_count = 0
                if error_message:
                    final_text = f"EXTRACTION FAILED: {error_message}"
                    status = "FAILED"
                else:
                    final_text = "EXTRACTION FAILED"
                    status = "FAILED"
            
            cursor.execute("""
                INSERT INTO [ev_enova].[EnergyLabelFileExtract]
                ([file_id], [filename], [extracted_text], [extraction_date], 
                 [extraction_method], [extraction_status], [character_count], [page_count])
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                file_id,
                filename,
                final_text,
                extraction_date,
                extraction_method,
                status,
                character_count,
                page_count
            ))
            
            conn.commit()
            logger.debug(f"Logged extraction result for file_id {file_id}: {status}")
            return True
            
        except Exception as e:
            logger.error(f"Error logging extraction result for file_id {file_id}: {str(e)}")
            return False
        finally:
            if conn:
                conn.close()
    
    def extract_text_from_pdf(self, file_info):
        """Extract text from a single PDF file"""
        file_id = file_info['file_id']
        filename = file_info['filename']
        full_path = file_info['full_path']
        
        logger.info(f"Processing file_id {file_id}: {filename}")
        
        # Convert to absolute path if needed
        if not Path(full_path).is_absolute():
            # Assume relative to project root
            file_path = Path(project_root) / full_path
        else:
            file_path = Path(full_path)
        
        # Check if file exists
        if not file_path.exists():
            error_msg = f"File not found: {file_path}"
            logger.error(error_msg)
            self.log_extraction_result(file_id, filename, status="FILE_NOT_FOUND", error_message=error_msg)
            return False
        
        # Check file size (skip very large files)
        file_size = file_path.stat().st_size
        max_size = 50 * 1024 * 1024  # 50MB limit
        if file_size > max_size:
            error_msg = f"File too large: {file_size:,} bytes (max {max_size:,} bytes)"
            logger.warning(error_msg)
            self.log_extraction_result(file_id, filename, status="FILE_TOO_LARGE", error_message=error_msg)
            return False
        
        # Extract text using Docling
        try:
            # Import docling here to handle import errors gracefully
            try:
                from docling.document_converter import DocumentConverter
            except ImportError as e:
                error_msg = f"Docling not available: {str(e)}. Please install with: pip install docling"
                logger.error(error_msg)
                self.log_extraction_result(file_id, filename, status="DOCLING_NOT_AVAILABLE", error_message=error_msg)
                return False
            
            logger.debug(f"Starting text extraction for {filename} ({file_size:,} bytes)")
            
            # Initialize converter and extract text
            converter = DocumentConverter()
            result = converter.convert(str(file_path))
            extracted_text = result.document.export_to_text()
            
            # Get page count if available
            page_count = None
            try:
                if hasattr(result.document, 'pages') and result.document.pages:
                    page_count = len(result.document.pages)
            except Exception as e:
                logger.debug(f"Could not get page count: {str(e)}")
                page_count = None
            
            # Validate extracted text
            if not extracted_text or len(extracted_text.strip()) < 10:
                error_msg = f"Extracted text too short ({len(extracted_text) if extracted_text else 0} chars)"
                logger.warning(error_msg)
                # Still log it as success but with a warning
                self.log_extraction_result(file_id, filename, extracted_text or "", page_count, 
                                         status="SUCCESS_LOW_CONTENT", error_message=error_msg)
                return True
            
            # Log successful extraction
            success = self.log_extraction_result(file_id, filename, extracted_text, page_count, "SUCCESS")
            if success:
                logger.info(f"Successfully extracted text from {filename}: {len(extracted_text):,} characters")
                return True
            else:
                logger.error(f"Failed to log extraction result for {filename}")
                return False
                
        except Exception as e:
            error_msg = f"Text extraction failed: {str(e)}"
            logger.error(f"Error extracting text from {filename}: {error_msg}")
            self.log_extraction_result(file_id, filename, status="EXTRACTION_ERROR", error_message=error_msg)
            return False
    
    def process_batch_single_thread(self, top_rows=10):
        """Process PDFs in single thread mode"""
        logger.info(f"Starting single-thread PDF text extraction (max {top_rows} files)")
        
        # Get files to process
        files_to_process = self.get_pdf_files_to_process(top_rows)
        
        if not files_to_process:
            logger.info("No PDF files found to process")
            return {
                'success': True,
                'message': 'No files to process',
                'files_processed': 0,
                'files_successful': 0,
                'files_failed': 0,
                'processing_time': 0
            }
        
        start_time = time.time()
        
        # Process each file
        for i, file_info in enumerate(files_to_process):
            self.files_processed += 1
            
            success = self.extract_text_from_pdf(file_info)
            if success:
                self.files_successful += 1
            else:
                self.files_failed += 1
            
            # Progress reporting
            if (i + 1) % 10 == 0:
                elapsed = time.time() - start_time
                rate = (i + 1) / elapsed if elapsed > 0 else 0
                logger.info(f"Progress: {i + 1}/{len(files_to_process)} files, {rate:.1f} files/min")
        
        end_time = time.time()
        processing_time = end_time - start_time
        
        # Final summary
        logger.info("=" * 50)
        logger.info("PDF Text Extraction Complete")
        logger.info("=" * 50)
        logger.info(f"Files processed: {self.files_processed}")
        logger.info(f"Successful extractions: {self.files_successful}")
        logger.info(f"Failed extractions: {self.files_failed}")
        logger.info(f"Processing time: {processing_time:.1f} seconds")
        if self.files_processed > 0:
            logger.info(f"Average time per file: {processing_time / self.files_processed:.1f} seconds")
        
        return {
            'success': True,
            'message': 'Processing completed',
            'files_processed': self.files_processed,
            'files_successful': self.files_successful,
            'files_failed': self.files_failed,
            'processing_time': processing_time
        }

def extract_single_pdf_multiprocess(pdf_data):
    """Process a single PDF - designed for multiprocessing"""
    file_id, filename, full_path, conn_str = pdf_data
    
    print(f"Process starting file_id {file_id}: {filename}")
    
    # Convert to absolute path if needed
    if not Path(full_path).is_absolute():
        # Assume relative to project root  
        file_path = Path(__file__).parent.parent.parent / full_path
    else:
        file_path = Path(full_path)
    
    # Check if file exists
    if not file_path.exists():
        error_msg = f"File not found: {file_path}"
        print(f"File not found: {file_path}")
        log_extraction_to_db_multiprocess(conn_str, file_id, filename, status="FILE_NOT_FOUND", error_message=error_msg)
        return False
    
    # Check file size
    file_size = file_path.stat().st_size
    max_size = 50 * 1024 * 1024  # 50MB limit
    if file_size > max_size:
        error_msg = f"File too large: {file_size:,} bytes"
        print(error_msg)
        log_extraction_to_db_multiprocess(conn_str, file_id, filename, status="FILE_TOO_LARGE", error_message=error_msg)
        return False
    
    # Extract text
    try:
        from docling.document_converter import DocumentConverter
        
        converter = DocumentConverter()
        result = converter.convert(str(file_path))
        extracted_text = result.document.export_to_text()
        
        # Get page count
        page_count = None
        try:
            if hasattr(result.document, 'pages') and result.document.pages:
                page_count = len(result.document.pages)
        except:
            page_count = None
        
        # Log successful extraction
        if log_extraction_to_db_multiprocess(conn_str, file_id, filename, extracted_text, page_count, "SUCCESS"):
            print(f"Successfully processed file_id {file_id}: {len(extracted_text):,} characters")
            return True
        else:
            return False
            
    except ImportError as e:
        error_msg = f"Docling not available: {str(e)}"
        print(error_msg)
        log_extraction_to_db_multiprocess(conn_str, file_id, filename, status="DOCLING_NOT_AVAILABLE", error_message=error_msg)
        return False
    except Exception as e:
        error_msg = f"Text extraction failed: {str(e)}"
        print(f"Error extracting text from {filename}: {error_msg}")
        log_extraction_to_db_multiprocess(conn_str, file_id, filename, status="EXTRACTION_ERROR", error_message=error_msg)
        return False

def log_extraction_to_db_multiprocess(conn_str, file_id, filename, extracted_text=None, page_count=None, 
                                     status="SUCCESS", error_message=None):
    """Log extraction result to database (multiprocessing version)"""
    try:
        conn = pyodbc.connect(conn_str)
        cursor = conn.cursor()
        
        extraction_date = datetime.now()
        extraction_method = "docling.document_converter"
        
        if status == "SUCCESS" and extracted_text:
            character_count = len(extracted_text)
            final_text = extracted_text
        else:
            character_count = 0
            if error_message:
                final_text = f"EXTRACTION FAILED: {error_message}"
                status = "FAILED"
            else:
                final_text = "EXTRACTION FAILED"
                status = "FAILED"
        
        cursor.execute("""
            INSERT INTO [ev_enova].[EnergyLabelFileExtract]
            ([file_id], [filename], [extracted_text], [extraction_date], 
             [extraction_method], [extraction_status], [character_count], [page_count])
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            file_id, filename, final_text, extraction_date,
            extraction_method, status, character_count, page_count
        ))
        
        conn.commit()
        conn.close()
        return True
        
    except Exception as e:
        print(f"Error logging extraction for file_id {file_id}: {e}")
        return False

def process_pdfs_multiprocess(config, top_rows=10, num_processes=None):
    """Process PDFs using multiprocessing"""
    logger.info(f"Starting multi-process PDF text extraction (max {top_rows} files)")
    
    # Create processor to get files
    processor = PDFTextProcessor(config)
    files_to_process = processor.get_pdf_files_to_process(top_rows)
    
    if not files_to_process:
        logger.info("No PDF files found to process")
        return {
            'success': True,
            'message': 'No files to process',
            'files_processed': 0,
            'files_successful': 0,
            'files_failed': 0,
            'processing_time': 0
        }
    
    # Prepare data for multiprocessing
    conn_str = processor.get_connection_string()
    pdf_data = [(f['file_id'], f['filename'], f['full_path'], conn_str) for f in files_to_process]
    
    # Determine number of processes
    if num_processes is None:
        num_processes = min(cpu_count(), len(files_to_process), 8)  # Max 8 processes
    
    logger.info(f"Using {num_processes} processes for {len(files_to_process)} files")
    
    start_time = time.time()
    
    # Process with multiprocessing
    with Pool(processes=num_processes) as pool:
        results = pool.map(extract_single_pdf_multiprocess, pdf_data)
    
    end_time = time.time()
    processing_time = end_time - start_time
    
    # Calculate results
    files_successful = sum(results)
    files_failed = len(results) - files_successful
    
    # Final summary
    logger.info("=" * 50)
    logger.info("PDF Text Extraction Complete (Multiprocess)")
    logger.info("=" * 50)
    logger.info(f"Files processed: {len(files_to_process)}")
    logger.info(f"Successful extractions: {files_successful}")
    logger.info(f"Failed extractions: {files_failed}")
    logger.info(f"Processing time: {processing_time:.1f} seconds")
    logger.info(f"Average time per file: {processing_time / len(files_to_process):.1f} seconds")
    
    return {
        'success': True,
        'message': 'Processing completed',
        'files_processed': len(files_to_process),
        'files_successful': files_successful,
        'files_failed': files_failed,
        'processing_time': processing_time
    }

def main():
    """Main function with command line options"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Extract text from PDF files using Docling',
        epilog="""
Examples:
  python src/services/pdf_processor.py                     # Process 10 PDFs (default)
  python src/services/pdf_processor.py --count 50          # Process up to 50 PDFs
  python src/services/pdf_processor.py --multiprocess      # Use multiprocessing
  python src/services/pdf_processor.py --processes 4       # Use 4 processes
  python src/services/pdf_processor.py --verbose           # Verbose logging
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument('--count', type=int, default=10,
                       help='Number of PDFs to process (default: 10)')
    parser.add_argument('--multiprocess', action='store_true',
                       help='Use multiprocessing for faster extraction')
    parser.add_argument('--processes', type=int, default=None,
                       help='Number of processes to use (default: auto-detect)')
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
    
    # Check if docling is available
    try:
        from docling.document_converter import DocumentConverter
        logger.info("✓ Docling is available")
    except ImportError:
        print("❌ Docling is not installed. Please install with: pip install docling")
        print("   Or install AI/ML dependencies: pip install -r requirements.txt")
        return 1
    
    # Run processing
    try:
        if args.multiprocess:
            result = process_pdfs_multiprocess(config, args.count, args.processes)
        else:
            processor = PDFTextProcessor(config)
            result = processor.process_batch_single_thread(args.count)
        
        if result['success']:
            print(f"\n✅ PDF text extraction completed!")
            print(f"   Files processed: {result['files_processed']:,}")
            print(f"   Successful extractions: {result['files_successful']:,}")
            print(f"   Failed extractions: {result['files_failed']:,}")
            print(f"   Processing time: {result['processing_time']:.1f} seconds")
            
            if result['files_processed'] > 0:
                success_rate = (result['files_successful'] / result['files_processed']) * 100
                rate = result['files_processed'] / result['processing_time'] if result['processing_time'] > 0 else 0
                print(f"   Success rate: {success_rate:.1f}%")
                print(f"   Processing rate: {rate:.1f} files/second")
            
            return 0
        else:
            print(f"\n❌ PDF processing failed: {result.get('message', 'Unknown error')}")
            return 1
            
    except KeyboardInterrupt:
        print("\n⏹️  Processing interrupted by user")
        return 1
    except Exception as e:
        print(f"\n❌ Processing failed with error: {str(e)}")
        logger.exception("Detailed error information:")
        return 1

if __name__ == "__main__":
    sys.exit(main())
