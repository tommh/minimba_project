# PDF Downloader - Certificate URL to File System

## 🎯 **Purpose**
Download PDF files from certificate URLs stored in your database to your local `data/downloads/pdfs` directory.

## 📋 **Prerequisites**

### 1. **Database Setup**
First, run the SQL setup script:
```sql
-- Run this in SQL Server Management Studio
-- File: sql/create_pdf_download_tables.sql
```

This creates:
- `[ev_enova].[PDF_Download_Log]` - Tracks all download attempts
- `[ev_enova].[Get_Enova_BLOB_url]` - Stored procedure to get URLs

### 2. **Requirements**
- Certificate URLs in `[ev_enova].[EnovaApi_Energiattest_url]` table
- PDF directory configured in `.env` (`DOWNLOAD_PDF_PATH`)
- Internet connection for downloading files

## 🚀 **Usage Options**

### **1. Standalone Script** (Recommended)
```bash
# Download 10 PDFs (default)
python pdf_downloader.py

# Download 50 PDFs  
python pdf_downloader.py --count 50

# Add 2-second delay between downloads (be nice to servers)
python pdf_downloader.py --delay 2.0

# Verbose logging
python pdf_downloader.py --verbose
```

### **2. Integrated CLI**
```bash
# Download 10 PDFs via main CLI
python main.py download-pdf

# Download 20 PDFs with custom delay
python main.py download-pdf --count 20 --delay 1.5
```

## 🔄 **How It Works**

### **Smart URL Selection**
The stored procedure `Get_Enova_BLOB_url` finds URLs that:
1. ✅ Have valid `attest_url` in certificate data
2. ✅ Don't already exist as files on disk
3. ✅ Haven't been successfully downloaded before (logged)
4. ✅ Are unique (no duplicate URLs)

### **Download Process**
1. **📋 Get URLs**: Calls stored procedure for batch of URLs
2. **🔍 Check Existing**: Skips files already downloaded
3. **⬇️ Download**: Streams PDF files to disk with progress tracking
4. **✅ Verify**: Checks file size and content validity
5. **📊 Log**: Records all attempts (success/failure) in database

### **Filename Extraction**
Smart filename detection from URLs:
- Extracts from URL path (`/filename.pdf`)
- Parses query parameters (`?filename=cert.pdf`)
- Handles Azure blob URLs with metadata
- Generates fallback names for complex URLs

## 📊 **Example Output**

```bash
$ python pdf_downloader.py --count 20

Processing 1/15: Energiattest-2025-94803.pdf
Downloading: Energiattest-2025-94803.pdf from https://stemsenergyplanprodnoea.blob.core.windows.net/attester/...
Successfully downloaded: Energiattest-2025-94803.pdf (2,340,567 bytes)

Processing 2/15: Energiattest-20230414.pdf
File already exists: Energiattest-20230414.pdf (1,876,432 bytes)

Processing 3/15: certificate_a1b2c3d4.pdf
Download failed for certificate_a1b2c3d4.pdf: HTTP request failed: 404 Client Error

Progress: 10/15 processed, 7 successful

==================================================
PDF Download Batch Complete
==================================================
URLs processed: 15
Downloads successful: 8
Downloads failed: 2
Downloads skipped (existing): 5

✅ Download batch completed!
   URLs processed: 15
   Downloads successful: 8
   Downloads failed: 2
   Downloads skipped: 5
   Success rate: 80.0%
```

## 🛡️ **Safety Features**

### **Smart Error Handling**:
- **File size limits**: Skips files over 50MB
- **Content validation**: Detects error pages disguised as PDFs
- **Duplicate prevention**: Won't re-download existing files
- **Graceful failures**: Continues processing even if some downloads fail

### **Respectful Downloading**:
- **Rate limiting**: Configurable delay between downloads (default 1 second)
- **Proper headers**: Mimics browser behavior
- **Timeout handling**: 60-second timeout per download
- **Connection reuse**: Efficient HTTP session management

### **Comprehensive Logging**:
```sql
-- Check download results
SELECT 
    status,
    COUNT(*) as count,
    AVG(file_size) as avg_size
FROM [ev_enova].[PDF_Download_Log]
GROUP BY status
ORDER BY count DESC;
```

## 📈 **Integration with Workflow**

This is **Step 4** in your processing pipeline:

1. ✅ Download CSV files (`python main.py download`)
2. ✅ Import CSV to database (future)
3. ✅ Process certificates via API (`python main.py api`)
4. ✅ **Download PDF files** (`python main.py download-pdf`) ← **NEW**
5. ✅ Scan PDF files (`python main.py scan-pdf`)
6. ⏳ Extract text from PDFs (future)
7. ⏳ AI analysis (future)

## 🔍 **Monitoring & Troubleshooting**

### **Check Download Log**:
```sql
-- Recent download activity
SELECT TOP 20
    filename,
    status,
    status_message,
    file_size / 1024 / 1024 as size_mb,
    download_date
FROM [ev_enova].[PDF_Download_Log]
ORDER BY download_date DESC;

-- Success rate by day
SELECT 
    CAST(download_date AS DATE) as date,
    COUNT(*) as total_attempts,
    SUM(CASE WHEN status = 'Success' THEN 1 ELSE 0 END) as successful,
    CAST(SUM(CASE WHEN status = 'Success' THEN 1 ELSE 0 END) * 100.0 / COUNT(*) AS DECIMAL(5,2)) as success_rate
FROM [ev_enova].[PDF_Download_Log]
GROUP BY CAST(download_date AS DATE)
ORDER BY date DESC;
```

### **Common Issues**:

1. **"No URLs found to download"**
   - All certificates already have PDF files
   - Check: `SELECT COUNT(*) FROM [ev_enova].[EnovaApi_Energiattest_url] WHERE attest_url IS NOT NULL`

2. **High failure rate**
   - URLs may be expired/invalid
   - Check log table for specific error messages
   - Azure blob URLs have expiration times

3. **Downloads very slow**
   - Increase `--delay` to reduce server load
   - Check network connectivity

## ⚙️ **Configuration**

Uses your existing `.env` settings:
```bash
# PDF download directory
DOWNLOAD_PDF_PATH=./data/downloads/pdfs

# Database connection
DATABASE_SERVER=TH\SQL2025
DATABASE_NAME=EnergyCertificate
```

## 🎯 **Quick Start**

```bash
# 1. Setup database tables
# Run: sql/create_pdf_download_tables.sql in SSMS

# 2. Download some PDFs
python pdf_downloader.py --count 20

# 3. Check results in database
# SELECT * FROM [ev_enova].[PDF_Download_Log]

# 4. Sync file inventory
python main.py scan-pdf
```

## ✅ **Result**

You now have a complete PDF download system that:
- ✅ **Intelligently selects** URLs that need downloading
- ✅ **Downloads efficiently** with proper error handling
- ✅ **Tracks all attempts** in database log
- ✅ **Integrates perfectly** with your existing workflow
- ✅ **Handles edge cases** gracefully (expired URLs, duplicates, errors)

**Perfect for batch processing** thousands of certificate PDF files! 🎉
