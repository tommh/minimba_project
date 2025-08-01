"""
PDF Download Service for Enova Energy Certificates
Downloads PDF files from URLs obtained via stored procedure
"""

import os
import sys
from pathlib import Path
from datetime import datetime
import pyodbc
import requests
import logging
from urllib.parse import urlparse
import time
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)

class PDFDownloader:
    """Downloads PDF files from Enova certificate URLs"""
    
    def __init__(self, config):
        self.config = config
        self.pdf_directory = Path(config.DOWNLOAD_PDF_PATH)
        self.session = self._setup_session()
        self.downloads_attempted = 0
        self.downloads_successful = 0
        self.downloads_failed = 0
        self.downloads_skipped = 0
        
        # Ensure download directory exists
        self.pdf_directory.mkdir(parents=True, exist_ok=True)
        
    def _setup_session(self):
        """Setup requests session with appropriate headers"""
        session = requests.Session()
        
        # Set headers to mimic a browser
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'application/pdf,application/octet-stream,*/*',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
        })
        
        # Configure timeout
        session.timeout = 60  # 60 seconds timeout
        
        return session
    
    def _get_database_connection(self):
        """Get database connection using configuration"""
        try:
            # Build connection string based on configuration
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
            
            logger.debug(f"Connecting to database: {self.config.DATABASE_SERVER}/{self.config.DATABASE_NAME}")
            return pyodbc.connect(conn_str)
            
        except Exception as e:
            logger.error(f"Database connection failed: {str(e)}")
            raise
    
    def get_urls_to_download(self, top_rows: int = 10) -> List[Dict[str, str]]:
        """Get PDF URLs to download from stored procedure"""
        conn = None
        try:
            conn = self._get_database_connection()
            cursor = conn.cursor()
            
            cursor.execute("{CALL ev_enova.Get_Enova_BLOB_url (?)}", top_rows)
            rows = cursor.fetchall()
            
            urls = []
            for row in rows:
                urls.append({
                    'url': row.attest_url,
                    'expected_filename': row.expected_filename
                })
            
            logger.info(f"Retrieved {len(urls)} URLs to download")
            return urls
            
        except Exception as e:
            logger.error(f"Error getting URLs from database: {str(e)}")
            return []
        finally:
            if conn:
                conn.close()
    
    def log_download_attempt(self, url: str, filename: str, status: str, status_message: str, 
                           file_size: Optional[int] = None, http_status_code: Optional[int] = None):
        """Log download attempt to database"""
        conn = None
        try:
            conn = self._get_database_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO [ev_enova].[PDF_Download_Log] 
                (attest_url, filename, download_date, status, status_message, file_size, http_status_code, created)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                url,
                filename,
                datetime.now(),
                status,
                status_message,
                file_size,
                http_status_code,
                datetime.now()
            ))
            
            conn.commit()
            logger.debug(f"Logged download attempt: {filename} - {status}")
            
        except Exception as e:
            logger.error(f"Error logging download attempt: {str(e)}")
        finally:
            if conn:
                conn.close()
    
    def extract_filename_from_url(self, url: str) -> str:
        """Extract filename from URL, handling various URL formats"""
        try:
            # Parse URL
            parsed = urlparse(url)
            
            # Get the path part
            path = parsed.path
            
            # Extract filename from path
            if '/' in path:
                filename = path.split('/')[-1]
            else:
                filename = path
            
            # Handle URLs with query parameters that might contain filename info
            if not filename or not filename.endswith('.pdf'):
                # Try to extract from query parameters
                from urllib.parse import parse_qs
                params = parse_qs(parsed.query)
                
                # Look for filename in various parameter names
                for param_name in ['filename', 'file', 'name', 'rscd']:
                    if param_name in params:
                        param_value = params[param_name][0]
                        if '.pdf' in param_value.lower():
                            # Extract filename from parameter value
                            if 'filename=' in param_value:
                                filename = param_value.split('filename=')[1].split(';')[0].strip('\"')
                            elif param_value.endswith('.pdf'):
                                filename = param_value
                            break
            
            # If still no valid filename, generate one from URL
            if not filename or not filename.endswith('.pdf'):
                # Use last part of path or generate from URL hash
                url_hash = str(hash(url))[-8:]  # Last 8 chars of hash
                filename = f"energiattest_{url_hash}.pdf"
            
            # Clean filename (remove invalid characters)
            invalid_chars = '<>:"/\\|?*'
            for char in invalid_chars:
                filename = filename.replace(char, '_')
            
            # Ensure .pdf extension
            if not filename.lower().endswith('.pdf'):
                filename += '.pdf'
                
            return filename
            
        except Exception as e:
            logger.warning(f"Error extracting filename from URL: {str(e)}")
            # Generate fallback filename
            url_hash = str(hash(url))[-8:]
            return f"energiattest_{url_hash}.pdf"
    
    def download_pdf(self, url: str, expected_filename: Optional[str] = None) -> bool:
        """Download a single PDF file"""
        filename = expected_filename or self.extract_filename_from_url(url)
        file_path = self.pdf_directory / filename
        
        # Check if file already exists
        if file_path.exists():
            existing_size = file_path.stat().st_size
            logger.info(f"File already exists: {filename} ({existing_size:,} bytes)")
            self.log_download_attempt(url, filename, "Already Exists", f"File already exists ({existing_size:,} bytes)", existing_size)
            self.downloads_skipped += 1
            return True
        
        try:
            logger.info(f"Downloading: {filename} from {url[:80]}...")
            
            # Make the request
            response = self.session.get(url, stream=True)
            response.raise_for_status()
            
            # Check content type
            content_type = response.headers.get('content-type', '').lower()
            if 'pdf' not in content_type and 'application/octet-stream' not in content_type:
                logger.warning(f"Unexpected content type: {content_type} for {filename}")
            
            # Get content length
            content_length = response.headers.get('content-length')
            expected_size = int(content_length) if content_length else None
            
            if expected_size:
                logger.debug(f"Expected file size: {expected_size:,} bytes")
                
                # Skip very large files (over 50MB)
                if expected_size > 50 * 1024 * 1024:
                    message = f"File too large: {expected_size:,} bytes (max 50MB)"
                    logger.warning(message)
                    self.log_download_attempt(url, filename, "File Too Large", message, expected_size, response.status_code)
                    self.downloads_failed += 1
                    return False
            
            # Download the file
            total_downloaded = 0
            with open(file_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        total_downloaded += len(chunk)
            
            # Verify download
            actual_size = file_path.stat().st_size
            
            if expected_size and actual_size != expected_size:
                logger.warning(f"Size mismatch: expected {expected_size:,}, got {actual_size:,} bytes")
            
            if actual_size < 1024:  # Less than 1KB is suspicious for a PDF
                logger.warning(f"Downloaded file is very small: {actual_size} bytes")
                
                # Check if it's actually an error page
                with open(file_path, 'rb') as f:
                    content_start = f.read(100)
                    if b'<html' in content_start.lower() or b'error' in content_start.lower():
                        file_path.unlink()  # Delete the invalid file
                        message = "Downloaded file appears to be an error page, not a PDF"
                        logger.error(message)
                        self.log_download_attempt(url, filename, "Invalid Content", message, actual_size, response.status_code)
                        self.downloads_failed += 1
                        return False
            
            logger.info(f"Successfully downloaded: {filename} ({actual_size:,} bytes)")
            self.log_download_attempt(url, filename, "Success", f"Downloaded successfully ({actual_size:,} bytes)", actual_size, response.status_code)
            self.downloads_successful += 1
            return True
            
        except requests.exceptions.RequestException as e:
            error_msg = f"HTTP request failed: {str(e)}"
            logger.error(f"Download failed for {filename}: {error_msg}")
            
            # Get status code if available
            status_code = getattr(e.response, 'status_code', None) if hasattr(e, 'response') else None
            
            self.log_download_attempt(url, filename, "HTTP Error", error_msg, http_status_code=status_code)
            self.downloads_failed += 1
            
            # Clean up partial download
            if file_path.exists():
                file_path.unlink()
                
            return False
            
        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
            logger.error(f"Download failed for {filename}: {error_msg}")
            self.log_download_attempt(url, filename, "Error", error_msg)
            self.downloads_failed += 1
            
            # Clean up partial download
            if file_path.exists():
                file_path.unlink()
                
            return False
    
    def download_pdfs(self, count: int = 10, delay: float = 1.0) -> Dict[str, Any]:
        """Download a batch of PDF files"""
        logger.info(f"Starting PDF download batch (max {count} files)")
        
        # Reset counters
        self.downloads_attempted = 0
        self.downloads_successful = 0
        self.downloads_failed = 0
        self.downloads_skipped = 0
        
        # Get URLs to download
        urls_to_download = self.get_urls_to_download(count)
        
        if not urls_to_download:
            logger.info("No URLs found to download")
            return {
                'success': True,
                'message': 'No URLs to download',
                'attempted': 0,
                'successful': 0,
                'failed': 0,
                'skipped': 0
            }
        
        # Download each file
        for i, url_info in enumerate(urls_to_download):
            url = url_info['url']
            expected_filename = url_info['expected_filename']
            
            logger.info(f"Processing {i+1}/{len(urls_to_download)}: {expected_filename}")
            
            self.downloads_attempted += 1
            success = self.download_pdf(url, expected_filename)
            
            # Add delay between downloads to be respectful
            if delay > 0 and i < len(urls_to_download) - 1:
                time.sleep(delay)
            
            # Progress reporting
            if (i + 1) % 10 == 0:
                logger.info(f"Progress: {i + 1}/{len(urls_to_download)} processed, {self.downloads_successful} successful")
        
        # Final summary
        logger.info("=" * 50)
        logger.info("PDF Download Batch Complete")
        logger.info("=" * 50)
        logger.info(f"URLs processed: {self.downloads_attempted}")
        logger.info(f"Downloads successful: {self.downloads_successful}")
        logger.info(f"Downloads failed: {self.downloads_failed}")
        logger.info(f"Downloads skipped (existing): {self.downloads_skipped}")
        
        return {
            'success': True,
            'message': 'Batch download completed',
            'attempted': self.downloads_attempted,
            'successful': self.downloads_successful,
            'failed': self.downloads_failed,
            'skipped': self.downloads_skipped
        } 