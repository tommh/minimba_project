"""
File Download Service for Norwegian Energy Certificate Data
Simplified version for direct import
"""

import requests
import time
import os
from pathlib import Path
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from datetime import datetime
from typing import Dict, Any

class FileDownloader:
    """Service for downloading Certificate data files from Enova API"""
    
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
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        # Use the exact same headers that worked in your original code
        headers = {
            "Content-Type": "application/json",
            "Cache-Control": "no-cache"
        }
        
        # Add API key using x-api-key header (as in your working code)
        if self.config.ENOVA_API_KEY:
            headers["x-api-key"] = self.config.ENOVA_API_KEY
        
        session.headers.update(headers)
        return session
    
    def download_year_data(self, year: int, output_dir: str = None, force_download: bool = False) -> Dict[str, Any]:
        """
        Download CSV data for a specific year from Enova API
        """
        try:
            # Rate limiting
            if self.api_call_count > 0:
                time.sleep(0.5)  # Default delay
            
            # Step 1: Get the file URL from the API
            print(f"Requesting file information for year {year}...")
            api_url = f"{self.base_url}/{year}"
            
            response = self.session.get(api_url, timeout=30)
            self.api_call_count += 1
            
            # Handle rate limiting
            if response.status_code == 429:
                print(f"Rate limited on year {year}, waiting 60 seconds...")
                time.sleep(60)
                response = self.session.get(api_url, timeout=30)
                self.api_call_count += 1
            
            if response.status_code == 404:
                return {
                    'success': False,
                    'error': f'No data available for year {year}',
                    'status_code': 404
                }
            
            response.raise_for_status()
            data = response.json()
            
            # Extract information from API response
            from_date = data.get('fromDate')
            to_date = data.get('toDate')
            bank_file_url = data.get('bankFileUrl')
            
            if not bank_file_url:
                return {
                    'success': False,
                    'error': 'No bankFileUrl found in API response'
                }
            
            print(f"Found data file for period: {from_date} to {to_date}")
            
            # Step 2: Determine output file path
            if not output_dir:
                output_dir = "./data/downloads/csv"
            
            output_path = Path(output_dir)
            output_path.mkdir(parents=True, exist_ok=True)
            
            # Create filename
            filename = f"enova_data_{year}.csv"
            file_path = output_path / filename
            
            # Step 3: Check if file already exists
            if file_path.exists() and not force_download:
                file_size = file_path.stat().st_size
                print(f"File already exists: {file_path} ({file_size:,} bytes) - skipping download")
                return {
                    'success': True,
                    'file_path': str(file_path),
                    'from_date': from_date,
                    'to_date': to_date,
                    'file_size': file_size,
                    'downloaded': False,
                    'message': 'File already exists'
                }
            
            # Step 4: Download the CSV file
            print(f"Downloading CSV file from: {bank_file_url}")
            csv_response = self.session.get(bank_file_url, timeout=30)
            csv_response.raise_for_status()
            
            # Write file
            with open(file_path, 'wb') as f:
                f.write(csv_response.content)
            
            final_size = file_path.stat().st_size
            self.download_count += 1
            print(f"Successfully downloaded: {file_path} ({final_size:,} bytes)")
            
            return {
                'success': True,
                'file_path': str(file_path),
                'from_date': from_date,
                'to_date': to_date,
                'file_size': final_size,
                'downloaded': True
            }
            
        except requests.exceptions.RequestException as e:
            return {
                'success': False,
                'error': f'HTTP request failed: {str(e)}'
            }
        except Exception as e:
            return {
                'success': False,
                'error': f'Unexpected error: {str(e)}'
            }