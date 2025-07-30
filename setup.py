#!/usr/bin/env python3
"""
Setup script for MinimBA Energy Certificate Processing System
This script helps initialize the database and verify the setup
"""

import sys
import os
from pathlib import Path
from config import Config

def check_dependencies():
    """Check if required dependencies are installed"""
    print("Checking dependencies...")
    
    required_packages = [
        'pyodbc',
        'requests', 
        'pandas'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
            print(f"  ✓ {package}")
        except ImportError:
            print(f"  ✗ {package} - MISSING")
            missing_packages.append(package)
    
    if missing_packages:
        print(f"\nMissing packages: {', '.join(missing_packages)}")
        print("Please install them with: pip install -r requirements.txt")
        return False
    
    print("All dependencies are installed!")
    return True

def check_configuration():
    """Check configuration"""
    print("\nChecking configuration...")
    
    try:
        config = Config()
        
        # Check .env file exists
        env_file = Path('.env')
        if env_file.exists():
            print("  ✓ .env file exists")
        else:
            print("  ✗ .env file missing")
            return False
        
        # Check database configuration
        print(f"  Database: {config.DATABASE_SERVER}/{config.DATABASE_NAME}")
        print(f"  Trusted connection: {config.DATABASE_TRUSTED_CONNECTION}")
        
        # Check API key
        if config.ENOVA_API_KEY:
            print(f"  ✓ Enova API key configured")
        else:
            print("  ✗ Enova API key missing")
            return False
        
        # Validate configuration
        if config.validate_config():
            print("  ✓ Configuration is valid")
            return True
        else:
            print("  ✗ Configuration validation failed")
            return False
            
    except Exception as e:
        print(f"  ✗ Configuration error: {str(e)}")
        return False

def test_database_connection(config):
    """Test database connection"""
    print("\nTesting database connection...")
    
    try:
        import pyodbc
        
        # Build connection string
        if config.DATABASE_TRUSTED_CONNECTION:
            conn_str = (
                f"DRIVER={{{config.DATABASE_DRIVER}}};"
                f"SERVER={config.DATABASE_SERVER};"
                f"DATABASE={config.DATABASE_NAME};"
                f"Trusted_Connection=yes;"
            )
        else:
            conn_str = (
                f"DRIVER={{{config.DATABASE_DRIVER}}};"
                f"SERVER={config.DATABASE_SERVER};"
                f"DATABASE={config.DATABASE_NAME};"
                f"UID={config.DATABASE_USERNAME};"
                f"PWD={config.DATABASE_PASSWORD};"
            )
        
        conn = pyodbc.connect(conn_str)
        cursor = conn.cursor()
        cursor.execute("SELECT 1 AS test, GETDATE() AS current_time")
        result = cursor.fetchone()
        conn.close()
        
        print(f"  ✓ Database connection successful")
        print(f"  Server time: {result.current_time}")
        return True
        
    except Exception as e:
        print(f"  ✗ Database connection failed: {str(e)}")
        return False

def check_database_tables(config):
    """Check if required database tables exist"""
    print("\nChecking database tables...")
    
    try:
        import pyodbc
        
        # Build connection string
        if config.DATABASE_TRUSTED_CONNECTION:
            conn_str = (
                f"DRIVER={{{config.DATABASE_DRIVER}}};"
                f"SERVER={config.DATABASE_SERVER};"
                f"DATABASE={config.DATABASE_NAME};"
                f"Trusted_Connection=yes;"
            )
        else:
            conn_str = (
                f"DRIVER={{{config.DATABASE_DRIVER}}};"
                f"SERVER={config.DATABASE_SERVER};"
                f"DATABASE={config.DATABASE_NAME};"
                f"UID={config.DATABASE_USERNAME};"
                f"PWD={config.DATABASE_PASSWORD};"
            )
        
        conn = pyodbc.connect(conn_str)
        cursor = conn.cursor()
        
        required_tables = [
            'ev_enova.Certificate',
            'ev_enova.EnovaApi_Energiattest_url_log', 
            'ev_enova.EnovaApi_Energiattest_url'
        ]
        
        missing_tables = []
        
        for table in required_tables:
            schema, table_name = table.split('.')
            cursor.execute("""
                SELECT COUNT(*) 
                FROM INFORMATION_SCHEMA.TABLES 
                WHERE TABLE_SCHEMA = ? AND TABLE_NAME = ?
            """, (schema, table_name))
            
            if cursor.fetchone()[0] > 0:
                print(f"  ✓ {table}")
            else:
                print(f"  ✗ {table} - MISSING")
                missing_tables.append(table)
        
        # Check stored procedure
        cursor.execute("""
            SELECT COUNT(*) 
            FROM INFORMATION_SCHEMA.ROUTINES 
            WHERE ROUTINE_SCHEMA = 'ev_enova' AND ROUTINE_NAME = 'Get_Enova_API_Parameters'
        """)
        
        if cursor.fetchone()[0] > 0:
            print(f"  ✓ ev_enova.Get_Enova_API_Parameters")
        else:
            print(f"  ✗ ev_enova.Get_Enova_API_Parameters - MISSING")
            missing_tables.append('Get_Enova_API_Parameters')
        
        conn.close()
        
        if missing_tables:
            print(f"\nMissing database objects: {', '.join(missing_tables)}")
            print("Please run the SQL script: sql/create_tables.sql")
            return False
        
        print("All required database objects exist!")
        return True
        
    except Exception as e:
        print(f"  ✗ Database table check failed: {str(e)}")
        return False

def test_api_connection(config):
    """Test API connection"""
    print("\nTesting API connection...")
    
    try:
        import requests
        
        # Test the file download API first (simpler)
        url = f"{config.ENOVA_API_BASE_URL}/Fil/2025"
        headers = {
            "Content-Type": "application/json",
            "Cache-Control": "no-cache"
        }
        
        if config.ENOVA_API_KEY:
            headers["x-api-key"] = config.ENOVA_API_KEY
        
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            print(f"  ✓ API connection successful")
            data = response.json()
            print(f"  API response keys: {list(data.keys())}")
            return True
        else:
            print(f"  ✗ API connection failed: Status {response.status_code}")
            print(f"  Response: {response.text[:200]}...")
            return False
            
    except Exception as e:
        print(f"  ✗ API connection failed: {str(e)}")
        return False

def create_data_directories(config):
    """Create required data directories"""
    print("\nCreating data directories...")
    
    try:
        directories = [
            config.DOWNLOAD_CSV_PATH,
            config.DOWNLOAD_PDF_PATH,
            config.PROCESSED_TEXT_PATH,
            config.LOGS_PATH
        ]
        
        for directory in directories:
            path = Path(directory)
            path.mkdir(parents=True, exist_ok=True)
            print(f"  ✓ {directory}")
        
        print("All data directories created!")
        return True
        
    except Exception as e:
        print(f"  ✗ Error creating directories: {str(e)}")
        return False

def show_next_steps():
    """Show next steps for the user"""
    print("\n" + "=" * 60)
    print("SETUP COMPLETED!")
    print("=" * 60)
    print("\nNext steps:")
    print("1. Create database tables:")
    print("   - Run the SQL script: sql/create_tables.sql")
    print("   - Optionally add test data: sql/sample_data.sql")
    print()
    print("2. Test the system:")
    print("   python main.py download 2025              # Download CSV data")
    print("   python main.py list                       # List downloaded files")
    print("   python tests/test_api_client.py --rows 5  # Test API client")
    print("   python main.py api --rows 5               # Process certificates")
    print()
    print("3. For development:")
    print("   python tests/test_api_client.py --test-connection  # Test DB connection")
    print("   python tests/test_api_client.py --test-procedure   # Test stored proc")
    print("   python tests/test_api_client.py --test-api         # Test API call")
    print("=" * 60)

def main():
    """Main setup function"""
    print("=" * 60)
    print("MinimBA Energy Certificate Processing System")
    print("Setup and Verification Script")
    print("=" * 60)
    
    all_good = True
    
    # Check dependencies
    if not check_dependencies():
        all_good = False
    
    # Check configuration
    config = None
    if not check_configuration():
        all_good = False
    else:
        config = Config()
    
    # Create data directories
    if config and not create_data_directories(config):
        all_good = False
    
    # Test database connection
    if config and not test_database_connection(config):
        all_good = False
    
    # Check database tables (optional - will fail if not created yet)
    if config:
        check_database_tables(config)  # Don't fail setup if tables don't exist
    
    # Test API connection
    if config and not test_api_connection(config):
        all_good = False
    
    if all_good:
        print("\n✓ Basic setup verification completed successfully!")
    else:
        print("\n✗ Some setup issues were found. Please fix them before proceeding.")
    
    show_next_steps()
    
    return 0 if all_good else 1

if __name__ == "__main__":
    sys.exit(main())
