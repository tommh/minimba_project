#!/usr/bin/env python3
"""
Database Deployment Script for Energy Certificate Project
Deploys all database objects in correct dependency order
"""

import os
import pyodbc
from pathlib import Path
import logging
import re
import sys
from typing import List, Tuple

class DatabaseDeployer:
    def __init__(self, connection_string: str, base_path: str):
        self.connection_string = connection_string
        self.base_path = Path(base_path)
        self.setup_logging()
    
    def setup_logging(self):
        """Setup logging configuration"""
        logging.basicConfig(
            level=logging.INFO, 
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('database_deployment.log'),
                logging.StreamHandler(sys.stdout)
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def clean_sql_content(self, sql_content: str) -> str:
        """Remove USE statements and clean up SQL content"""
        # Remove USE [DatabaseName] statements since we're already connected
        sql_content = re.sub(r'USE\s+\[.*?\]\s*GO\s*', '', sql_content, flags=re.IGNORECASE | re.MULTILINE)
        
        # Remove SSMS-generated comments
        sql_content = re.sub(r'/\*{6}.*?Script Date:.*?\*{6}/', '', sql_content, flags=re.DOTALL)
        
        # Remove extra whitespace
        sql_content = re.sub(r'\n\s*\n\s*\n', '\n\n', sql_content)
        
        return sql_content.strip()
    
    def execute_sql_batches(self, cursor, sql_content: str):
        """Execute SQL content split by GO statements"""
        # Clean the content first
        sql_content = self.clean_sql_content(sql_content)
        
        if not sql_content:
            return
        
        # Split by GO (case insensitive, at start of line)
        batches = re.split(r'^\s*GO\s*$', sql_content, flags=re.MULTILINE | re.IGNORECASE)
        
        for i, batch in enumerate(batches):
            batch = batch.strip()
            if batch:
                try:
                    cursor.execute(batch)
                    # Handle PRINT statements and multiple result sets
                    while cursor.nextset():
                        pass
                except Exception as e:
                    self.logger.error(f"Error executing batch {i+1}: {str(e)}")
                    self.logger.error(f"Batch content (first 200 chars): {batch[:200]}...")
                    raise
    
    def deploy_all(self):
        """Deploy all database objects in correct dependency order"""
        # Order matters! Dependencies must be created first
        deployment_order: List[Tuple[str, str]] = [
            ('schemas', 'schemas'),                           # Create schemas first
            ('tables', 'schema/tables'),                      # Tables next
            ('indexes', 'schema/indexes'),                    # Indexes after tables
            ('functions', 'schema/functions'),                # Functions
            ('views', 'schema/views'),                        # Views after tables and functions
            ('stored_procedures', 'schema/stored_procedures'), # Procedures last
        ]
        
        self.logger.info("🚀 Starting database deployment...")
        
        conn = pyodbc.connect(self.connection_string)
        cursor = conn.cursor()
        
        try:
            for object_type, folder_path in deployment_order:
                self.deploy_object_type(cursor, object_type, folder_path)
            
            conn.commit()
            self.logger.info("✅ All database objects deployed successfully!")
            
        except Exception as e:
            conn.rollback()
            self.logger.error(f"❌ Deployment failed: {e}")
            raise
        finally:
            cursor.close()
            conn.close()
    
    def deploy_object_type(self, cursor, object_type: str, folder_path: str):
        """Deploy all objects of a specific type"""
        full_path = self.base_path / folder_path
        
        if not full_path.exists():
            self.logger.info(f"⏭️  Skipping {object_type} - folder doesn't exist: {full_path}")
            return
        
        sql_files = sorted(full_path.glob('*.sql'))
        if not sql_files:
            self.logger.info(f"⏭️  Skipping {object_type} - no SQL files found in {full_path}")
            return
        
        self.logger.info(f"📁 Deploying {object_type} ({len(sql_files)} files)...")
        
        for sql_file in sql_files:
            try:
                self.logger.info(f"   └─ {sql_file.name}")
                with open(sql_file, 'r', encoding='utf-8') as f:
                    sql_content = f.read()
                    self.execute_sql_batches(cursor, sql_content)
            except Exception as e:
                self.logger.error(f"❌ Failed to deploy {sql_file.name}: {e}")
                raise
    
    def check_database_connection(self) -> bool:
        """Test database connection"""
        try:
            conn = pyodbc.connect(self.connection_string)
            cursor = conn.cursor()
            cursor.execute("SELECT @@VERSION")
            version = cursor.fetchone()[0]
            self.logger.info(f"✅ Connected to: {version}")
            cursor.close()
            conn.close()
            return True
        except Exception as e:
            self.logger.error(f"❌ Database connection failed: {e}")
            return False
    
    def list_existing_schemas(self) -> List[str]:
        """List existing schemas in the database"""
        try:
            conn = pyodbc.connect(self.connection_string)
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sys.schemas ORDER BY name")
            schemas = [row[0] for row in cursor.fetchall()]
            cursor.close()
            conn.close()
            return schemas
        except Exception as e:
            self.logger.error(f"Error listing schemas: {e}")
            return []

def main():
    """Main deployment function"""
    # Get connection string from environment
    conn_str = os.getenv('DATABASE_CONNECTION_STRING')
    if not conn_str:
        print("❌ ERROR: DATABASE_CONNECTION_STRING environment variable not set")
        print("Example: DATABASE_CONNECTION_STRING='Driver={ODBC Driver 17 for SQL Server};Server=server;Database=EnergyCertificate;UID=user;PWD=password'")
        sys.exit(1)
    
    # Initialize deployer
    deployer = DatabaseDeployer(conn_str, '..')
    
    # Test connection
    if not deployer.check_database_connection():
        sys.exit(1)
    
    # List existing schemas
    schemas = deployer.list_existing_schemas()
    deployer.logger.info(f"Existing schemas: {schemas}")
    
    # Deploy everything
    try:
        deployer.deploy_all()
    except Exception as e:
        deployer.logger.error(f"Deployment failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
