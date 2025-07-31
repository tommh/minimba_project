# PDF Text Processor - Docling Integration

## 🎯 **Purpose**
Extract text from PDF files using **Docling** (IBM's advanced document processing library) and store the results in your database.

## 📋 **Prerequisites**

### 1. **Install Docling**
```bash
# Install docling
pip install docling

# Or install all dependencies
pip install -r requirements.txt
```

### 2. **Database Setup**
Run the SQL setup script:
```sql
-- Run this in SQL Server Management Studio
-- File: sql/create_pdf_extraction_tables.sql
```

This creates:
- `[ev_enova].[EnergyLabelFileExtract]` - Stores extracted text
- `[ev_enova].[Get_PDF_for_Extract]` - Gets PDFs needing processing

### 3. **PDF Files**
- PDFs should be in your database (`[ev_enova].[EnergylabelIDFiles]`)
- Files accessible at paths specified in `full_path` column
- Typically in `data/downloads/pdfs/` directory

## 🚀 **Usage Options**

### **1. Standalone Script** (Recommended)
```bash
# Process 10 PDFs (default, single-thread)
python src/services/pdf_processor.py

# Process 50 PDFs  
python src/services/pdf_processor.py --count 50

# Use multiprocessing for speed (recommended for large batches)
python src/services/pdf_processor.py --count 100 --multiprocess

# Control number of processes
python src/services/pdf_processor.py --multiprocess --processes 4

# Verbose logging
python src/services/pdf_processor.py --verbose
```

### **2. Integrated CLI**
```bash
# Process 10 PDFs via main CLI
python main.py process-pdf

# Process 50 PDFs with multiprocessing
python main.py process-pdf --count 50 --multiprocess

# Control processes
python main.py process-pdf --multiprocess --processes 6
```

## 🔄 **How It Works**

### **Smart File Selection**
The stored procedure `Get_PDF_for_Extract` finds PDFs that:
1. ✅ Exist in `[ev_enova].[EnergylabelIDFiles]` table
2. ✅ Have `.pdf` extension
3. ✅ Haven't been processed yet (no entry in extract table)
4. ✅ Are ordered by filename for consistent processing

### **Processing Workflow**
1. **📋 Get Files**: Calls stored procedure for batch of PDF files
2. **🔍 Validate**: Checks file exists and size is reasonable (<50MB)
3. **📄 Extract**: Uses Docling to extract text and metadata
4. **💾 Store**: Saves extracted text and statistics to database
5. **📊 Report**: Tracks success/failure rates and processing speed

### **Docling Advantages**
- **🧠 AI-Powered**: Advanced document understanding
- **📊 Table Extraction**: Handles complex layouts, tables, headers
- **🔤 High Accuracy**: Better text extraction than traditional PDF parsers
- **📈 Metadata**: Extracts page count, document structure
- **🌍 Multi-language**: Supports various languages including Norwegian

## 📊 **Example Output**

### **Single-Thread Processing**:
```bash
$ python src/services/pdf_processor.py --count 20

Processing file_id 21182: 0157d540-79c0-46de-ada9-c84fd8628c69.pdf
Successfully extracted text from 0157d540-79c0-46de-ada9-c84fd8628c69.pdf: 2,847 characters

Processing file_id 21183: 01e82f64-e4ae-4672-b24c-a490674ef611.pdf
Successfully extracted text from 01e82f64-e4ae-4672-b24c-a490674ef611.pdf: 1,923 characters

Progress: 10/20 files, 3.2 files/min

==================================================
PDF Text Extraction Complete
==================================================
Files processed: 20
Successful extractions: 18
Failed extractions: 2
Processing time: 127.3 seconds
Average time per file: 6.4 seconds

✅ PDF text extraction completed!
   Files processed: 20
   Successful extractions: 18
   Failed extractions: 2
   Processing time: 127.3 seconds
   Success rate: 90.0%
   Processing rate: 0.16 files/second
```

### **Multiprocessing** (Much Faster):
```bash
$ python src/services/pdf_processor.py --count 100 --multiprocess

Using 8 processes for 100 files

Process starting file_id 21182: 0157d540-79c0-46de-ada9-c84fd8628c69.pdf
Process starting file_id 21183: 01e82f64-e4ae-4672-b24c-a490674ef611.pdf
...
Successfully processed file_id 21182: 2,847 characters
Successfully processed file_id 21185: 1,654 characters

==================================================
PDF Text Extraction Complete (Multiprocess)
==================================================
Files processed: 100
Successful extractions: 94
Failed extractions: 6
Processing time: 89.7 seconds
Average time per file: 0.9 seconds

✅ PDF text extraction completed!
   Success rate: 94.0%
   Processing rate: 1.11 files/second
```

## 🛡️ **Safety Features**

### **File Validation**:
- **Size limits**: Skips files over 50MB (configurable)
- **Existence check**: Verifies file exists before processing
- **Content validation**: Detects very short extractions (likely errors)

### **Error Handling**:
- **Graceful failures**: Continues processing even if some files fail
- **Detailed logging**: Records specific error messages
- **Status tracking**: Different status codes (SUCCESS, FAILED, FILE_NOT_FOUND, etc.)

### **Performance Optimization**:
- **Multiprocessing**: Uses multiple CPU cores for parallel processing
- **Memory management**: Processes files in configurable batches
- **Progress reporting**: Shows real-time processing statistics

## 📈 **Database Results**

After processing, check your results:

```sql
-- Check extraction status
SELECT 
    extraction_status,
    COUNT(*) as count,
    AVG(character_count) as avg_chars,
    AVG(page_count) as avg_pages
FROM [ev_enova].[EnergyLabelFileExtract]
GROUP BY extraction_status;

-- Recent extractions
SELECT TOP 10
    filename,
    character_count,
    page_count,
    extraction_status,
    extraction_date
FROM [ev_enova].[EnergyLabelFileExtract]
ORDER BY extraction_date DESC;

-- Sample extracted text
SELECT TOP 3
    filename,
    LEFT(extracted_text, 200) + '...' as text_sample
FROM [ev_enova].[EnergyLabelFileExtract]
WHERE extraction_status = 'SUCCESS'
ORDER BY character_count DESC;
```

## ⚙️ **Performance Tips**

### **Single-Thread vs Multiprocessing**:
- **Single-thread**: 0.1-0.2 files/second, uses ~2GB RAM
- **Multiprocess**: 0.5-2.0 files/second, uses ~2-4GB RAM per process

### **Recommended Settings**:
```bash
# Small batches (testing)
python src/services/pdf_processor.py --count 10

# Medium batches (regular use) 
python src/services/pdf_processor.py --count 50 --multiprocess

# Large batches (bulk processing)
python src/services/pdf_processor.py --count 200 --multiprocess --processes 8
```

### **System Requirements**:
- **RAM**: 4GB minimum, 16GB+ recommended for multiprocessing
- **CPU**: More cores = faster multiprocessing
- **Disk**: Sufficient space for PDF files and database

## 🔍 **Troubleshooting**

### **Common Issues**:

1. **"Docling not installed"**
   ```bash
   pip install docling  
   ```

2. **"No PDF files found to process"**
   - Check: `SELECT COUNT(*) FROM [ev_enova].[EnergylabelIDFiles] WHERE file_extension = '.pdf'`
   - Run: `python main.py scan-pdf` to populate file inventory

3. **High failure rate**
   - Check file paths are correct
   - Verify PDF files aren't corrupted
   - Check database logs for specific error messages

4. **Slow processing**
   - Use `--multiprocess` for faster extraction
   - Increase `--processes` count (up to CPU cores)
   - Ensure sufficient RAM (4GB+ per process)

## 📋 **Integration with Workflow**

This is **Step 5** in your processing pipeline:

1. ✅ Download CSV files (`python main.py download`)
2. ⏳ Import CSV to database (future)
3. ✅ Process certificates via API (`python main.py api`)
4. ✅ Download PDF files (`python main.py download-pdf`)
5. ✅ Scan PDF files (`python main.py scan-pdf`)
6. ✅ **Extract PDF text** (`python main.py process-pdf`) ← **NEW**
7. ⏳ Clean and parse text (future)
8. ⏳ AI analysis (future)

## 🎯 **Quick Start**

```bash
# 1. Install docling
pip install docling

# 2. Setup database tables  
# Run: sql/create_pdf_extraction_tables.sql in SSMS

# 3. Process some PDFs
python src/services/pdf_processor.py --count 20 --multiprocess

# 4. Check results in database
# SELECT * FROM [ev_enova].[EnergyLabelFileExtract]
```

## ✅ **Result**

You now have a production-ready PDF text extraction system that:
- ✅ **Uses advanced AI** (Docling) for superior text extraction
- ✅ **Scales efficiently** with multiprocessing support
- ✅ **Handles errors gracefully** with comprehensive logging
- ✅ **Integrates seamlessly** with your existing workflow
- ✅ **Tracks everything** with detailed database records

**Perfect for processing thousands of energy certificate PDFs!** 🎉

The extracted text is now ready for Step 6 (text cleaning and parsing) and Step 7 (AI analysis).
