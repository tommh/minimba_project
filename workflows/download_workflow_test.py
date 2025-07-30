import requests
import time
import os
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from pathlib import Path

start = time.perf_counter()
download_count = 0
api_call_count = 0

# Configure session with retry strategy
session = requests.Session()
retry_strategy = Retry(
    total=3,
    backoff_factor=1,
    status_forcelist=[429, 500, 502, 503, 504],
)
adapter = HTTPAdapter(max_retries=retry_strategy)
session.mount("http://", adapter)
session.mount("https://", adapter)

# API configuration
base_url = "https://api.data.enova.no/ems/offentlige-data/v1/Fil"
headers = {
    "Content-Type": "application/json",
    "Cache-Control": "no-cache",
    "x-api-key": "f36a1754f10f47b487892998d48c47ff"
}

# Rate limiting configuration
REQUESTS_PER_SECOND = 2  # Adjust based on API limits
DELAY_BETWEEN_REQUESTS = 1.0 / REQUESTS_PER_SECOND

# Create downloads directory if it doesn't exist
downloads_dir = Path("downloads")
downloads_dir.mkdir(exist_ok=True)

# Loop through years from 2024 back to 2014
for year in range(2024, 2013, -1):  # 2024 down to 2014
    try:
        # Add delay before API call (except for first request)
        if api_call_count > 0:
            time.sleep(DELAY_BETWEEN_REQUESTS)
        
        url = f"{base_url}/{year}"
        print(f"Fetching data for year {year}...")
        
        response = session.get(url, headers=headers, timeout=30)
        api_call_count += 1
        
        # Handle rate limiting
        if response.status_code == 429:
            print(f"Rate limited on year {year}, waiting 60 seconds...")
            time.sleep(60)
            response = session.get(url, headers=headers, timeout=30)
            api_call_count += 1
        
        if response.status_code == 200:
            # Parse JSON response to get the CSV file URL
            try:
                data = response.json()
                bank_file_url = data.get('bankFileUrl')
                from_date = data.get('fromDate')
                to_date = data.get('toDate')
                
                if bank_file_url:
                    print(f"Found file URL for {year}: {from_date} to {to_date}")
                    
                    # Download the actual CSV file
                    csv_response = session.get(bank_file_url, timeout=30)
                    
                    if csv_response.status_code == 200:
                        # Save the CSV file
                        filename = f"enova_data_{year}.csv"
                        filepath = downloads_dir / filename
                        
                        with open(filepath, 'wb') as f:
                            f.write(csv_response.content)
                        
                        file_size = len(csv_response.content)
                        print(f"Successfully downloaded {filename} ({file_size:,} bytes)")
                        download_count += 1
                    else:
                        print(f"Failed to download CSV file for {year}. Status code: {csv_response.status_code}")
                else:
                    print(f"No bankFileUrl found in response for year {year}")
                    
            except ValueError as e:
                print(f"Failed to parse JSON response for year {year}: {e}")
                print(f"Response content: {response.text[:200]}...")
            
        elif response.status_code == 404:
            print(f"No data available for year {year} (404 Not Found)")
            
        else:
            print(f"Failed to fetch data for year {year}. Status code: {response.status_code}")
            if response.text:
                print(f"Error message: {response.text[:200]}...")
    
    except requests.exceptions.RequestException as e:
        print(f"Request error for year {year}: {e}")
    except Exception as e:
        print(f"General error for year {year}: {e}")

end = time.perf_counter()
total_time = end - start

print(f"\n=== Summary ===")
print(f"API calls made: {api_call_count}")
print(f"Files downloaded: {download_count}")
print(f"Total time: {total_time:.3f} sec")
print(f"Average per API call: {total_time/api_call_count:.4f} sec" if api_call_count else "N/A")
print(f"Files saved to: {downloads_dir.absolute()}")