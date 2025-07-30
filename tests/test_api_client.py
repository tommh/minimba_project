"""
Test script for Enova API Client
Tests the API client functionality with configurable number of rows
"""

import sys
import os
import argparse
import logging
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.services.api_client import EnovaApiClient
from config import Config

def setup_logging():
    """Setup logging configuration"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('api_client_test.log')
        ]
    )

def test_database_connection(config):
    """Test database connection"""
    print("Testing database connection...")
    try:
        client = EnovaApiClient(config)
        conn = client._get_database_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT 1 AS test")
        result = cursor.fetchone()
        conn.close()
        print(f"✓ Database connection successful: {result.test}")
        return True
    except Exception as e:
        print(f"✗ Database connection failed: {e}")
        return False

def test_stored_procedure(config, top_rows):
    """Test stored procedure call"""
    print(f"Testing stored procedure with TopRows = {top_rows}...")
    try:
        client = EnovaApiClient(config)
        parameters = client.get_api_parameters(top_rows)
        print(f"✓ Retrieved {len(parameters)} parameter sets")
        
        if parameters:
            print("Sample parameter:")
            sample = parameters[0]
            for key, value in sample.items():
                print(f"  {key}: {value}")
        
        return parameters
    except Exception as e:
        print(f"✗ Stored procedure test failed: {e}")
        return None

def test_api_call(config, parameters):
    """Test single API call"""
    if not parameters:
        print("No parameters to test API call")
        return False
    
    print("Testing single API call...")
    try:
        client = EnovaApiClient(config)
        sample_param = parameters[0]
        result = client.call_energiattest_api(sample_param)
        
        if result:
            print(f"✓ API call successful, returned {len(result)} records")
            if result:
                print("Sample result structure:")
                sample_result = result[0]
                print(f"  Keys: {list(sample_result.keys())}")
                if 'energiattest' in sample_result:
                    print(f"  Energiattest keys: {list(sample_result['energiattest'].keys())}")
        else:
            print("✗ API call returned no data")
            return False
        
        return True
    except Exception as e:
        print(f"✗ API call test failed: {e}")
        return False

def run_full_processing(config, top_rows):
    """Run full processing workflow"""
    print(f"Running full processing workflow with {top_rows} rows...")
    try:
        client = EnovaApiClient(config)
        result = client.process_certificates(top_rows)
        
        if result['success']:
            print("✓ Full processing completed successfully")
            print(f"  Parameters logged: {result['parameters_logged']}")
            print(f"  API calls made: {result['api_calls']}")
            print(f"  Records inserted: {result['records_inserted']}")
            print(f"  Processing time: {result['processing_time']:.3f} seconds")
            print(f"  Avg time per API call: {result['avg_time_per_api_call']:.4f} seconds")
            
            # Show status breakdown if available
            if 'status_breakdown' in result and result['status_breakdown']:
                print("\n  Status breakdown:")
                for status, info in result['status_breakdown'].items():
                    if status != '_totals':
                        print(f"    {status}: {info['count']} calls, {info['records']} records returned")
        else:
            print(f"✗ Processing failed: {result['message']}")
            return False
        
        return True
    except Exception as e:
        print(f"✗ Full processing test failed: {e}")
        return False

def main():
    """Main test function"""
    parser = argparse.ArgumentParser(
        description='Test Enova API Client',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python test_api_client.py --rows 5                    # Test with 5 rows
  python test_api_client.py --rows 10 --full           # Run full processing
  python test_api_client.py --test-connection          # Test connection only
  python test_api_client.py --test-procedure --rows 3  # Test stored procedure only
        """
    )
    
    parser.add_argument('--rows', type=int, default=10, 
                       help='Number of rows to process (default: 10)')
    parser.add_argument('--full', action='store_true', 
                       help='Run full processing workflow')
    parser.add_argument('--test-connection', action='store_true', 
                       help='Test database connection only')
    parser.add_argument('--test-procedure', action='store_true', 
                       help='Test stored procedure only')
    parser.add_argument('--test-api', action='store_true', 
                       help='Test API call only')
    parser.add_argument('--verbose', action='store_true', 
                       help='Enable verbose logging')
    
    args = parser.parse_args()
    
    # Setup logging
    if args.verbose:
        setup_logging()
    
    # Load configuration
    try:
        config = Config()
        if not config.validate_config():
            print("Configuration validation failed. Please check your .env file.")
            return 1
    except Exception as e:
        print(f"Configuration error: {str(e)}")
        return 1
    
    print("=" * 60)
    print("Enova API Client Test")
    print("=" * 60)
    print(f"Database: {config.DATABASE_SERVER}/{config.DATABASE_NAME}")
    print(f"API URL: {config.ENOVA_API_BASE_URL}")
    print(f"Rows to process: {args.rows}")
    print("=" * 60)
    
    # Run tests based on arguments
    success = True
    
    if args.test_connection:
        success = test_database_connection(config)
    elif args.test_procedure:
        parameters = test_stored_procedure(config, args.rows)
        success = parameters is not None
    elif args.test_api:
        parameters = test_stored_procedure(config, 1)  # Get one parameter for API test
        success = test_api_call(config, parameters)
    elif args.full:
        success = run_full_processing(config, args.rows)
    else:
        # Run all tests step by step
        print("\\nStep 1: Testing database connection...")
        if not test_database_connection(config):
            return 1
        
        print("\\nStep 2: Testing stored procedure...")
        parameters = test_stored_procedure(config, args.rows)
        if not parameters:
            return 1
        
        print("\\nStep 3: Testing API call...")
        if not test_api_call(config, parameters[:1]):  # Test with first parameter only
            return 1
        
        print("\\nAll tests passed! Ready for full processing.")
        
        # Ask if user wants to run full processing
        if input("\\nRun full processing? (y/N): ").lower().strip() == 'y':
            success = run_full_processing(config, args.rows)
    
    print("=" * 60)
    if success:
        print("✓ Test completed successfully")
        return 0
    else:
        print("✗ Test failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())
