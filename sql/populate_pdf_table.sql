-- SQL Script to populate EnergylabelIDFiles table with PDF files
-- This creates a PowerShell command that generates INSERT statements
-- Run this in SQL Server Management Studio

USE [EnergyCertificate]
GO

-- First, let's see what we have currently
SELECT 
    COUNT(*) as current_file_count,
    MIN(sync_date) as oldest_sync,
    MAX(sync_date) as newest_sync
FROM [ev_enova].[EnergylabelIDFiles];

-- Show some sample records
SELECT TOP 10 
    file_id,
    filename,
    file_size,
    file_extension,
    sync_date
FROM [ev_enova].[EnergylabelIDFiles]
ORDER BY sync_date DESC;

PRINT ''
PRINT '========================================================='
PRINT 'To populate the table with PDF files from your directory:'
PRINT '========================================================='
PRINT ''
PRINT '1. Run the Python scanner:'
PRINT '   python scan_pdf_files.py'
PRINT ''
PRINT '2. Or use PowerShell to generate INSERT statements:'
PRINT '   See the PowerShell script below'
PRINT ''
PRINT '========================================================='

/*
-- Alternative: PowerShell script to generate SQL INSERT statements
-- Save this as a .ps1 file and run it, then execute the output in SSMS

$pdfPath = "C:\Users\tomm\minimba_project\minimba_project\data\downloads\pdfs"
$outputFile = "insert_pdf_files.sql"

# Clear output file
"USE [EnergyCertificate]" | Out-File $outputFile -Encoding UTF8
"GO" | Out-File $outputFile -Append -Encoding UTF8
"" | Out-File $outputFile -Append -Encoding UTF8

# Get all PDF files
$pdfFiles = Get-ChildItem -Path $pdfPath -Filter "*.pdf" -Recurse

Write-Host "Found $($pdfFiles.Count) PDF files"

$batchSize = 100
$currentBatch = 0

foreach ($file in $pdfFiles) {
    if ($currentBatch -eq 0) {
        "-- Batch of $batchSize files" | Out-File $outputFile -Append -Encoding UTF8
        "INSERT INTO [ev_enova].[EnergylabelIDFiles] (filename, full_path, file_size, file_extension, sync_date)" | Out-File $outputFile -Append -Encoding UTF8
        "VALUES" | Out-File $outputFile -Append -Encoding UTF8
    }
    
    $filename = $file.Name
    $fullPath = $file.FullName -replace "'", "''"  # Escape single quotes
    $fileSize = $file.Length
    $extension = $file.Extension.ToLower()
    $syncDate = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    
    $comma = if ($currentBatch -eq ($batchSize - 1) -or $file -eq $pdfFiles[-1]) { "" } else { "," }
    
    "    ('$filename', '$fullPath', $fileSize, '$extension', '$syncDate')$comma" | Out-File $outputFile -Append -Encoding UTF8
    
    $currentBatch++
    
    if ($currentBatch -eq $batchSize -or $file -eq $pdfFiles[-1]) {
        "GO" | Out-File $outputFile -Append -Encoding UTF8
        "" | Out-File $outputFile -Append -Encoding UTF8
        $currentBatch = 0
    }
}

Write-Host "Generated SQL file: $outputFile"
Write-Host "Execute this file in SQL Server Management Studio"

*/

PRINT ''
PRINT 'Alternative PowerShell approach:'
PRINT '1. Copy the PowerShell script from the comments above'
PRINT '2. Save it as generate_pdf_inserts.ps1'  
PRINT '3. Run: PowerShell -ExecutionPolicy Bypass -File generate_pdf_inserts.ps1'
PRINT '4. Execute the generated insert_pdf_files.sql in SSMS'
PRINT ''
PRINT 'Recommended: Use the Python scanner for better error handling'
PRINT '========================================================='
