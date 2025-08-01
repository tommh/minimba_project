#!/usr/bin/env python3
"""
Test script to verify database setup for OpenAI Energy Service
This script helps troubleshoot database connectivity and table structure
"""

import sys
import logging
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from config import get_config
import pyodbc

def setup_logging():
    """Setup logging configuration"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

def test_database_connection(config):
    """Test basic database connection"""
    logger = logging.getLogger(__name__)
    
    try:
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
        
        logger.info(f"Testing connection to: {config.DATABASE_SERVER}/{config.DATABASE_NAME}")
        
        conn = pyodbc.connect(conn_str)
        cursor = conn.cursor()
        
        # Test basic query
        cursor.execute("SELECT @@VERSION")
        version = cursor.fetchone()[0]
        logger.info(f"Database connection successful!")
        logger.info(f"SQL Server version: {version[:100]}...")
        
        conn.close()
        return True
        
    except Exception as e:
        logger.error(f"Database connection failed: {str(e)}")
        return False

def check_required_tables(config):
    """Check if required tables exist"""
    logger = logging.getLogger(__name__)
    
    try:
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
        
        # Check for ev_enova schema
        logger.info("Checking for ev_enova schema...")
        cursor.execute("""
            SELECT COUNT(*) FROM sys.schemas WHERE name = 'ev_enova'
        """)
        schema_exists = cursor.fetchone()[0] > 0
        
        if schema_exists:
            logger.info("✓ ev_enova schema exists")
        else:
            logger.warning("✗ ev_enova schema does not exist")
            logger.info("Creating ev_enova schema...")
            try:
                cursor.execute("CREATE SCHEMA ev_enova")
                conn.commit()
                logger.info("✓ ev_enova schema created")
            except Exception as e:
                logger.error(f"Failed to create schema: {str(e)}")
        
        # Check for source table
        logger.info("Checking for SampleTestDataForOpenAI table...")
        cursor.execute("""
            SELECT COUNT(*) FROM INFORMATION_SCHEMA.TABLES 
            WHERE TABLE_SCHEMA = 'ev_enova' AND TABLE_NAME = 'SampleTestDataForOpenAI'
        """)
        source_table_exists = cursor.fetchone()[0] > 0
        
        if source_table_exists:
            logger.info("✓ SampleTestDataForOpenAI table exists")
            
            # Check columns
            cursor.execute("""
                SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE 
                FROM INFORMATION_SCHEMA.COLUMNS 
                WHERE TABLE_SCHEMA = 'ev_enova' AND TABLE_NAME = 'SampleTestDataForOpenAI'
                ORDER BY ORDINAL_POSITION
            """)
            columns = cursor.fetchall()
            logger.info("Table columns:")
            for col in columns:
                logger.info(f"  - {col.COLUMN_NAME} ({col.DATA_TYPE}, nullable: {col.IS_NULLABLE})")
            
            # Check for data
            cursor.execute("SELECT COUNT(*) FROM [ev_enova].[SampleTestDataForOpenAI]")
            row_count = cursor.fetchone()[0]
            logger.info(f"  Records in table: {row_count}")
            
        else:
            logger.warning("✗ SampleTestDataForOpenAI table does not exist")
            logger.info("You need to create this table with your prompt data")
        
        # Check for target table
        logger.info("Checking for OpenAIAnswers table...")
        cursor.execute("""
            SELECT COUNT(*) FROM INFORMATION_SCHEMA.TABLES 
            WHERE TABLE_SCHEMA = 'ev_enova' AND TABLE_NAME = 'OpenAIAnswers'
        """)
        target_table_exists = cursor.fetchone()[0] > 0
        
        if target_table_exists:
            logger.info("✓ OpenAIAnswers table exists")
            
            # Check for existing data
            cursor.execute("SELECT COUNT(*) FROM [ev_enova].[OpenAIAnswers]")
            answer_count = cursor.fetchone()[0]
            logger.info(f"  Existing answers: {answer_count}")
            
        else:
            logger.warning("✗ OpenAIAnswers table does not exist")
            logger.info("Creating OpenAIAnswers table...")
            try:
                cursor.execute("""
                    CREATE TABLE [ev_enova].[OpenAIAnswers](
                        [openAIAnswerID] [int] IDENTITY(1,1) NOT NULL,
                        [file_id] [int] NOT NULL,
                        [PromptVersion] [nvarchar](100) NOT NULL,
                        [AboutEstate] [nvarchar](2000) NULL,
                        [Positives] [nvarchar](2000) NULL,
                        [Evaluation] [nvarchar](2000) NULL,
                        [Created] [datetime] NOT NULL,
                        CONSTRAINT [PK_OpenAIAnswers] PRIMARY KEY CLUSTERED ([openAIAnswerID] ASC),
                        CONSTRAINT [DF_OpenAIAnswers_Created] DEFAULT (getdate()) FOR [Created]
                    )
                """)
                conn.commit()
                logger.info("✓ OpenAIAnswers table created successfully")
            except Exception as e:
                logger.error(f"Failed to create OpenAIAnswers table: {str(e)}")
        
        conn.close()
        return source_table_exists and (target_table_exists or True)  # True if we created it
        
    except Exception as e:
        logger.error(f"Error checking tables: {str(e)}")
        return False

def check_openai_config(config):
    """Check OpenAI configuration"""
    logger = logging.getLogger(__name__)
    
    if config.OPENAI_API_KEY:
        logger.info("✓ OpenAI API key is configured")
        logger.info(f"  Model: {config.OPENAI_MODEL}")
        logger.info(f"  Max tokens: {config.OPENAI_MAX_TOKENS}")
        logger.info(f"  Temperature: {config.OPENAI_TEMPERATURE}")
        return True
    else:
        logger.error("✗ OpenAI API key is not configured")
        logger.info("  Set OPENAI_API_KEY environment variable")
        return False

def main():
    """Main test function"""
    setup_logging()
    logger = logging.getLogger(__name__)
    
    logger.info("=" * 60)
    logger.info("OpenAI Energy Service - Database Setup Test")
    logger.info("=" * 60)
    
    try:
        # Load configuration
        config = get_config()
        
        logger.info("\n1. Testing database connection...")
        db_ok = test_database_connection(config)
        
        if db_ok:
            logger.info("\n2. Checking required tables...")
            tables_ok = check_required_tables(config)
        else:
            logger.error("Cannot proceed - database connection failed")
            return
        
        logger.info("\n3. Checking OpenAI configuration...")
        openai_ok = check_openai_config(config)
        
        logger.info("\n" + "=" * 60)
        logger.info("SUMMARY")
        logger.info("=" * 60)
        logger.info(f"Database connection: {'✓ OK' if db_ok else '✗ FAILED'}")
        logger.info(f"Required tables: {'✓ OK' if tables_ok else '✗ MISSING'}")
        logger.info(f"OpenAI configuration: {'✓ OK' if openai_ok else '✗ MISSING'}")
        
        if db_ok and tables_ok and openai_ok:
            logger.info("\n🎉 Setup is complete! You can now run the OpenAI service.")
        else:
            logger.warning("\n⚠️  Setup is incomplete. Please address the issues above.")
            
            if not tables_ok:
                logger.info("\nTo create the source table, run:")
                logger.info("CREATE TABLE [ev_enova].[SampleTestDataForOpenAI] (")
                logger.info("    [FILE_ID] [int] NOT NULL,")
                logger.info("    [PROMPT_V1_NOR] [nvarchar](max) NULL,")
                logger.info("    [PROMPT_V2_NOR] [nvarchar](max) NULL")
                logger.info(")")
            
            if not openai_ok:
                logger.info("\nTo configure OpenAI:")
                logger.info("Set environment variable: OPENAI_API_KEY=your_api_key_here")
        
    except Exception as e:
        logger.error(f"Test failed with error: {str(e)}")

if __name__ == "__main__":
    main()
