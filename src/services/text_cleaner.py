#!/usr/bin/env python3
"""
PDF Text Cleaner Service
Cleans extracted PDF text using regex patterns and stores results in database
"""

import os
import sys
import re
import unicodedata
from pathlib import Path
from datetime import datetime
import pyodbc
import logging
from multiprocessing import Pool, cpu_count
import time
from typing import List, Optional

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


class PDFTextCleaner:
    """Enhanced PDF text cleaner with comprehensive regex patterns"""
    
    def __init__(self):
        # Common PDF artifacts and unwanted patterns
        self.unwanted_patterns = [
            r'\f',  # Form feed characters
            r'\x0c',  # Page break characters
            r'^\s*\d+\s*$',  # Standalone page numbers
            r'^\s*Page\s+\d+\s*$',  # "Page X" lines
            r'^\s*\d+\s*/\s*\d+\s*$',  # "X/Y" page indicators
            r'^\s*[\-_=]{3,}\s*$',  # Lines of dashes/underscores
            r'^\s*[•·▪▫■□▲△▼▽◆◇○●★☆]+\s*$',  # Bullet point artifacts
            r'(?:https?://|www\.)\S+',  # URLs (optional removal)
            r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',  # Email addresses
        ]
        
        # Headers/footers that commonly repeat
        self.header_footer_patterns = [
            r'^\s*(?:confidential|proprietary|draft|internal)\s*$',
            r'^\s*©.*$',  # Copyright lines
            r'^\s*\d{1,2}[-/]\d{1,2}[-/]\d{2,4}\s*$',  # Date-only lines
        ]
    
    def clean_text(self, text: str, 
                   remove_extra_whitespace: bool = True,
                   remove_page_artifacts: bool = True,
                   remove_headers_footers: bool = True,
                   min_line_length: int = 3,
                   preserve_structure: bool = True) -> str:
        """
        Clean PDF-converted text for LLM consumption
        
        Args:
            text: Raw PDF text
            remove_extra_whitespace: Remove excessive whitespace
            remove_page_artifacts: Remove page numbers, breaks, etc.
            remove_headers_footers: Remove common header/footer patterns
            min_line_length: Minimum line length to keep
            preserve_structure: Keep paragraph structure
        """
        if not text:
            return ""
        
        # Normalize Unicode characters
        text = unicodedata.normalize('NFKD', text)
        
        # Remove null bytes and control characters (except newlines/tabs)
        text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]', '', text)
        
        # Split into lines for line-by-line processing
        lines = text.split('\n')
        cleaned_lines = []
        
        for line in lines:
            original_line = line
            
            # Skip empty lines initially
            if not line.strip():
                if preserve_structure:
                    cleaned_lines.append("")
                continue
            
            # Remove page artifacts
            if remove_page_artifacts:
                skip_line = False
                for pattern in self.unwanted_patterns:
                    if re.match(pattern, line.strip(), re.IGNORECASE):
                        skip_line = True
                        break
                if skip_line:
                    continue
            
            # Remove headers/footers
            if remove_headers_footers:
                skip_line = False
                for pattern in self.header_footer_patterns:
                    if re.match(pattern, line.strip(), re.IGNORECASE):
                        skip_line = True
                        break
                if skip_line:
                    continue
            
            # Clean the line
            line = self._clean_line(line)
            
            # Skip lines that are too short after cleaning
            if len(line.strip()) < min_line_length:
                continue
            
            cleaned_lines.append(line)
        
        # Join lines back together
        result = '\n'.join(cleaned_lines)
        
        # Final cleanup
        if remove_extra_whitespace:
            result = self._remove_extra_whitespace(result)
        
        return result.strip()
    
    def _clean_line(self, line: str) -> str:
        """Clean individual line"""
        # Remove excessive spaces but preserve indentation
        line = re.sub(r'[ \t]{2,}', ' ', line)
        
        # Fix common OCR errors
        line = re.sub(r'([a-z])([A-Z])', r'\1 \2', line)  # Missing spaces
        line = re.sub(r'(\w)([.!?])(\w)', r'\1\2 \3', line)  # Missing spaces after punctuation
        
        # Remove isolated special characters
        line = re.sub(r'\s+[^\w\s]{1}\s+', ' ', line)
        
        # Clean up hyphenation artifacts
        line = re.sub(r'(\w)-\s*\n\s*(\w)', r'\1\2', line)
        
        return line
    
    def _remove_extra_whitespace(self, text: str) -> str:
        """Remove excessive whitespace while preserving structure"""
        # Remove multiple consecutive empty lines
        text = re.sub(r'\n\s*\n\s*\n', '\n\n', text)
        
        # Remove trailing whitespace from lines
        lines = text.split('\n')
        lines = [line.rstrip() for line in lines]
        
        return '\n'.join(lines)
    
    def remove_duplicate_lines(self, text: str, similarity_threshold: float = 0.9) -> str:
        """Remove duplicate or very similar lines (common in headers/footers)"""
        lines = text.split('\n')
        unique_lines = []
        
        for line in lines:
            if not line.strip():
                unique_lines.append(line)
                continue
                
            is_duplicate = False
            for existing_line in unique_lines[-10:]:  # Check last 10 lines
                if self._similarity(line.strip(), existing_line.strip()) > similarity_threshold:
                    is_duplicate = True
                    break
            
            if not is_duplicate:
                unique_lines.append(line)
        
        return '\n'.join(unique_lines)
    
    def _similarity(self, s1: str, s2: str) -> float:
        """Calculate similarity between two strings"""
        if not s1 or not s2:
            return 0.0
        
        set1 = set(s1.lower().split())
        set2 = set(s2.lower().split())
        
        if not set1 or not set2:
            return 0.0
        
        intersection = set1.intersection(set2)
        union = set1.union(set2)
        
        return len(intersection) / len(union)
    
    def extract_content_blocks(self, text: str) -> List[str]:
        """Split text into logical content blocks"""
        # Split on double newlines (paragraphs)
        blocks = re.split(r'\n\s*\n', text)
        
        # Filter out very short blocks
        content_blocks = []
        for block in blocks:
            cleaned_block = block.strip()
            if len(cleaned_block) > 20:  # Minimum block length
                content_blocks.append(cleaned_block)
        
        return content_blocks


