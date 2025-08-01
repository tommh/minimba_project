#!/usr/bin/env python3
"""
Selective deployment script for specific database objects
"""

import argparse
import os
import sys
from pathlib import Path
from deploy import DatabaseDeployer

def deploy_specific_objects(connection_string: str, base_path: str, object_types: list, specific_files: list = None):
    """Deploy specific object types or files"""
    deployer = DatabaseDeployer(connection_string, base_path)
    
    if not deployer.check_database_connection():
        return False
    
    # Map of object types to folder paths
    type_mapping = {
        'schemas': 'schemas',
        'tables': 'schema/tables',
        'views': 'schema/views',
        'procedures': 'schema/stored_procedures',
        'stored_procedures': 'schema/stored_procedures',
        'functions': 'schema/functions',
        'indexes': 'schema/indexes'
    }
    
    conn = deployer.connection_string
    try:
        import pyodbc
        conn_obj = pyodbc.connect(conn)
        cursor = conn_obj.cursor()
        
        if specific_files:
            # Deploy specific files
            deployer.logger.info(f"🎯 Deploying specific files: {specific_files}")
            for file_path in specific_files:
                full_path = Path(base_path) / file_path
                if full_path.exists():
                    deployer.logger.info(f"   └─ {full_path.name}")
                    with open(full_path, 'r', encoding='utf-8') as f:
                        sql_content = f.read()
                        deployer.execute_sql_batches(cursor, sql_content)
                else:
                    deployer.logger.error(f"❌ File not found: {full_path}")
                    return False
        else:
            # Deploy specific object types
            for obj_type in object_types:
                if obj_type in type_mapping:
                    folder_path = type_mapping[obj_type]
                    deployer.deploy_object_type(cursor, obj_type, folder_path)
                else:
                    deployer.logger.error(f"❌ Unknown object type: {obj_type}")
                    return False
        
        conn_obj.commit()
        deployer.logger.info("✅ Selective deployment completed!")
        return True
        
    except Exception as e:
        conn_obj.rollback()
        deployer.logger.error(f"❌ Selective deployment failed: {e}")
        return False
    finally:
        cursor.close()
        conn_obj.close()

def main():
    parser = argparse.ArgumentParser(description='Deploy specific database object types or files')
    parser.add_argument('--types', nargs='+', 
                       choices=['schemas', 'tables', 'views', 'procedures', 'stored_procedures', 'functions', 'indexes'],
                       help='Object types to deploy')
    parser.add_argument('--files', nargs='+', help='Specific files to deploy (relative to database folder)')
    parser.add_argument('--environment', default='development', 
                       choices=['development', 'staging', 'production'],
                       help='Target environment')
    
    args = parser.parse_args()
    
    if not args.types and not args.files:
        parser.error("Must specify either --types or --files")
    
    # Get connection string
    from config import get_config
    config = get_config(args.environment)
    
    if not config['connection_string']:
        print(f"❌ No connection string configured for {args.environment}")
        sys.exit(1)
    
    # Deploy
    success = deploy_specific_objects(
        config['connection_string'], 
        '..', 
        args.types or [], 
        args.files
    )
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
