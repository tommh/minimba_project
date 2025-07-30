# MinimBA Energy Certificate Processing System

A Python-based system for processing Norwegian energy certificate data from Enova's API.

## Features

✅ **Step 1 - Data Download**: Download CSV files containing energy certificate data by year  
🔄 **Step 3 - API Processing**: Call Enova API to get detailed certificate information  
⏳ **Steps 2, 4-7**: CSV import, PDF processing, text extraction, parsing, and AI analysis (coming next)

## Quick Start

### 1. Setup Environment

```bash
# Clone the repository
git clone https://github.com/tommh/minimba_project.git
cd minimba_project

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your database and API settings
```

### 2. Database Setup

```sql
-- Run in SQL Server Management Studio
-- 1. Create database: EnergyCertificate
-- 2. Run: sql/create_tables.sql
-- 3. Optionally run: sql/sample_data.sql (for testing)
```

### 3. Verify Setup

```bash
python setup.py
```

### 4. Usage Examples

```bash
# Download energy certificate data
python main.py download 2025                    # Download 2025 data
python main.py download 2020 2025               # Download range
python main.py list                             # List downloaded files

# Process certificates through API
python main.py api --rows 10                    # Process 10 certificates
python tests/test_api_client.py --rows 5        # Test API with 5 rows

# Configuration
python main.py config                           # Show current config
```

## Architecture

```
src/
├── services/
│   ├── file_downloader.py     # Download CSV files from Enova API
│   ├── api_client.py          # Process certificates through detailed API
│   └── ...                    # More services coming
├── utils/
│── workflows/
sql/
├── create_tables.sql          # Database schema
└── sample_data.sql           # Test data
tests/
├── test_api_client.py        # API client testing
```

## Configuration (.env)

```bash
# Database (SQL Server 2025)
DATABASE_SERVER=YOUR_SERVER\\INSTANCE
DATABASE_NAME=EnergyCertificate
DATABASE_TRUSTED_CONNECTION=yes

# Enova API
ENOVA_API_KEY=your-api-key-here
ENOVA_API_BASE_URL=https://api.data.enova.no/ems/offentlige-data/v1

# File Storage
BASE_DATA_PATH=./data
```

## Database Tables

- `[ev_enova].[Certificate]` - Main certificate data (your source)
- `[ev_enova].[EnovaApi_Energiattest_url_log]` - API call logging
- `[ev_enova].[EnovaApi_Energiattest_url]` - Detailed API responses

## API Workflow

1. **Get Parameters**: Call `[ev_enova].[Get_Enova_API_Parameters]` stored procedure
2. **Log Calls**: Record all API parameters for tracking
3. **API Calls**: Call Enova Energiattest API with certificate parameters
4. **Store Results**: Save detailed energy certificate data
5. **Progress Tracking**: Monitor processing with statistics

## What's Working Now

### ✅ File Downloader (`file_downloader.py`)
- Downloads yearly CSV files from Enova API
- Handles rate limiting and retries
- Skips existing files, force re-download option
- Progress reporting and error handling

### ✅ API Client (`api_client.py`)
- Retrieves certificate parameters from database
- Calls Enova Energiattest API for detailed data
- Logs all API calls for tracking
- Stores comprehensive energy certificate information
- Batch processing with configurable row counts
- Rate limiting and error handling

### ✅ Main CLI (`main.py`)
- Command-line interface for all operations
- Download management
- API processing
- Configuration display

### ✅ Testing Framework
- Comprehensive API client testing
- Database connection verification
- Step-by-step testing workflow

## Coming Next

- **Step 2**: CSV import to database
- **Step 4**: PDF download and file management  
- **Step 5**: PDF text extraction using docling
- **Step 6**: Text cleaning with regex
- **Step 7**: OpenAI integration for analysis
- **Web interface**: Optional Flask/FastAPI dashboard

## Development

```bash
# Test individual components
python tests/test_api_client.py --test-connection
python tests/test_api_client.py --test-procedure --rows 3
python tests/test_api_client.py --test-api
python tests/test_api_client.py --full --rows 5

# Run setup verification
python setup.py
```

## Example Output

```bash
$ python main.py api --rows 3
Processing 3 certificates through API...
✓ API processing completed successfully
  Parameters logged: 3
  API calls made: 3
  Records inserted: 8
  Processing time: 2.147 seconds
  Avg time per API call: 0.7157 seconds
```

## Requirements

- Python 3.8+
- SQL Server 2019+ (tested with SQL Server 2025)
- ODBC Driver 17 for SQL Server
- Enova API key
- Windows (for trusted connection) or SQL authentication

## License

This project is for internal use with Enova's public API. Please respect API rate limits and terms of service.