class TextCleaningProcessor:
    """Main processor for cleaning extracted PDF text"""
    
    def __init__(self, config):
        self.config = config
        self.text_cleaner = PDFTextCleaner()
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
    
    def get_text_to_clean(self, top_rows=10):
        """Get text records that need cleaning"""
        conn = None
        try:
            conn = self.get_database_connection()
            cursor = conn.cursor()
            
            cursor.execute("{CALL ev_enova.Get_Text_To_Clean (?)}", top_rows)
            rows = cursor.fetchall()
            
            records = []
            for row in rows:
                records.append({
                    'file_id': row.file_id,
                    'extracted_text': row.extracted_text,
                    'character_count': row.character_count
                })
            
            logger.info(f"Retrieved {len(records)} text records to clean")
            return records
            
        except Exception as e:
            logger.error(f"Error getting text records from database: {str(e)}")
            return []
        finally:
            if conn:
                conn.close()
    
    def save_cleaned_text(self, file_id, cleaned_text):
        """Save cleaned text to database"""
        conn = None
        try:
            conn = self.get_database_connection()
            cursor = conn.cursor()
            
            cleaned_date = datetime.now()
            character_count = len(cleaned_text)
            
            cursor.execute("""
                INSERT INTO [ev_enova].[EnergyLabelCleanedText]
                ([file_id], [clean_text], [cleaned_date], [character_count])
                VALUES (?, ?, ?, ?)
            """, (
                file_id,
                cleaned_text,
                cleaned_date,
                character_count
            ))
            
            conn.commit()
            logger.debug(f"Saved cleaned text for file_id {file_id}: {character_count:,} characters")
            return True
            
        except Exception as e:
            logger.error(f"Error saving cleaned text for file_id {file_id}: {str(e)}")
            return False
        finally:
            if conn:
                conn.close()
    
    def clean_single_text(self, record, aggressive_cleaning=False):
        """Clean text from a single record"""
        file_id = record['file_id']
        extracted_text = record['extracted_text']
        original_char_count = record['character_count']
        
        logger.info(f"Cleaning text for file_id {file_id}: {original_char_count:,} characters")
        
        try:
            # Check if text is valid
            if not extracted_text or len(extracted_text.strip()) < 10:
                error_msg = f"Text too short or empty: {len(extracted_text) if extracted_text else 0} characters"
                logger.warning(error_msg)
                return False
            
            # Basic cleaning
            cleaned_text = self.text_cleaner.clean_text(
                extracted_text,
                remove_extra_whitespace=True,
                remove_page_artifacts=True,
                remove_headers_footers=True,
                min_line_length=3 if not aggressive_cleaning else 10,
                preserve_structure=not aggressive_cleaning
            )
            
            # Additional cleaning for aggressive mode
            if aggressive_cleaning:
                cleaned_text = self.text_cleaner.remove_duplicate_lines(cleaned_text)
                
                # Extract only substantial content blocks
                content_blocks = self.text_cleaner.extract_content_blocks(cleaned_text)
                cleaned_text = '\n\n'.join(content_blocks)
            
            # Validate cleaned text
            if not cleaned_text or len(cleaned_text.strip()) < 5:
                logger.warning(f"Cleaned text too short for file_id {file_id}")
                return False
            
            # Save to database
            success = self.save_cleaned_text(file_id, cleaned_text)
            if success:
                cleaned_char_count = len(cleaned_text)
                reduction_pct = ((original_char_count - cleaned_char_count) / original_char_count) * 100
                logger.info(f"Successfully cleaned file_id {file_id}: "
                          f"{original_char_count:,} → {cleaned_char_count:,} chars "
                          f"({reduction_pct:.1f}% reduction)")
                return True
            else:
                logger.error(f"Failed to save cleaned text for file_id {file_id}")
                return False
                
        except Exception as e:
            error_msg = f"Text cleaning failed: {str(e)}"
            logger.error(f"Error cleaning text for file_id {file_id}: {error_msg}")
            return False
    
    def process_batch_single_thread(self, top_rows=10, aggressive_cleaning=False):
        """Process text cleaning in single thread mode"""
        logger.info(f"Starting single-thread text cleaning (max {top_rows} records)")
        
        # Get records to process
        records_to_process = self.get_text_to_clean(top_rows)
        
        if not records_to_process:
            logger.info("No text records found to clean")
            return {
                'success': True,
                'message': 'No records to process',
                'files_processed': 0,
                'files_successful': 0,
                'files_failed': 0,
                'processing_time': 0
            }
        
        start_time = time.time()
        
        # Process each record
        for i, record in enumerate(records_to_process):
            self.files_processed += 1
            
            success = self.clean_single_text(record, aggressive_cleaning)
            if success:
                self.files_successful += 1
            else:
                self.files_failed += 1
            
            # Progress reporting
            if (i + 1) % 10 == 0:
                elapsed = time.time() - start_time
                rate = (i + 1) / elapsed if elapsed > 0 else 0
                logger.info(f"Progress: {i + 1}/{len(records_to_process)} records, {rate:.1f} records/min")
        
        end_time = time.time()
        processing_time = end_time - start_time
        
        # Final summary
        logger.info("=" * 50)
        logger.info("Text Cleaning Complete")
        logger.info("=" * 50)
        logger.info(f"Records processed: {self.files_processed}")
        logger.info(f"Successful cleanings: {self.files_successful}")
        logger.info(f"Failed cleanings: {self.files_failed}")
        logger.info(f"Processing time: {processing_time:.1f} seconds")
        if self.files_processed > 0:
            logger.info(f"Average time per record: {processing_time / self.files_processed:.1f} seconds")
        
        return {
            'success': True,
            'message': 'Processing completed',
            'files_processed': self.files_processed,
            'files_successful': self.files_successful,
            'files_failed': self.files_failed,
            'processing_time': processing_time
        }


