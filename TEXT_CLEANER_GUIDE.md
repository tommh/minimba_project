# PDF Text Cleaner Service Guide

## Overview

The PDF Text Cleaner service (`src/services/text_cleaner.py`) is designed to clean and normalize extracted PDF text for better LLM consumption. It removes common PDF artifacts, unwanted patterns, and normalizes text structure.

## Features

✅ **Comprehensive Text Cleaning** - Remove PDF artifacts, headers, footers, and unwanted patterns  
✅ **Regex Pattern Matching** - Advanced pattern recognition for common PDF issues  
✅ **Multiprocessing Support** - Fast parallel processing for large datasets  
✅ **Database Integration** - Direct integration with PDF text storage tables  
✅ **Configurable Cleaning** - Adjustable cleaning levels and options  
✅ **Statistics & Monitoring** - Detailed processing statistics and success rates  

## Quick Start

### 1. Basic Usage

```bash
# Clean 10 records (default)
python main.py clean-text

# Clean 100 records
python main.py clean-text --count 100

# Use multiprocessing for faster processing
python main.py clean-text --multiprocess --count 500

# Aggressive cleaning (removes more content)
python main.py clean-text --aggressive --count 50
```

### 2. Direct Service Usage

```bash
# Direct service usage
python src/services/text_cleaner.py --count 50

# With multiprocessing
python src/services/text_cleaner.py --multiprocess --processes 4 --count 200

# Aggressive cleaning mode
python src/services/text_cleaner.py --aggressive --count 100
```

## Command Line Options

| Option | Description | Default |
|--------|-------------|---------|
| `--count` | Number of records to process | 10 |
| `--multiprocess` | Use multiprocessing | False |
| `--processes` | Number of processes to use | Auto-detect |
| `--aggressive` | Use aggressive cleaning | False |
| `--verbose` | Enable verbose logging | False |

## Text Cleaning Features

### 1. PDF Artifact Removal

The cleaner removes common PDF artifacts:

- **Page breaks and form feeds** (`\f`, `\x0c`)
- **Standalone page numbers** (`123`, `Page 45`)
- **Page indicators** (`1/10`, `5/12`)
- **Decorative lines** (`---`, `===`, `___`)
- **Bullet point artifacts** (`•`, `▪`, `■`, etc.)

### 2. Header/Footer Removal

Removes common repeating headers and footers:

- **Confidentiality notices** (`CONFIDENTIAL`, `PROPRIETARY`)
- **Copyright lines** (`© 2024 Company Name`)
- **Date-only lines** (`12/31/2024`, `31-12-24`)

### 3. Content Normalization

- **Unicode normalization** - Standardizes character encoding
- **Control character removal** - Removes null bytes and control chars
- **Whitespace normalization** - Removes excessive whitespace
- **Line length filtering** - Removes very short lines (configurable)

### 4. Duplicate Detection

- **Similarity-based deduplication** - Removes similar lines
- **Configurable threshold** - Adjust similarity sensitivity
- **Content block extraction** - Identifies meaningful content blocks

## Database Integration

### Tables Used

- **`[ev_enova].[EnergylabelIDFiles]`** - Source PDF file information
- **`[ev_enova].[PDFTextExtraction]`** - Raw extracted text
- **`[ev_enova].[PDFTextCleaned]`** - Cleaned text storage

### Processing Flow

1. **Query raw text** - Get unprocessed text from `PDFTextExtraction`
2. **Apply cleaning** - Use regex patterns and text processing
3. **Save results** - Store cleaned text in `PDFTextCleaned`
4. **Update status** - Mark records as processed

## Configuration

### Environment Variables

The service uses the same configuration as other services:

```env
# Database Configuration
DATABASE_SERVER=your-server
DATABASE_NAME=your-database
DATABASE_USERNAME=your-username
DATABASE_PASSWORD=your-password
DATABASE_DRIVER=ODBC Driver 17 for SQL Server
DATABASE_TRUSTED_CONNECTION=true

# Processing Configuration
DOWNLOAD_PDF_PATH=data/downloads/pdfs
```

## Performance Optimization

### 1. Multiprocessing

For large datasets, use multiprocessing:

```bash
# Auto-detect CPU cores
python main.py clean-text --multiprocess --count 1000

# Specify number of processes
python main.py clean-text --multiprocess --processes 8 --count 2000
```

### 2. Batch Processing

The service processes records in batches for optimal performance:

