# PDF File Scanner - Database Population Tool

## 🎯 **Purpose**
Scan your `data/downloads/pdfs` directory and populate the `[ev_enova].[EnergylabelIDFiles]` database table with file information.

## 📁 **What It Does**

✅ **Scans PDF Directory**: Recursively finds all `.pdf` files  
✅ **Extracts File Info**: Filename, full path, file size, extension, modified date  
✅ **Populates Database**: Inserts file records into `[ev_enova].[EnergylabelIDFiles]`  
✅ **Avoids Duplicates**: Skips files already in database (unless `--force` used)  
✅ **Batch Processing**: Efficient batch inserts (configurable batch size)  
✅ **Error Handling**: Robust error handling and logging  
✅ **Progress Reporting**: Shows detailed progress and statistics  

## 🚀 **Usage Options**

### **1. Main CLI Command** (Recommended)
```bash
# Basic scan (skip existing files)
python main.py scan-pdf

# Force scan all files (including existing)
python main.py scan-pdf --force

# Custom batch size
python main.py scan-pdf --batch-size 200

# Show help
python main.py scan-pdf --help
```

### **2. Programmatic Usage**
```python
from src.services.pdf_scanner import PDFFileScanner
from config import get_config

config = get_config()
scanner = PDFFileScanner(config)

# Scan with default settings
result = scanner.scan_pdf_directory()

# Force scan all files
result = scanner.scan_pdf_directory(force=True, batch_size=50)
```

### **3. SQL/PowerShell Alternative**
```sql
-- Run the SQL script for instructions
-- File: sql/populate_pdf_table.sql
```

## 📊 **Example Output**

```bash
$ python main.py scan-pdf

📁 Scanning directory: C:\Users\tomm\minimba_project\minimba_project\data\downloads\pdfs
Found 1247 files already in database
Found 2834 PDF files in directory
Files to insert: 1587
Files skipped (already exist): 1247

Batch 1: Inserted 100 files
Batch 2: Inserted 100 files
...
Batch 16: Inserted 87 files

==================================================
PDF File Scan Complete
==================================================
Total files processed: 2834
Files added to database: 1587  
Files skipped (existing): 1247

✅ Scan completed successfully!
   Files processed: 2,834
   Files added: 1,587
   Files skipped: 1,247
```

## 🔧 **Database Table Structure**

The scanner populates this table:
```sql
CREATE TABLE [ev_enova].[EnergylabelIDFiles](
    [file_id] [int] IDENTITY(1,1) NOT NULL,
    [filename] [nvarchar](255) NOT NULL,
    [full_path] [nvarchar](500) NULL,
    [file_size] [bigint] NULL,
    [file_extension] [nvarchar](10) NULL,
    [sync_date] [datetime] NULL
)
```

**Fields populated**:
- `filename`: Just the file name (e.g., "certificate_123.pdf")
- `full_path`: Complete path to file
- `file_size`: File size in bytes
- `file_extension`: Always ".pdf" for this scanner
- `sync_date`: When the record was added to database

## 📈 **Features**

### **Smart Duplicate Handling**:
- By default, skips files already in database
- Use `--force` to re-scan all files
- Compares by filename only

### **Directory Statistics**:
```bash
# The scanner automatically shows statistics during execution
python main.py scan-pdf

# For detailed logging, you can also use the programmatic approach
from src.services.pdf_scanner import PDFFileScanner
scanner = PDFFileScanner(config)
stats = scanner.get_directory_statistics()
print(f"Total PDF files: {stats['total_files']}")
print(f"Files in database: {stats['files_in_db']}")
print(f"Files to process: {stats['files_to_process']}")
```

### **Batch Processing**:
- Processes files in configurable batches (default: 100)
- Efficient for large directories
- Progress reporting for long-running scans

### **Error Handling**:
- Handles corrupted/inaccessible files gracefully
- Continues processing even if individual files fail
- Detailed error logging

## 🏗️ **Service Architecture**

The PDF scanner is now integrated as a service in the main CLI:

```
src/services/pdf_scanner.py  ← PDF scanner service
main.py                      ← Main CLI with scan-pdf command
config.py                    ← Configuration management
```

**Integration Benefits:**
- ✅ Consistent with other services (file_downloader, api_client, etc.)
- ✅ Uses shared configuration and logging
- ✅ Available through main CLI: `python main.py scan-pdf`
- ✅ Programmatic access for custom workflows

## ⚙️ **Configuration**

Uses your existing `.env` configuration:
- Database connection settings
- PDF directory path (`DOWNLOAD_PDF_PATH`)
- Logging preferences

## 🔍 **Monitoring Queries**

After running the scanner, use these SQL queries to check results:

```sql
-- Check total files in database
SELECT COUNT(*) as total_files FROM [ev_enova].[EnergylabelIDFiles];

-- Check recent sync activity
SELECT 
    CAST(sync_date AS DATE) as sync_date,
    COUNT(*) as files_added
FROM [ev_enova].[EnergylabelIDFiles]
GROUP BY CAST(sync_date AS DATE)
ORDER BY sync_date DESC;

-- Check largest files
SELECT TOP 10
    filename,
    file_size / 1024 / 1024 as size_mb,
    sync_date
FROM [ev_enova].[EnergylabelIDFiles]
ORDER BY file_size DESC;

-- Check for duplicate filenames
SELECT 
    filename,
    COUNT(*) as count
FROM [ev_enova].[EnergylabelIDFiles]
GROUP BY filename
HAVING COUNT(*) > 1;
```

## 🛠️ **Troubleshooting**

### **Common Issues**:

1. **"PDF directory does not exist"**
   ```bash
   # Check your .env configuration
   BASE_DATA_PATH=./data
   ```

2. **Database connection failed**
   ```bash
   # Verify database settings in .env
   DATABASE_SERVER=TH\SQL2025
   DATABASE_NAME=EnergyCertificate
   ```

3. **Permission denied on files**
   - Some PDF files may be locked/in use
   - Scanner continues with other files
   - Check verbose logs for details

4. **Memory issues with large directories**
   ```bash
   # Use smaller batch size
   python main.py scan-pdf --batch-size 50
   ```

## 📋 **Integration with Workflow**

This scanner is **Step 4** in your overall workflow:
1. ✅ Download CSV files (`python main.py download`)
2. ⏳ Import CSV to database (coming next)
3. ✅ Process certificates via API (`python main.py api`)
4. ✅ **Scan PDF files** (`python main.py scan-pdf`) ← **NEW**
5. ⏳ Extract text from PDFs (coming next)
6. ⏳ Clean and parse text (coming next)
7. ⏳ OpenAI analysis (coming next)

## 🎯 **Quick Start**

```bash
# 1. Check what's in your PDF directory
python scan_pdf_files.py --stats

# 2. Run the scan
python scan_pdf_files.py

# 3. Verify results in database
# Run the monitoring queries above in SSMS
```

## ✅ **Result**

You now have a complete solution to populate your `[ev_enova].[EnergylabelIDFiles]` table with all PDF files from your directory, with smart duplicate handling, batch processing, and comprehensive error handling! 🎉

**Files created:**
- `scan_pdf_files.py` - Main scanner script
- `sql/populate_pdf_table.sql` - SQL/PowerShell alternative
- Enhanced `main.py` with `scan-pdf` command