def clean_single_text_multiprocess(text_data):
    """Process a single text record - designed for multiprocessing"""
    file_id, extracted_text, character_count, conn_str, aggressive_cleaning = text_data
    
    print(f"Process starting file_id {file_id}: {character_count:,} characters")
    
    try:
        # Create text cleaner
        text_cleaner = PDFTextCleaner()
        
        # Check if text is valid
        if not extracted_text or len(extracted_text.strip()) < 10:
            print(f"Text too short for file_id {file_id}")
            return False
        
        # Basic cleaning
        cleaned_text = text_cleaner.clean_text(
            extracted_text,
            remove_extra_whitespace=True,
            remove_page_artifacts=True,
            remove_headers_footers=True,
            min_line_length=3 if not aggressive_cleaning else 10,
            preserve_structure=not aggressive_cleaning
        )
        
        # Additional cleaning for aggressive mode
        if aggressive_cleaning:
            cleaned_text = text_cleaner.remove_duplicate_lines(cleaned_text)
            
            # Extract only substantial content blocks
            content_blocks = text_cleaner.extract_content_blocks(cleaned_text)
            cleaned_text = '\n\n'.join(content_blocks)
        
        # Validate cleaned text
        if not cleaned_text or len(cleaned_text.strip()) < 5:
            print(f"Cleaned text too short for file_id {file_id}")
            return False
        
        # Save to database
        if save_cleaned_text_multiprocess(conn_str, file_id, cleaned_text):
            cleaned_char_count = len(cleaned_text)
            reduction_pct = ((character_count - cleaned_char_count) / character_count) * 100
            print(f"Successfully cleaned file_id {file_id}: "
                  f"{character_count:,} → {cleaned_char_count:,} chars "
                  f"({reduction_pct:.1f}% reduction)")
            return True
        else:
            return False
            
    except Exception as e:
        print(f"Error cleaning text for file_id {file_id}: {str(e)}")
        return False