- **Default batch size**: 100 records
- **Configurable**: Adjust based on memory and performance needs
- **Error handling**: Continues processing even if individual records fail

### 3. Memory Management

- **Streaming processing** - Processes records one at a time
- **Garbage collection** - Automatic memory cleanup
- **Connection pooling** - Efficient database connections

## Error Handling

### Common Issues

1. **Database Connection Errors**
   - Check connection string and credentials
   - Verify database server accessibility

2. **Memory Issues**
   - Reduce batch size for large files
   - Use multiprocessing to distribute load

3. **Text Encoding Issues**
   - Unicode normalization handles most cases
   - Check source PDF encoding

### Debugging

Enable verbose logging for detailed information:

```bash
python main.py clean-text --verbose --count 10
```

## Integration with Workflow

### Typical Processing Pipeline

1. **Scan PDFs** → `python main.py scan-pdf`
2. **Download PDFs** → `python main.py download-pdf`
3. **Extract Text** → `python main.py process-pdf`
4. **Clean Text** → `python main.py clean-text` ← **You are here**
5. **Parse Content** → (Next step in pipeline)

### Batch Processing Example

```bash
# Complete pipeline for 1000 files
python main.py scan-pdf --force
python main.py download-pdf --count 1000
python main.py process-pdf --multiprocess --count 1000
python main.py clean-text --multiprocess --count 1000
```

## Monitoring and Statistics

### Processing Statistics

The service provides detailed statistics:

```
✅ PDF text cleaning completed successfully
   Records processed: 1,000
   Successful cleanings: 985
   Failed cleanings: 15
   Processing time: 45.2 seconds
   Success rate: 98.5%
   Processing rate: 22.1 records/second
```

### Database Queries

Monitor processing status:

```sql
-- Check processing status
SELECT 
    COUNT(*) as total_records,
    SUM(CASE WHEN cleaned_text IS NOT NULL THEN 1 ELSE 0 END) as cleaned_records,
    SUM(CASE WHEN cleaned_text IS NULL THEN 1 ELSE 0 END) as pending_records
FROM [ev_enova].[PDFTextExtraction] e
LEFT JOIN [ev_enova].[PDFTextCleaned] c ON e.file_id = c.file_id;

-- Check recent processing
SELECT TOP 10
    file_id,
    filename,
    extraction_date,
    cleaning_date,
    LEN(cleaned_text) as cleaned_length
FROM [ev_enova].[PDFTextExtraction] e
LEFT JOIN [ev_enova].[PDFTextCleaned] c ON e.file_id = c.file_id
ORDER BY extraction_date DESC;
```

## Advanced Usage

### Custom Cleaning Patterns

You can extend the cleaning patterns by modifying `PDFTextCleaner`:

```python
# Add custom patterns
self.unwanted_patterns.extend([
    r'your-custom-pattern',
    r'another-pattern'
])
```

### Programmatic Usage

```python
from src.services.text_cleaner import PDFTextCleaner, TextCleaningProcessor
from config import Config

# Initialize
config = Config()
processor = TextCleaningProcessor(config)

# Process batch
result = processor.process_batch_single_thread(count=100, aggressive=True)

# Use cleaner directly
cleaner = PDFTextCleaner()
cleaned_text = cleaner.clean_text(raw_text, aggressive_cleaning=True)
```

## Troubleshooting

### Common Problems

1. **"Text cleaner module not found"**
   - Ensure `src/services/text_cleaner.py` exists
   - Check Python path configuration

2. **"Configuration validation failed"**
   - Verify `.env` file exists and is properly configured
   - Check database connection settings

3. **"No records found to process"**
   - Ensure text extraction has been completed first
   - Check database tables for extracted text

4. **"Processing failed with error"**
   - Enable verbose logging for detailed error information
   - Check database permissions and connectivity

### Performance Tips

1. **Use multiprocessing** for datasets > 100 records
2. **Adjust batch size** based on available memory
3. **Monitor database performance** during large processing jobs
4. **Use aggressive cleaning** only when necessary

## Support

For issues or questions:

1. **Check logs** - Enable verbose logging for detailed information
2. **Verify configuration** - Ensure all environment variables are set
3. **Test with small batches** - Start with 10-50 records to verify setup
4. **Check database connectivity** - Verify database access and permissions

---

**Next Steps**: After text cleaning, the processed text is ready for content parsing and AI analysis in the next pipeline stage. 