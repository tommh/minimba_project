# MinimBA Energy Certificate Processing System

An AI-powered energy certificate analysis system that downloads Norwegian building data, uses OpenAI to generate structured property insights, and provides comprehensive monitoring through LangSmith tracing.

## Features

✅ **Step 1 - Data Download**: Download CSV files containing energy certificate data by year  
✅ **Step 2 - CSV Import**: Import CSV data to database for processing with batch support  
✅ **Step 3 - API Processing**: Call Enova API to get detailed certificate information  
✅ **Step 4 - PDF Download**: Download PDF files from certificate URLs  
✅ **Step 5 - PDF Scan**: Scan PDF directory and populate database  
✅ **Step 6 - PDF Processing**: Extract text from PDF files using Docling  
✅ **Step 7 - Text Cleaning**: Clean extracted text using regex patterns  
✅ **Step 8 - AI Analysis**: OpenAI integration for energy certificate text analysis

## Quick Start

### 1. Setup Environment

```bash
# Clone the repository
git clone https://github.com/tommh/minimba_project.git
cd minimba_project

# Install production dependencies
pip install -r requirements.txt

# For development work, also install dev dependencies
pip install -r dev-requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your database and API settings
```

### 2. Database Setup

```bash
# 1. Create database in SQL Server Management Studio or command line
# CREATE DATABASE EnergyCertificate;

# 2. Deploy database schema and objects
cd database
python scripts/deploy.py

# 3. Optionally load reference data
python scripts/deploy_selective.py --files data/reference_data.sql

# 4. Validate deployment
python scripts/validate.py
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

# Import CSV data to database
python main.py import-csv 2025                  # Import 2025 CSV to database
python main.py import-csv 2020 2025             # Import 2020-2025 CSV files

# Process certificates through API
python main.py api --rows 10                    # Process 10 certificates
python tests/test_api_client.py --rows 5        # Test API with 5 rows

# PDF processing
python main.py scan-pdf                         # Scan PDF directory and populate database
python main.py download-pdf --count 20          # Download 20 PDF files
python main.py process-pdf --count 50           # Extract text from 50 PDF files
python main.py clean-text --count 100           # Clean 100 extracted text records

# Full pipeline
python scripts/run_full_pipeline.py 2025        # Run complete pipeline for 2025

# Process energy certificates with OpenAI
python main.py openai --limit 20                # Process 20 prompts with OpenAI
python main.py openai --prompt-column PROMPT_V2_NOR --limit 10  # Use different prompt column
python main.py openai-stats                     # Show OpenAI processing statistics
python examples/openai_usage_example.py         # Alternative: Use example script
python tests/test_openai_setup.py               # Test OpenAI configuration

# Configuration
python main.py config                           # Show current config
```

## Architecture

```
src/
├── services/
│   ├── file_downloader.py     # Download CSV files from Enova API
│   ├── csv_import_service.py   # CSV import management and batch processing
│   ├── csv_processor.py        # Internal CSV processing utilities
│   ├── api_client.py           # Process certificates through detailed API
│   ├── pdf_downloader.py       # Download PDF files from certificate URLs
│   ├── pdf_scanner.py          # Scan PDF directory and populate database
│   ├── pdf_processor.py        # Extract text from PDF files using Docling
│   ├── text_cleaner.py         # Clean extracted text using regex patterns
│   └── openai_service.py       # OpenAI integration for text analysis
├── utils/
├── workflows/
database/
├── schemas/                    # Schema creation scripts
├── schema/                     # Database objects (tables, views, procedures)
├── scripts/                    # Deployment and management scripts
├── migrations/                 # Database migration scripts
└── data/                       # Reference and seed data
tests/
├── test_api_client.py         # API client testing
├── test_csv_processor.py      # CSV processing tests
├── test_openai_setup.py       # OpenAI configuration test
└── test_langsmith_setup.py    # LangSmith integration test
examples/
├── openai_usage_example.py    # OpenAI service usage example
└── README.md                   # Examples documentation
tools/
├── diagnose_pdf_scanner.py    # PDF processing diagnostics
└── README.md                   # Tools documentation
scripts/
└── run_full_pipeline.py       # Complete pipeline orchestration
reports/
├── energy_certificate_analysis.pbix  # Power BI dashboard
├── templates/                  # Report templates
├── exports/                    # Exported reports
└── documentation/              # Report guides
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

## ✅ All Steps Implemented

🎉 **Complete Pipeline Available**: All 8 steps are now implemented and working!

- ✅ **Step 1**: Data Download - Download CSV files by year
- ✅ **Step 2**: CSV Import - Import CSV data to database
- ✅ **Step 3**: API Processing - Call Enova API for detailed information
- ✅ **Step 4**: PDF Download - Download PDF files from URLs
- ✅ **Step 5**: PDF Scan - Scan PDF directory and populate database
- ✅ **Step 6**: PDF Processing - Extract text from PDF files
- ✅ **Step 7**: Text Cleaning - Clean extracted text with regex
- ✅ **Step 8**: AI Analysis - OpenAI integration for analysis

### 🚀 Full Pipeline Usage
`ash
# Run complete pipeline for 2025
python scripts/run_full_pipeline.py 2025

# Customize pipeline parameters
python scripts/run_full_pipeline.py 2025 --download-count 50 --pdf-count 100

# Force re-download and custom OpenAI analysis
python scripts/run_full_pipeline.py 2025 --force --openai-limit 50
`

## Development

```bash
# Test individual components
python tests/test_api_client.py --test-connection
python tests/test_api_client.py --test-procedure --rows 3
python tests/test_api_client.py --test-api
python tests/test_api_client.py --full --rows 5

# Test individual services
python main.py scan-pdf                         # Test PDF scanning
python main.py download-pdf --count 5           # Test PDF downloading
python main.py process-pdf --count 5            # Test PDF text extraction
python main.py clean-text --count 10            # Test text cleaning

# Test CSV import functionality
python main.py import-csv 2025                  # Test CSV import
python src/services/csv_import_service.py --year 2025  # Direct service test

# Test OpenAI service
python main.py openai --limit 5                 # Test with 5 prompts
python main.py openai-stats                     # Check processing statistics
python tests/test_openai_setup.py               # Test configuration
python tests/test_langsmith_setup.py            # Test LangSmith integration
python examples/openai_usage_example.py         # Alternative test script

# Test database operations
python database/scripts/validate.py             # Validate database
python tools/diagnose_pdf_scanner.py            # Diagnose PDF issues

# Test full pipeline
python scripts/run_full_pipeline.py 2025 --download-count 5  # Test with small counts

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
- **[Reports Documentation](reports/README.md)**: Power BI reports and analytics

## 📊 Power BI Analytics

The project includes Power BI reports for visualizing OpenAI analysis results:

### Energy Certificate Analysis Dashboard
- **File**: `reports/energy_certificate_analysis.pbix`
- **Purpose**: Visualizes AI-generated insights from energy certificates
- **Data Sources**: `[ev_enova].[OpenAIAnswers]`, `[ev_enova].[ViewOpenAIinPowerBI]`
- **Key Metrics**: AI completion rates, evaluation trends, processing performance

### Usage:
```bash
# Process data for Power BI
python main.py openai --limit 100

# Open Power BI report
# Double-click: reports/energy_certificate_analysis.pbix

# Refresh data in Power BI Desktop
# Click "Refresh" to get latest analysis results
```

**Prerequisites**:
- Power BI Desktop installed
- Database access with read permissions
- ODBC drivers configured

## License

This project is for internal use with Enova's public API. Please respect API rate limits and terms of service.
