"""
File Download Service for Norwegian Energy Certificate Data
Handles downloading CSV files from Enova's API
"""

import requests
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional
import os
import time
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

logger = logging.getLogger(__name__)

class FileDownloader:
    """Service for downloading files from Enova API"""
    
    def __init__(self, config):
        self.config = config
        self.base_url = config.ENOVA_API_BASE_URL + "/Fil"
        self.session = self._setup_session()
        self.download_count = 0
        self.api_call_count = 0
    
    def _setup_session(self):
        """Setup requests session with retry strategy and headers"""
        session = requests.Session()
        
        # Configure retry strategy
        retry_strategy = Retry(
            total=self.config.ENOVA_API_RETRY_COUNT,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        # Set headers including API key from config
        headers = {
            'User-Agent': 'MinimBA-EnergyData-Processor/1.0',
            'Accept': 'application/json',
            'Content-Type': 'application/json',
            'Cache-Control': 'no-cache'
        }
        
        # Add API key if configured
        if self.config.ENOVA_API_KEY:
            headers['x-api-key'] = self.config.ENOVA_API_KEY
        
        session.headers.update(headers)
        return session
    
    def download_year_data(self, year: int, output_dir: str = None, force_download: bool = False) -> Dict[str, Any]:
        """
        Download CSV data for a specific year from Enova API
        
        Args:
            year: Year to download data for
            output_dir: Directory to save the file (optional)
            force_download: Force download even if file exists
            
        Returns:
            Dictionary with download results and metadata
        """
        try:
            # Add delay before API call (rate limiting)
            if self.api_call_count > 0:
                time.sleep(self.config.ENOVA_API_DELAY)
            
            # Step 1: Get the file URL from the API
            logger.info(f"Requesting file information for year {year}")
            api_url = f"{self.base_url}/{year}"
            
            response = self.session.get(api_url, timeout=self.config.ENOVA_API_TIMEOUT)
            self.api_call_count += 1
            
            # Handle rate limiting
            if response.status_code == 429:
                logger.warning(f"Rate limited on year {year}, waiting 60 seconds...")
                time.sleep(60)
                response = self.session.get(api_url, timeout=self.config.ENOVA_API_TIMEOUT)
                self.api_call_count += 1
            
            response.raise_for_status()
            
            data = response.json()
            
            # Extract information from API response
            from_date = data.get('fromDate')
            to_date = data.get('toDate')
            bank_file_url = data.get('bankFileUrl')
            
            if not bank_file_url:
                return {
                    'success': False,
                    'error': 'No bankFileUrl found in API response',
                    'api_response': data
                }
            
            logger.info(f"Found data file for period: {from_date} to {to_date}")
            
            # Step 2: Determine output file path
            if not output_dir:
                output_dir = self.config.DOWNLOAD_CSV_PATH
            
            output_path = Path(output_dir)
            output_path.mkdir(parents=True, exist_ok=True)
            
            # Create filename based on the actual CSV filename from URL
            filename = self._extract_filename_from_url(bank_file_url, year, from_date, to_date)
            file_path = output_path / filename
            
            # Step 3: Check if file already exists
            if file_path.exists() and not force_download:
                file_size = file_path.stat().st_size
                logger.info(f"File already exists: {file_path} ({file_size} bytes) - skipping download")
                return {
                    'success': True,
                    'file_path': str(file_path),
                    'from_date': from_date,
                    'to_date': to_date,
                    'file_size': file_size,
                    'downloaded': False,
                    'message': 'File already exists (use --force to re-download)'
                }
            
            # Step 4: Download the CSV file
            logger.info(f"Downloading CSV file from: {bank_file_url}")
            csv_response = self.session.get(bank_file_url, stream=True, timeout=self.config.ENOVA_API_TIMEOUT)
            csv_response.raise_for_status()
            
            # Write file with progress logging
            total_size = int(csv_response.headers.get('content-length', 0))
            downloaded_size = 0
            
            with open(file_path, 'wb') as f:
                for chunk in csv_response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded_size += len(chunk)
                        
                        # Log progress for large files
                        if total_size > 0 and downloaded_size % (1024 * 1024) == 0:  # Every MB
                            progress = (downloaded_size / total_size) * 100
                            logger.info(f"Download progress: {progress:.1f}%")
            
            final_size = file_path.stat().st_size
            self.download_count += 1
            logger.info(f"Successfully downloaded: {file_path} ({final_size:,} bytes)")
            
            return {
                'success': True,
                'file_path': str(file_path),
                'from_date': from_date,
                'to_date': to_date,
                'file_size': final_size,
                'downloaded': True,
                'bank_file_url': bank_file_url
            }
            
        except requests.exceptions.RequestException as e:
            if hasattr(e.response, 'status_code') and e.response.status_code == 404:
                logger.info(f"No data available for year {year} (404 Not Found)")
                return {
                    'success': False,
                    'error': f'No data available for year {year}',
                    'status_code': 404
                }
            else:
                logger.error(f"HTTP request failed for year {year}: {str(e)}")
                return {
                    'success': False,
                    'error': f'HTTP request failed: {str(e)}'
                }
        except Exception as e:
            logger.error(f"Unexpected error during download for year {year}: {str(e)}")
            return {
                'success': False,
                'error': f'Unexpected error: {str(e)}'
            }
    
    def _extract_filename_from_url(self, url: str, year: int, from_date: str, to_date: str) -> str:
        """
        Extract filename from the bank file URL or generate a descriptive one
        
        Args:
            url: Bank file URL from API
            year: Year of the data
            from_date: Start date from API response
            to_date: End date from API response
            
        Returns:
            Filename for the downloaded CSV
        """
        try:
            # Try to extract filename from URL
            from urllib.parse import urlparse, parse_qs
            parsed_url = urlparse(url)
            
            # Check if there's a filename in the path
            path_parts = parsed_url.path.split('/')
            if path_parts and '.' in path_parts[-1]:
                original_filename = path_parts[-1]
                # Add year prefix to make it more descriptive
                return f"enova_{year}_{original_filename}"
            
            # Fallback to generating filename from dates
            return self._generate_filename(year, from_date, to_date)
            
        except Exception as e:
            logger.warning(f"Could not extract filename from URL: {e}")
            return self._generate_filename(year, from_date, to_date)

    def download_multiple_years(self, start_year: int, end_year: int = None, 
                               output_dir: str = None, force_download: bool = False) -> Dict[str, Any]:
        """
        Download CSV data for multiple years
        
        Args:
            start_year: Starting year (inclusive)
            end_year: Ending year (inclusive, optional - defaults to start_year)
            output_dir: Directory to save files (optional)
            force_download: Force download even if files exist
            
        Returns:
            Summary of download results
        """
        if end_year is None:
            end_year = start_year
        
        # Ensure start_year <= end_year
        if start_year > end_year:
            start_year, end_year = end_year, start_year
        
        results = {
            'total_years': end_year - start_year + 1,
            'successful_downloads': 0,
            'skipped_existing': 0,
            'failed_downloads': 0,
            'results': {},
            'start_time': time.time()
        }
        
        logger.info(f"Starting bulk download for years {start_year} to {end_year}")
        
        for year in range(start_year, end_year + 1):
            try:
                result = self.download_year_data(year, output_dir, force_download)
                results['results'][year] = result
                
                if result['success']:
                    if result.get('downloaded', False):
                        results['successful_downloads'] += 1
                    else:
                        results['skipped_existing'] += 1
                else:
                    results['failed_downloads'] += 1
                    
                # Log progress
                completed = year - start_year + 1
                total = results['total_years']
                logger.info(f"Progress: {completed}/{total} years processed")
                
            except Exception as e:
                logger.error(f"Error processing year {year}: {str(e)}")
                results['failed_downloads'] += 1
                results['results'][year] = {
                    'success': False,
                    'error': str(e)
                }
        
        results['end_time'] = time.time()
        results['total_time'] = results['end_time'] - results['start_time']
        results['total_api_calls'] = self.api_call_count
        results['total_files_downloaded'] = self.download_count
        
        # Log summary
        logger.info(f"Bulk download completed:")
        logger.info(f"  - Total years processed: {results['total_years']}")
        logger.info(f"  - Successful downloads: {results['successful_downloads']}")
        logger.info(f"  - Skipped (already exist): {results['skipped_existing']}")
        logger.info(f"  - Failed downloads: {results['failed_downloads']}")
        logger.info(f"  - Total time: {results['total_time']:.2f} seconds")
        logger.info(f"  - API calls made: {results['total_api_calls']}")
        
        return results
        """
        Generate a descriptive filename for the downloaded CSV
        
        Args:
            year: Year of the data
            from_date: Start date from API response
            to_date: End date from API response
            
        Returns:
            Generated filename
        """
        try:
            # Parse dates to create a clean filename
            from_dt = datetime.fromisoformat(from_date.replace('Z', '+00:00'))
            to_dt = datetime.fromisoformat(to_date.replace('Z', '+00:00'))
            
            from_str = from_dt.strftime('%Y%m%d')
            to_str = to_dt.strftime('%Y%m%d')
            
            return f"enova_certificates_{year}_{from_str}_{to_str}.csv"
            
        except Exception as e:
            logger.warning(f"Could not parse dates for filename: {e}")
            # Fallback to simple filename
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            return f"enova_certificates_{year}_{timestamp}.csv"
    
    def validate_csv_file(self, file_path: str) -> Dict[str, Any]:
        """
        Validate downloaded CSV file
        
        Args:
            file_path: Path to the CSV file
            
        Returns:
            Validation results
        """
        try:
            import pandas as pd
            
            # Read first few rows to validate structure
            df = pd.read_csv(file_path, nrows=5)
            
            return {
                'valid': True,
                'columns': list(df.columns),
                'row_count_sample': len(df),
                'file_size': Path(file_path).stat().st_size
            }
            
        except Exception as e:
            logger.error(f"CSV validation failed: {str(e)}")
            return {
                'valid': False,
                'error': str(e)
            }
    
    def get_download_status(self, year: int, output_dir: str = None) -> Dict[str, Any]:
        """
        Check if data for a specific year has already been downloaded
        
        Args:
            year: Year to check
            output_dir: Directory to check (optional)
            
        Returns:
            Status information
        """
        if not output_dir:
            output_dir = self.config.DOWNLOAD_CSV_PATH
        
        output_path = Path(output_dir)
        
        # Look for files matching the year pattern
        pattern = f"enova_certificates_{year}_*.csv"
        matching_files = list(output_path.glob(pattern))
        
        if matching_files:
            # Return info about the most recent file
            latest_file = max(matching_files, key=lambda f: f.stat().st_mtime)
            return {
                'downloaded': True,
                'file_path': str(latest_file),
                'file_size': latest_file.stat().st_size,
                'modified_time': datetime.fromtimestamp(latest_file.stat().st_mtime),
                'all_files': [str(f) for f in matching_files]
            }
        else:
            return {
                'downloaded': False,
                'message': f'No files found for year {year}'
            }

class DownloadProgress:
    """Helper class for tracking download progress"""
    
    def __init__(self, total_size: int):
        self.total_size = total_size
        self.downloaded = 0
        self.last_reported = 0
    
    def update(self, chunk_size: int):
        """Update progress and return if we should log"""
        self.downloaded += chunk_size
        
        if self.total_size > 0:
            progress = (self.downloaded / self.total_size) * 100
            
            # Report every 10% or every MB for large files
            report_threshold = max(10, (self.total_size * 0.1))
            
            if self.downloaded - self.last_reported >= report_threshold:
                self.last_reported = self.downloaded
                return True, progress
        
        return False, 0