# MinimBA Energy Certificate Processing System

A Python-based system for processing Norwegian energy certificate data from Enova's API.

## Features

✅ **Step 1 - Data Download**: Download CSV files containing energy certificate data by year  
✅ **Step 3 - API Processing**: Call Enova API to get detailed certificate information  
✅ **Step 7 - AI Analysis**: OpenAI integration for energy certificate text analysis  
⏳ **Steps 2, 4-6**: CSV import, PDF processing, text extraction, and parsing (coming next)

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

# Process energy certificates with OpenAI
python main.py openai --limit 20                # Process 20 prompts with OpenAI
python main.py openai --prompt-column PROMPT_V2_NOR --limit 10  # Use different prompt column
python main.py openai-stats                     # Show OpenAI processing statistics
python example_openai_usage.py                  # Alternative: Use example script
python test_openai_setup.py                     # Test OpenAI configuration

# Configuration
python main.py config                           # Show current config
```

## Architecture

```
src/
├── services/
│   ├── file_downloader.py     # Download CSV files from Enova API
│   ├── api_client.py          # Process certificates through detailed API
│   ├── openai_service.py      # OpenAI integration for text analysis
│   └── ...                    # More services coming
├── utils/
│── workflows/
sql/
├── create_tables.sql          # Database schema
└── sample_data.sql           # Test data
tests/
├── test_api_client.py        # API client testing
example_openai_usage.py       # OpenAI service usage example
test_openai_setup.py          # OpenAI configuration test
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

# OpenAI API
OPENAI_API_KEY=your-openai-api-key-here
OPENAI_MODEL=gpt-4o-mini
OPENAI_MAX_TOKENS=2000
OPENAI_TEMPERATURE=0.3

# LangSmith Tracing (Optional)
LANGSMITH_API_KEY=your-langsmith-api-key-here
LANGSMITH_ENDPOINT=https://api.smith.langchain.com
LANGSMITH_PROJECT=minimba-energy-certificates
LANGSMITH_TRACING_ENABLED=true

# File Storage
BASE_DATA_PATH=./data
```

## Database Tables

- `[ev_enova].[Certificate]` - Main certificate data (your source)
- `[ev_enova].[EnovaApi_Energiattest_url_log]` - API call logging
- `[ev_enova].[EnovaApi_Energiattest_url]` - Detailed API responses
- `[ev_enova].[SampleTestDataForOpenAI]` - Energy certificate prompts for AI analysis
- `[ev_enova].[OpenAIAnswers]` - Structured AI responses (AboutEstate, Positives, Evaluation)

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

### ✅ OpenAI Service (`openai_service.py`)
- Processes energy certificate prompts with OpenAI API
- Structured response parsing (AboutEstate, Positives, Evaluation)
- Database integration for storing AI analysis results
- Rate limiting and error handling
- Comprehensive logging and statistics
- Support for multiple prompt versions (PROMPT_V1_NOR, PROMPT_V2_NOR)
- **LangSmith tracing integration** for monitoring and debugging OpenAI calls

### ✅ Testing Framework
- Comprehensive API client testing
- Database connection verification
- Step-by-step testing workflow
- OpenAI service testing and examples

## Coming Next

- **Step 2**: CSV import to database
- **Step 4**: PDF download and file management  
- **Step 5**: PDF text extraction using docling
- **Step 6**: Text cleaning with regex
- **Web interface**: Optional Flask/FastAPI dashboard

## Development

```bash
# Test individual components
python tests/test_api_client.py --test-connection
python tests/test_api_client.py --test-procedure --rows 3
python tests/test_api_client.py --test-api
python tests/test_api_client.py --full --rows 5

# Test OpenAI service
python main.py openai --limit 5                 # Test with 5 prompts
python main.py openai-stats                     # Check processing statistics
python test_openai_setup.py                     # Test configuration
python test_langsmith_setup.py                  # Test LangSmith integration
python example_openai_usage.py                  # Alternative test script

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

$ python main.py openai --limit 10
Processing 10 prompts with OpenAI using column: PROMPT_V1_NOR...
✓ OpenAI processing completed successfully
  Total prompts: 10
  Successfully processed: 10
  Errors: 0
  Processing time: 25.3 seconds
  Success rate: 100.0%

$ python main.py openai-stats
OpenAI Processing Statistics:
==================================================
Prompt Version: PROMPT_V1_NOR
  Total responses: 25
  First processed: 2024-01-15 10:30:00
  Last processed: 2024-01-15 14:45:00
  Completion rates:
    About Estate: 100.0%
    Positives: 96.0%
    Evaluation: 92.0%
```

## Requirements

- Python 3.8+
- SQL Server 2019+ (tested with SQL Server 2025)
- ODBC Driver 17 for SQL Server
- Enova API key
- Windows (for trusted connection) or SQL authentication

## Documentation

- **Main README**: This file - overview and quick start
- **[OpenAI Service Guide](README_OpenAI_Service.md)**: Detailed documentation for the OpenAI integration
- **[PDF Scanner Guide](PDF_SCANNER_GUIDE.md)**: PDF processing and scanning
- **[PDF Processor Guide](PDF_PROCESSOR_GUIDE.md)**: PDF text extraction and processing
- **[PDF Downloader Guide](PDF_DOWNLOADER_GUIDE.md)**: PDF file downloading
- **[Text Cleaner Guide](TEXT_CLEANER_GUIDE.md)**: Text cleaning and preprocessing

## License

This project is for internal use with Enova's public API. Please respect API rate limits and terms of service.
