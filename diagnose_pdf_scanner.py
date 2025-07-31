#!/usr/bin/env python3
"""
Quick diagnostic script to check PDF scanner issues
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from src.services.pdf_scanner import PDFFileScanner
from config import Config
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def diagnose_pdf_scanner():
    """Diagnose PDF scanner issues"""
    try:
        config = Config()
        scanner = PDFFileScanner(config)
        
        print("=== PDF Scanner Diagnostics ===")
        print(f"PDF Directory: {scanner.pdf_directory}")
        print(f"Directory exists: {scanner.pdf_directory.exists()}")
        
        # Check database connection
        try:
            conn = scanner.get_database_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM [ev_enova].[EnergylabelIDFiles]")
            db_count = cursor.fetchone()[0]
            print(f"Files in database: {db_count:,}")
            conn.close()
        except Exception as e:
            print(f"Database error: {e}")
            return
        
        # Count PDF files on disk
        if scanner.pdf_directory.exists():
            pdf_files = list(scanner.pdf_directory.rglob("*.pdf"))
            print(f"PDF files on disk: {len(pdf_files):,}")
            
            # Show first few filenames
            print("\\nSample PDF files:")
            for pdf_file in pdf_files[:5]:
                print(f"  {pdf_file.name}")
            if len(pdf_files) > 5:
                print("  ...")
        
        # Check existing files detection
        existing_files = scanner.get_existing_files()
        print(f"\\nExisting files detected: {len(existing_files):,}")
        
        # Show sample existing filenames
        if existing_files:
            print("Sample existing files in database:")
            for filename in list(existing_files)[:5]:
                print(f"  {filename}")
            if len(existing_files) > 5:
                print("  ...")
        
        # Check for filename overlaps
        if scanner.pdf_directory.exists():
            disk_filenames = {f.name for f in scanner.pdf_directory.rglob("*.pdf")}
            overlap = existing_files.intersection(disk_filenames)
            print(f"\\nFiles both on disk and in database: {len(overlap):,}")
            print(f"Files on disk only: {len(disk_filenames - existing_files):,}")
            print(f"Files in database only: {len(existing_files - disk_filenames):,}")
            
            # Show samples of each category
            disk_only = disk_filenames - existing_files
            if disk_only:
                print("\\nSample files on disk but not in database:")
                for filename in list(disk_only)[:3]:
                    print(f"  {filename}")
            
            db_only = existing_files - disk_filenames  
            if db_only:
                print("\\nSample files in database but not on disk:")
                for filename in list(db_only)[:3]:
                    print(f"  {filename}")
        
        # Check for potential database constraint issues
        try:
            conn = scanner.get_database_connection()
            cursor = conn.cursor()
            
            # Check for duplicate filenames in database
            cursor.execute("""
                SELECT filename, COUNT(*) as count
                FROM [ev_enova].[EnergylabelIDFiles] 
                GROUP BY filename 
                HAVING COUNT(*) > 1
            """)
            duplicates = cursor.fetchall()
            
            if duplicates:
                print(f"\\n⚠️  Found {len(duplicates)} duplicate filenames in database:")
                for dup in duplicates[:5]:
                    print(f"  {dup.filename} ({dup.count} times)")
            else:
                print("\\n✅ No duplicate filenames found in database")
            
            conn.close()
            
        except Exception as e:
            print(f"\\nError checking duplicates: {e}")
    
    except Exception as e:
        print(f"Diagnostic error: {e}")

if __name__ == "__main__":
    diagnose_pdf_scanner()