def save_cleaned_text_multiprocess(conn_str, file_id, cleaned_text):
    """Save cleaned text to database (multiprocessing version)"""
    try:
        conn = pyodbc.connect(conn_str)
        cursor = conn.cursor()
        
        cleaned_date = datetime.now()
        character_count = len(cleaned_text)
        
        cursor.execute("""
            INSERT INTO [ev_enova].[EnergyLabelCleanedText]
            ([file_id], [clean_text], [cleaned_date], [character_count])
            VALUES (?, ?, ?, ?)
        """, (
            file_id, cleaned_text, cleaned_date, character_count
        ))
        
        conn.commit()
        conn.close()
        return True
        
    except Exception as e:
        print(f"Error saving cleaned text for file_id {file_id}: {e}")
        return False


def process_text_cleaning_multiprocess(config, top_rows=10, num_processes=None, aggressive_cleaning=False):
    """Process text cleaning using multiprocessing"""
    logger.info(f"Starting multi-process text cleaning (max {top_rows} records)")
    
    # Create processor to get records
    processor = TextCleaningProcessor(config)
    records_to_process = processor.get_text_to_clean(top_rows)
    
    if not records_to_process:
        logger.info("No text records found to clean")
        return {
            'success': True,
            'message': 'No records to process',
            'files_processed': 0,
            'files_successful': 0,
            'files_failed': 0,
            'processing_time': 0
        }
    
    # Prepare data for multiprocessing
    conn_str = processor.get_connection_string()
    text_data = [(
        r['file_id'], 
        r['extracted_text'], 
        r['character_count'], 
        conn_str, 
        aggressive_cleaning
    ) for r in records_to_process]
    
    # Determine number of processes
    if num_processes is None:
        num_processes = min(cpu_count(), len(records_to_process), 8)  # Max 8 processes
    
    logger.info(f"Using {num_processes} processes for {len(records_to_process)} records")
    
    start_time = time.time()
    
    # Process with multiprocessing
    with Pool(processes=num_processes) as pool:
        results = pool.map(clean_single_text_multiprocess, text_data)
    
    end_time = time.time()
    processing_time = end_time - start_time
    
    # Calculate results
    files_successful = sum(results)
    files_failed = len(results) - files_successful
    
    # Final summary
    logger.info("=" * 50)
    logger.info("Text Cleaning Complete (Multiprocess)")
    logger.info("=" * 50)
    logger.info(f"Records processed: {len(records_to_process)}")
    logger.info(f"Successful cleanings: {files_successful}")
    logger.info(f"Failed cleanings: {files_failed}")
    logger.info(f"Processing time: {processing_time:.1f} seconds")
    logger.info(f"Average time per record: {processing_time / len(records_to_process):.1f} seconds")
    
    return {
        'success': True,
        'message': 'Processing completed',
        'files_processed': len(records_to_process),
        'files_successful': files_successful,
        'files_failed': files_failed,
        'processing_time': processing_time
    }


def main():
    """Main function with command line options"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Clean extracted PDF text using regex patterns',
        epilog="""
Examples:
  python src/services/text_cleaner.py                        # Clean 10 records (default)
  python src/services/text_cleaner.py --count 50             # Clean up to 50 records
  python src/services/text_cleaner.py --multiprocess         # Use multiprocessing
  python src/services/text_cleaner.py --aggressive           # Aggressive cleaning
  python src/services/text_cleaner.py --processes 4          # Use 4 processes
  python src/services/text_cleaner.py --verbose              # Verbose logging
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument('--count', type=int, default=10,
                       help='Number of records to process (default: 10)')
    parser.add_argument('--multiprocess', action='store_true',
                       help='Use multiprocessing for faster cleaning')
    parser.add_argument('--processes', type=int, default=None,
                       help='Number of processes to use (default: auto-detect)')
    parser.add_argument('--aggressive', action='store_true',
                       help='Use aggressive cleaning (removes more content)')
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
    
    # Run processing
    try:
        if args.multiprocess:
            result = process_text_cleaning_multiprocess(
                config, args.count, args.processes, args.aggressive
            )
        else:
            processor = TextCleaningProcessor(config)
            result = processor.process_batch_single_thread(args.count, args.aggressive)
        
        if result['success']:
            print(f"\n✅ Text cleaning completed!")
            print(f"   Records processed: {result['files_processed']:,}")
            print(f"   Successful cleanings: {result['files_successful']:,}")
            print(f"   Failed cleanings: {result['files_failed']:,}")
            print(f"   Processing time: {result['processing_time']:.1f} seconds")
            
            if result['files_processed'] > 0:
                success_rate = (result['files_successful'] / result['files_processed']) * 100
                rate = result['files_processed'] / result['processing_time'] if result['processing_time'] > 0 else 0
                print(f"   Success rate: {success_rate:.1f}%")
                print(f"   Processing rate: {rate:.1f} records/second")
            
            return 0
        else:
            print(f"\n❌ Text cleaning failed: {result.get('message', 'Unknown error')}")
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