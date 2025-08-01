#!/usr/bin/env python3
"""
Full Pipeline Script for MinimBA Energy Certificate Data Processing
Orchestrates the complete workflow from data download to AI analysis
"""

import sys
import os
import time
import argparse
from datetime import datetime
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from config import get_config
from src.services.file_downloader import FileDownloader
from src.services.api_client import EnovaApiClient
from src.services.pdf_downloader import PDFDownloader
from src.services.pdf_scanner import PDFFileScanner
from src.services.pdf_processor import PDFTextProcessor
from src.services.text_cleaner import TextCleaningProcessor
from src.services.openai_service import OpenAIEnergyService
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class FullPipeline:
    """Orchestrates the complete energy certificate data processing pipeline"""
    
    def __init__(self, config):
        self.config = config
        self.start_time = datetime.now()
        self.results = {
            'download': {},
            'api_processing': {},
            'pdf_download': {},
            'pdf_scan': {},
            'pdf_processing': {},
            'text_cleaning': {},
            'openai_analysis': {}
        }
        
        # Initialize services
        self.file_downloader = FileDownloader(config)
        self.api_client = EnovaApiClient(config)
        self.pdf_downloader = PDFDownloader(config)
        self.pdf_scanner = PDFFileScanner(config)
        self.pdf_processor = PDFTextProcessor(config)
        self.text_cleaner = TextCleaningProcessor(config)
        self.openai_service = OpenAIEnergyService(config)
    
    def run_pipeline(self, year: int, force_download: bool = False, 
                    download_count: int = 10, pdf_count: int = 20, 
                    process_count: int = 50, clean_count: int = 100,
                    openai_limit: int = 20, prompt_column: str = "PROMPT_V5_NOR_BANK"):
        """
        Run the complete pipeline for a specific year
        
        Args:
            year: Year to process
            force_download: Force re-download of CSV files
            download_count: Number of PDFs to download
            pdf_count: Number of PDFs to process
            process_count: Number of text records to clean
            clean_count: Number of records to process with OpenAI
            openai_limit: Number of OpenAI prompts to process
            prompt_column: Prompt column to use for OpenAI analysis
        """
        logger.info("=" * 80)
        logger.info(f"🚀 Starting Full Pipeline for Year {year}")
        logger.info("=" * 80)
        logger.info(f"Start time: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info(f"Configuration: force_download={force_download}, download_count={download_count}")
        logger.info(f"PDF processing: pdf_count={pdf_count}, process_count={process_count}")
        logger.info(f"Text cleaning: clean_count={clean_count}")
        logger.info(f"OpenAI analysis: limit={openai_limit}, prompt_column={prompt_column}")
        
        try:
            # Step 1: Download CSV data
            self._step_download_csv(year, force_download)
            
            # Step 2: Process certificates through API
            self._step_api_processing(download_count)
            
            # Step 3: Download PDF files
            self._step_pdf_download(download_count)
            
            # Step 4: Scan PDF directory
            self._step_pdf_scan()
            
            # Step 5: Process PDF files (extract text)
            self._step_pdf_processing(pdf_count)
            
            # Step 6: Clean extracted text
            self._step_text_cleaning(clean_count)
            
            # Step 7: OpenAI analysis
            self._step_openai_analysis(openai_limit, prompt_column)
            
            # Final summary
            self._print_final_summary()
            
        except Exception as e:
            logger.error(f"Pipeline failed: {str(e)}")
            raise
    
    def _step_download_csv(self, year: int, force_download: bool):
        """Step 1: Download CSV data for the specified year"""
        logger.info("\n" + "=" * 60)
        logger.info("📥 STEP 1: Downloading CSV Data")
        logger.info("=" * 60)
        
        try:
            result = self.file_downloader.download_year_data(year, force_download=force_download)
            
            if result['success']:
                logger.info(f"✅ CSV download successful: {result.get('file_path', 'N/A')}")
                logger.info(f"   File size: {result.get('file_size', 0):,} bytes")
                logger.info(f"   Period: {result.get('from_date', 'N/A')} to {result.get('to_date', 'N/A')}")
                self.results['download'] = result
            else:
                logger.error(f"❌ CSV download failed: {result.get('error', 'Unknown error')}")
                self.results['download'] = result
                
        except Exception as e:
            logger.error(f"❌ CSV download step failed: {str(e)}")
            self.results['download'] = {'success': False, 'error': str(e)}
    
    def _step_api_processing(self, count: int):
        """Step 2: Process certificates through API"""
        logger.info("\n" + "=" * 60)
        logger.info("🔗 STEP 2: Processing Certificates Through API")
        logger.info("=" * 60)
        
        try:
            result = self.api_client.process_certificates(count)
            
            if result['success']:
                logger.info(f"✅ API processing successful")
                logger.info(f"   Certificates processed: {result.get('processed', 0)}")
                logger.info(f"   Success rate: {result.get('success_rate', 0):.1f}%")
                self.results['api_processing'] = result
            else:
                logger.error(f"❌ API processing failed: {result.get('error', 'Unknown error')}")
                self.results['api_processing'] = result
                
        except Exception as e:
            logger.error(f"❌ API processing step failed: {str(e)}")
            self.results['api_processing'] = {'success': False, 'error': str(e)}
    
    def _step_pdf_download(self, count: int):
        """Step 3: Download PDF files from certificate URLs"""
        logger.info("\n" + "=" * 60)
        logger.info("📄 STEP 3: Downloading PDF Files")
        logger.info("=" * 60)
        
        try:
            result = self.pdf_downloader.download_pdfs(count=count)
            
            if result['success']:
                logger.info(f"✅ PDF download successful")
                logger.info(f"   Attempted: {result.get('attempted', 0)}")
                logger.info(f"   Successful: {result.get('successful', 0)}")
                logger.info(f"   Failed: {result.get('failed', 0)}")
                logger.info(f"   Skipped: {result.get('skipped', 0)}")
                self.results['pdf_download'] = result
            else:
                logger.error(f"❌ PDF download failed: {result.get('error', 'Unknown error')}")
                self.results['pdf_download'] = result
                
        except Exception as e:
            logger.error(f"❌ PDF download step failed: {str(e)}")
            self.results['pdf_download'] = {'success': False, 'error': str(e)}
    
    def _step_pdf_scan(self):
        """Step 4: Scan PDF directory and populate database"""
        logger.info("\n" + "=" * 60)
        logger.info("🔍 STEP 4: Scanning PDF Directory")
        logger.info("=" * 60)
        
        try:
            result = self.pdf_scanner.scan_pdf_directory()
            
            if result['success']:
                logger.info(f"✅ PDF scan successful")
                logger.info(f"   Files processed: {result.get('total_files', 0)}")
                logger.info(f"   Files added: {result.get('files_added', 0)}")
                logger.info(f"   Files skipped: {result.get('files_skipped', 0)}")
                self.results['pdf_scan'] = result
            else:
                logger.error(f"❌ PDF scan failed: {result.get('error', 'Unknown error')}")
                self.results['pdf_scan'] = result
                
        except Exception as e:
            logger.error(f"❌ PDF scan step failed: {str(e)}")
            self.results['pdf_scan'] = {'success': False, 'error': str(e)}
    
    def _step_pdf_processing(self, count: int):
        """Step 5: Process PDF files to extract text"""
        logger.info("\n" + "=" * 60)
        logger.info("📝 STEP 5: Processing PDF Files (Text Extraction)")
        logger.info("=" * 60)
        
        try:
            result = self.pdf_processor.process_pdfs(count=count)
            
            if result['success']:
                logger.info(f"✅ PDF processing successful")
                logger.info(f"   Files processed: {result.get('processed', 0)}")
                logger.info(f"   Success rate: {result.get('success_rate', 0):.1f}%")
                self.results['pdf_processing'] = result
            else:
                logger.error(f"❌ PDF processing failed: {result.get('error', 'Unknown error')}")
                self.results['pdf_processing'] = result
                
        except Exception as e:
            logger.error(f"❌ PDF processing step failed: {str(e)}")
            self.results['pdf_processing'] = {'success': False, 'error': str(e)}
    
    def _step_text_cleaning(self, count: int):
        """Step 6: Clean extracted text using regex patterns"""
        logger.info("\n" + "=" * 60)
        logger.info("🧹 STEP 6: Cleaning Extracted Text")
        logger.info("=" * 60)
        
        try:
            result = self.text_cleaner.clean_text_records(count=count)
            
            if result['success']:
                logger.info(f"✅ Text cleaning successful")
                logger.info(f"   Records processed: {result.get('processed', 0)}")
                logger.info(f"   Success rate: {result.get('success_rate', 0):.1f}%")
                self.results['text_cleaning'] = result
            else:
                logger.error(f"❌ Text cleaning failed: {result.get('error', 'Unknown error')}")
                self.results['text_cleaning'] = result
                
        except Exception as e:
            logger.error(f"❌ Text cleaning step failed: {str(e)}")
            self.results['text_cleaning'] = {'success': False, 'error': str(e)}
    
    def _step_openai_analysis(self, limit: int, prompt_column: str):
        """Step 7: Process energy certificates with OpenAI API"""
        logger.info("\n" + "=" * 60)
        logger.info("🤖 STEP 7: OpenAI Analysis")
        logger.info("=" * 60)
        
        try:
            result = self.openai_service.process_prompts(prompt_column, limit)
            
            if result['success']:
                logger.info(f"✅ OpenAI analysis successful")
                logger.info(f"   Prompts processed: {result.get('processed', 0)}")
                logger.info(f"   Success rate: {result.get('success_rate', 0):.1f}%")
                self.results['openai_analysis'] = result
            else:
                logger.error(f"❌ OpenAI analysis failed: {result.get('error', 'Unknown error')}")
                self.results['openai_analysis'] = result
                
        except Exception as e:
            logger.error(f"❌ OpenAI analysis step failed: {str(e)}")
            self.results['openai_analysis'] = {'success': False, 'error': str(e)}
    
    def _print_final_summary(self):
        """Print final pipeline summary"""
        end_time = datetime.now()
        duration = end_time - self.start_time
        
        logger.info("\n" + "=" * 80)
        logger.info("🎉 PIPELINE COMPLETE - FINAL SUMMARY")
        logger.info("=" * 80)
        logger.info(f"Start time: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info(f"End time: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info(f"Total duration: {duration}")
        
        # Summary of each step
        steps = [
            ("📥 CSV Download", self.results['download']),
            ("🔗 API Processing", self.results['api_processing']),
            ("📄 PDF Download", self.results['pdf_download']),
            ("🔍 PDF Scan", self.results['pdf_scan']),
            ("📝 PDF Processing", self.results['pdf_processing']),
            ("🧹 Text Cleaning", self.results['text_cleaning']),
            ("🤖 OpenAI Analysis", self.results['openai_analysis'])
        ]
        
        for step_name, result in steps:
            if result.get('success'):
                logger.info(f"✅ {step_name}: SUCCESS")
            else:
                logger.info(f"❌ {step_name}: FAILED - {result.get('error', 'Unknown error')}")
        
        logger.info("=" * 80)

def main():
    """Main entry point for the pipeline script"""
    parser = argparse.ArgumentParser(
        description="Run the complete MinimBA Energy Certificate Data Processing Pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/run_full_pipeline.py 2025                    # Process 2025 data with defaults
  python scripts/run_full_pipeline.py 2025 --force            # Force re-download CSV
  python scripts/run_full_pipeline.py 2025 --download-count 50 --pdf-count 100  # Custom counts
  python scripts/run_full_pipeline.py 2025 --openai-limit 50 --prompt-column PROMPT_V2_NOR
        """
    )
    
    parser.add_argument('year', type=int, help='Year to process (e.g., 2025)')
    parser.add_argument('--force', action='store_true', help='Force re-download of CSV files')
    parser.add_argument('--download-count', type=int, default=10, help='Number of PDFs to download (default: 10)')
    parser.add_argument('--pdf-count', type=int, default=20, help='Number of PDFs to process (default: 20)')
    parser.add_argument('--process-count', type=int, default=50, help='Number of text records to clean (default: 50)')
    parser.add_argument('--clean-count', type=int, default=100, help='Number of records to process with OpenAI (default: 100)')
    parser.add_argument('--openai-limit', type=int, default=20, help='Number of OpenAI prompts to process (default: 20)')
    parser.add_argument('--prompt-column', type=str, default='PROMPT_V5_NOR_BANK', 
                       help='Prompt column to use for OpenAI analysis (default: PROMPT_V5_NOR_BANK)')
    
    args = parser.parse_args()
    
    try:
        # Load configuration
        config = get_config()
        
        # Create and run pipeline
        pipeline = FullPipeline(config)
        pipeline.run_pipeline(
            year=args.year,
            force_download=args.force,
            download_count=args.download_count,
            pdf_count=args.pdf_count,
            process_count=args.process_count,
            clean_count=args.clean_count,
            openai_limit=args.openai_limit,
            prompt_column=args.prompt_column
        )
        
    except KeyboardInterrupt:
        logger.info("\n⚠️ Pipeline interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"❌ Pipeline failed: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
