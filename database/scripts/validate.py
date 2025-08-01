#!/usr/bin/env python3
"""
Database validation and health check script
"""

import os
import pyodbc
import sys
from pathlib import Path
import logging
from config import get_config

class DatabaseValidator:
    def __init__(self, connection_string: str):
        self.connection_string = connection_string
        self.setup_logging()
    
    def setup_logging(self):
        logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')
        self.logger = logging.getLogger(__name__)
    
    def validate_connection(self) -> bool:
        """Test database connection"""
        try:
            conn = pyodbc.connect(self.connection_string)
            cursor = conn.cursor()
            cursor.execute("SELECT DB_NAME(), GETDATE(), @@VERSION")
            result = cursor.fetchone()
            
            self.logger.info(f"✅ Connected to database: {result[0]}")
            self.logger.info(f"✅ Current time: {result[1]}")
            self.logger.info(f"✅ SQL Server version: {result[2].split(' - ')[0]}")
            
            cursor.close()
            conn.close()
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Connection failed: {e}")
            return False
    
    def validate_schemas(self) -> bool:
        """Validate that required schemas exist"""
        required_schemas = ['dbo', 'ev_enova']
        
        try:
            conn = pyodbc.connect(self.connection_string)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT name 
                FROM sys.schemas 
                WHERE name IN ({})
                ORDER BY name
            """.format(','.join('?' * len(required_schemas))), required_schemas)
            
            existing_schemas = [row[0] for row in cursor.fetchall()]
            missing_schemas = set(required_schemas) - set(existing_schemas)
            
            if missing_schemas:
                self.logger.error(f"❌ Missing schemas: {list(missing_schemas)}")
                return False
            else:
                self.logger.info(f"✅ All required schemas exist: {existing_schemas}")
                return True
                
        except Exception as e:
            self.logger.error(f"❌ Schema validation failed: {e}")
            return False
        finally:
            cursor.close()
            conn.close()
    
    def count_objects(self) -> dict:
        """Count database objects by type"""
        try:
            conn = pyodbc.connect(self.connection_string)
            cursor = conn.cursor()
            
            # Count tables
            cursor.execute("""
                SELECT s.name as schema_name, COUNT(*) as table_count
                FROM sys.tables t
                JOIN sys.schemas s ON t.schema_id = s.schema_id
                GROUP BY s.name
                ORDER BY s.name
            """)
            tables = {row[0]: row[1] for row in cursor.fetchall()}
            
            # Count views
            cursor.execute("""
                SELECT s.name as schema_name, COUNT(*) as view_count
                FROM sys.views v
                JOIN sys.schemas s ON v.schema_id = s.schema_id
                GROUP BY s.name
                ORDER BY s.name
            """)
            views = {row[0]: row[1] for row in cursor.fetchall()}
            
            # Count stored procedures
            cursor.execute("""
                SELECT s.name as schema_name, COUNT(*) as proc_count
                FROM sys.procedures p
                JOIN sys.schemas s ON p.schema_id = s.schema_id
                WHERE p.type = 'P'
                GROUP BY s.name
                ORDER BY s.name
            """)
            procedures = {row[0]: row[1] for row in cursor.fetchall()}
            
            cursor.close()
            conn.close()
            
            return {
                'tables': tables,
                'views': views,
                'procedures': procedures
            }
            
        except Exception as e:
            self.logger.error(f"❌ Object count failed: {e}")
            return {}
    
    def validate_ev_enova_objects(self) -> bool:
        """Validate specific ev_enova schema objects"""
        try:
            conn = pyodbc.connect(self.connection_string)
            cursor = conn.cursor()
            
            # Check for key tables
            cursor.execute("""
                SELECT name 
                FROM sys.tables 
                WHERE schema_id = SCHEMA_ID('ev_enova')
                ORDER BY name
            """)
            tables = [row[0] for row in cursor.fetchall()]
            
            expected_tables = ['Certificate', 'EnergyLabelID', 'OpenAIAnswers']
            missing_tables = [t for t in expected_tables if t not in tables]
            
            if missing_tables:
                self.logger.warning(f"⚠️  Some expected tables missing: {missing_tables}")
            
            self.logger.info(f"✅ Found {len(tables)} tables in ev_enova schema")
            
            cursor.close()
            conn.close()
            return True
            
        except Exception as e:
            self.logger.error(f"❌ ev_enova validation failed: {e}")
            return False
    
    def run_full_validation(self) -> bool:
        """Run all validation checks"""
        self.logger.info("🔍 Running database validation...")
        
        checks = [
            ("Connection", self.validate_connection),
            ("Schemas", self.validate_schemas),
            ("ev_enova Objects", self.validate_ev_enova_objects)
        ]
        
        all_passed = True
        for check_name, check_func in checks:
            self.logger.info(f"\n--- {check_name} Check ---")
            if not check_func():
                all_passed = False
        
        # Object counts
        self.logger.info("\n--- Object Counts ---")
        counts = self.count_objects()
        for obj_type, schema_counts in counts.items():
            self.logger.info(f"{obj_type.title()}:")
            for schema, count in schema_counts.items():
                self.logger.info(f"  {schema}: {count}")
        
        if all_passed:
            self.logger.info("\n✅ All validation checks passed!")
        else:
            self.logger.error("\n❌ Some validation checks failed!")
        
        return all_passed

def main():
    environment = sys.argv[1] if len(sys.argv) > 1 else 'development'
    
    config = get_config(environment)
    if not config['connection_string']:
        print(f"❌ No connection string configured for {environment}")
        sys.exit(1)
    
    validator = DatabaseValidator(config['connection_string'])
    success = validator.run_full_validation()
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
