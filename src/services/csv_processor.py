"""
CSV Processor for Norwegian Energy Certificate Data
Handles importing CSV files into SQL Server database
"""

import pandas as pd
import pyodbc
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional, List
import re

logger = logging.getLogger(__name__)

class CSVProcessor:
    """Service for processing and importing CSV files to database"""
    
    def __init__(self, config):
        self.config = config
        self.connection_string = self._build_connection_string()
        
    def _build_connection_string(self):
        """Build SQL Server connection string using the format that works with named instances"""
        if self.config.DATABASE_TRUSTED_CONNECTION:
            # Use the simple format that worked in our test
            return (
                f"DRIVER={{{self.config.DATABASE_DRIVER}}};"
                f"SERVER={self.config.DATABASE_SERVER};"
                f"DATABASE={self.config.DATABASE_NAME};"
                f"Trusted_Connection=yes;"
                f"TrustServerCertificate=yes;"
                f"Encrypt=yes;"
            )
        else:
            return (
                f"DRIVER={{{self.config.DATABASE_DRIVER}}};"
                f"SERVER={self.config.DATABASE_SERVER};"
                f"DATABASE={self.config.DATABASE_NAME};"
                f"UID={self.config.DATABASE_USERNAME};"
                f"PWD={self.config.DATABASE_PASSWORD};"
                f"TrustServerCertificate=yes;"
                f"Encrypt=yes;"
            )
    
    def analyze_csv_structure(self, csv_path: str) -> Dict[str, Any]:
        """
        Analyze CSV file structure to understand columns and data
        """
        try:
            # Try different separators and encodings
            separators = [',', ';', '\t']
            encodings = ['utf-8', 'utf-8-sig', 'iso-8859-1', 'windows-1252']
            
            best_result = None
            max_columns = 0
            
            for encoding in encodings:
                for sep in separators:
                    try:
                        # Read first few rows to test
                        df_sample = pd.read_csv(csv_path, sep=sep, encoding=encoding, nrows=5)
                        
                        if len(df_sample.columns) > max_columns:
                            max_columns = len(df_sample.columns)
                            best_result = {
                                'separator': sep,
                                'encoding': encoding,
                                'columns': list(df_sample.columns),
                                'sample_data': df_sample.head(3).to_dict('records'),
                                'total_columns': len(df_sample.columns)
                            }
                    except Exception:
                        continue
            
            if best_result:
                # Get total row count
                df_count = pd.read_csv(csv_path, sep=best_result['separator'], 
                                     encoding=best_result['encoding'])
                best_result['total_rows'] = len(df_count)
                
                logger.info(f"CSV Analysis: {best_result['total_columns']} columns, "
                          f"{best_result['total_rows']} rows")
                
                return best_result
            else:
                raise ValueError("Could not determine CSV structure")
                
        except Exception as e:
            logger.error(f"Error analyzing CSV structure: {str(e)}")
            raise
    
    def create_column_mapping(self, csv_columns: List[str]) -> Dict[str, str]:
        """
        Create mapping between CSV columns and database table columns
        """
        # Expected database columns
        expected_db_columns = [
            'Knr', 'Gnr', 'Bnr', 'Snr', 'Fnr', 'Andelsnummer', 'Bygningsnummer',
            'GateAdresse', 'Postnummer', 'Poststed', 'BruksEnhetsNummer', 
            'Organisasjonsnummer', 'Bygningskategori', 'Byggear', 'Energikarakter',
            'Oppvarmingskarakter', 'Utstedelsesdato', 'TypeRegistrering', 'Attestnummer',
            'BeregnetLevertEnergiTotaltkWhm2', 'BeregnetFossilandel', 'Materialvalg',
            'HarEnergiVurdering', 'EnergiVurderingDato'
        ]
        
        # Create 1:1 mapping for columns that exist in both CSV and DB
        mapping = {}
        
        for csv_col in csv_columns:
            if csv_col in expected_db_columns:
                mapping[csv_col] = csv_col
                logger.info(f"Mapped CSV column '{csv_col}' -> DB column '{csv_col}'")
        
        logger.info(f"Created mapping for {len(mapping)} columns")
        return mapping
    
    def clean_and_validate_data(self, df: pd.DataFrame, mapping: Dict[str, str]) -> pd.DataFrame:
        """
        Clean and validate data before database insertion
        """
        cleaned_df = df.copy()
        logger.info("Cleaning and validating data...")
        
        # Clean numeric fields
        numeric_fields = ['Knr', 'Gnr', 'Bnr', 'Snr', 'Fnr', 'Andelsnummer', 
                         'Bygningsnummer', 'Postnummer', 'Organisasjonsnummer', 'Byggear']
        
        for field in numeric_fields:
            if field in cleaned_df.columns:
                cleaned_df[field] = cleaned_df[field].replace('', pd.NA)
                cleaned_df[field] = pd.to_numeric(cleaned_df[field], errors='coerce')
                cleaned_df[field] = cleaned_df[field].astype('Int64')
        
        # Clean datetime fields
        datetime_fields = ['Utstedelsesdato', 'EnergiVurderingDato']
        
        for field in datetime_fields:
            if field in cleaned_df.columns:
                cleaned_df[field] = cleaned_df[field].replace('', pd.NA)
                cleaned_df[field] = pd.to_datetime(cleaned_df[field], errors='coerce')
        
        # Clean string fields
        string_fields = ['GateAdresse', 'Poststed', 'BruksEnhetsNummer', 'Bygningskategori',
                        'Energikarakter', 'Oppvarmingskarakter', 'TypeRegistrering', 
                        'Attestnummer', 'BeregnetLevertEnergiTotaltkWhm2', 'BeregnetFossilandel',
                        'Materialvalg', 'HarEnergiVurdering']
        
        for field in string_fields:
            if field in cleaned_df.columns:
                cleaned_df[field] = cleaned_df[field].replace('', None)
                cleaned_df[field] = cleaned_df[field].astype(str).str.strip()
                cleaned_df[field] = cleaned_df[field].replace('nan', None)
        
        # Special handling for BeregnetFossilandel - convert comma decimal to dot
        if 'BeregnetFossilandel' in cleaned_df.columns:
            cleaned_df['BeregnetFossilandel'] = cleaned_df['BeregnetFossilandel'].str.replace(',', '.')
        
        # Convert HarEnergiVurdering boolean handling
        if 'HarEnergiVurdering' in cleaned_df.columns:
            cleaned_df['HarEnergiVurdering'] = cleaned_df['HarEnergiVurdering'].map({
                'True': 'True', 'False': 'False', True: 'True', False: 'False', None: None
            })
        
        # Remove empty rows
        cleaned_df = cleaned_df.dropna(how='all')
        
        logger.info(f"Data cleaned: {len(cleaned_df)} rows ready for import")
        return cleaned_df
    
    def check_existing_records(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Check which records already exist in the database based on Attestnummer
        Uses batching to handle large datasets
        """
        try:
            if 'Attestnummer' not in df.columns:
                logger.warning("No Attestnummer column found - cannot check for duplicates")
                return {
                    'existing_count': 0,
                    'new_count': len(df),
                    'existing_attestnummer': [],
                    'new_records_df': df
                }
            
            attestnummer_list = df['Attestnummer'].dropna().tolist()
            
            if not attestnummer_list:
                return {
                    'existing_count': 0,
                    'new_count': len(df),
                    'existing_attestnummer': [],
                    'new_records_df': df
                }
            
            logger.info(f"Checking for existing records among {len(attestnummer_list):,} Attestnummer values...")
            
            # Process in batches to avoid SQL parameter limits
            batch_size = 1000  # SQL Server can handle ~2100 parameters, use 1000 for safety
            all_existing = []
            
            with pyodbc.connect(self.connection_string) as conn:
                cursor = conn.cursor()
                
                # Process attestnummer_list in batches
                for i in range(0, len(attestnummer_list), batch_size):
                    batch = attestnummer_list[i:i + batch_size]
                    
                    # Create parameterized query for this batch
                    placeholders = ','.join(['?' for _ in batch])
                    check_sql = f"""
                        SELECT [Attestnummer] 
                        FROM [ev_enova].[EnovaApi_ImpHist] 
                        WHERE [Attestnummer] IN ({placeholders})
                    """
                    
                    cursor.execute(check_sql, batch)
                    batch_results = cursor.fetchall()
                    
                    # Add this batch's results to the overall list
                    all_existing.extend([row[0] for row in batch_results])
                    
                    # Log progress for large datasets
                    if len(attestnummer_list) > 10000:
                        processed = min(i + batch_size, len(attestnummer_list))
                        logger.info(f"Duplicate check progress: {processed:,}/{len(attestnummer_list):,} processed")
                
                # Filter out existing records from DataFrame
                new_records_df = df[~df['Attestnummer'].isin(all_existing)]
                
                result = {
                    'existing_count': len(all_existing),
                    'new_count': len(new_records_df),
                    'existing_attestnummer': all_existing,
                    'new_records_df': new_records_df
                }
                
                logger.info(f"Duplicate check completed: {result['existing_count']:,} existing, "
                          f"{result['new_count']:,} new records")
                
                return result
                
        except Exception as e:
            logger.error(f"Error checking existing records: {str(e)}")
            # If check fails, return all records as new to avoid data loss
            return {
                'existing_count': 0,
                'new_count': len(df),
                'existing_attestnummer': [],
                'new_records_df': df,
                'check_error': str(e)
            }
    
    def insert_to_database(self, df: pd.DataFrame, batch_size: int = 1000, skip_duplicates: bool = True) -> Dict[str, Any]:
        """
        Insert DataFrame to database table
        """
        try:
            # Check for existing records if skip_duplicates is True
            if skip_duplicates:
                duplicate_check = self.check_existing_records(df)
                df_to_insert = duplicate_check['new_records_df']
                skipped_count = duplicate_check['existing_count']
                
                if skipped_count > 0:
                    logger.info(f"Skipping {skipped_count} records that already exist in database")
                
                if len(df_to_insert) == 0:
                    logger.info("No new records to insert - all records already exist")
                    return {
                        'success': True,
                        'total_rows': len(df),
                        'inserted_rows': 0,
                        'skipped_rows': skipped_count,
                        'failed_rows': 0,
                        'message': 'All records already exist in database'
                    }
            else:
                df_to_insert = df
                skipped_count = 0
            
            total_rows = len(df_to_insert)
            inserted_rows = 0
            failed_rows = 0
            errors = []
            
            logger.info(f"Starting database insert: {total_rows} rows in batches of {batch_size}")
            
            # Build INSERT statement
            columns = list(df_to_insert.columns)
            placeholders = ', '.join(['?' for _ in columns])
            column_names = ', '.join([f'[{col}]' for col in columns])
            
            insert_sql = f"""
                INSERT INTO [ev_enova].[EnovaApi_ImpHist] ({column_names})
                VALUES ({placeholders})
            """
            
            with pyodbc.connect(self.connection_string) as conn:
                cursor = conn.cursor()
                
                # Process in batches
                for start_idx in range(0, total_rows, batch_size):
                    end_idx = min(start_idx + batch_size, total_rows)
                    batch_df = df_to_insert.iloc[start_idx:end_idx]
                    
                    try:
                        # Convert DataFrame to list of tuples for insertion
                        batch_data = []
                        for _, row in batch_df.iterrows():
                            row_tuple = tuple(None if pd.isna(val) else val for val in row)
                            batch_data.append(row_tuple)
                        
                        # Execute batch insert
                        cursor.executemany(insert_sql, batch_data)
                        conn.commit()
                        
                        batch_size_actual = len(batch_data)
                        inserted_rows += batch_size_actual
                        
                        logger.info(f"Inserted batch {start_idx//batch_size + 1}: "
                                  f"{batch_size_actual} rows ({inserted_rows}/{total_rows})")
                        
                    except Exception as batch_error:
                        error_msg = f"Batch {start_idx}-{end_idx} failed: {str(batch_error)}"
                        logger.error(error_msg)
                        errors.append(error_msg)
                        failed_rows += len(batch_df)
                        conn.rollback()
            
            result = {
                'success': inserted_rows > 0 or (total_rows == 0 and skipped_count > 0),
                'total_rows': len(df),
                'inserted_rows': inserted_rows,
                'skipped_rows': skipped_count,
                'failed_rows': failed_rows,
                'errors': errors,
                'insert_rate': (inserted_rows / total_rows) * 100 if total_rows > 0 else 100
            }
            
            logger.info(f"Database insert completed: {inserted_rows} inserted, "
                       f"{skipped_count} skipped, {failed_rows} failed")
            
            return result
            
        except Exception as e:
            error_msg = f"Database insert failed: {str(e)}"
            logger.error(error_msg)
            return {
                'success': False,
                'error': error_msg,
                'total_rows': len(df) if df is not None else 0,
                'inserted_rows': 0,
                'skipped_rows': 0,
                'failed_rows': len(df) if df is not None else 0
            }
    
    def process_csv_file(self, csv_path: str, batch_size: int = 1000, skip_duplicates: bool = True) -> Dict[str, Any]:
        """
        Complete CSV processing workflow
        """
        try:
            logger.info(f"Starting CSV processing: {csv_path}")
            
            # Step 1: Analyze CSV structure
            analysis = self.analyze_csv_structure(csv_path)
            
            # Step 2: Read full CSV
            logger.info("Reading full CSV file...")
            df = pd.read_csv(csv_path, 
                           sep=analysis['separator'], 
                           encoding=analysis['encoding'])
            
            logger.info(f"Loaded {len(df)} rows with {len(df.columns)} columns")
            
            # Step 3: Create column mapping
            mapping = self.create_column_mapping(list(df.columns))
            
            if not mapping:
                raise ValueError("No column mappings found - CSV structure doesn't match expected format")
            
            # Step 4: Clean and validate data
            cleaned_df = self.clean_and_validate_data(df, mapping)
            
            # Step 5: Insert to database with duplicate checking
            insert_result = self.insert_to_database(cleaned_df, batch_size, skip_duplicates)
            
            # Combine results
            result = {
                'success': insert_result['success'],
                'csv_analysis': analysis,
                'column_mapping': mapping,
                'database_insert': insert_result,
                'total_processed': len(df),
                'total_inserted': insert_result.get('inserted_rows', 0),
                'total_skipped': insert_result.get('skipped_rows', 0)
            }
            
            logger.info(f"CSV processing completed: "
                       f"{result['total_inserted']} inserted, "
                       f"{result['total_skipped']} skipped")
            
            return result
            
        except Exception as e:
            error_msg = f"CSV processing failed: {str(e)}"
            logger.error(error_msg)
            return {
                'success': False,
                'error': error_msg
            }

def test_database_connection(config):
    """Test database connection without logging sensitive information"""
    try:
        import pyodbc
        
        # Build connection string using the same format that worked
        if config.DATABASE_TRUSTED_CONNECTION:
            conn_str = (
                f"DRIVER={{{config.DATABASE_DRIVER}}};"
                f"SERVER={config.DATABASE_SERVER};"
                f"DATABASE={config.DATABASE_NAME};"
                f"Trusted_Connection=yes;"
                f"TrustServerCertificate=yes;"
                f"Encrypt=yes;"
            )
        else:
            conn_str = (
                f"DRIVER={{{config.DATABASE_DRIVER}}};"
                f"SERVER={config.DATABASE_SERVER};"
                f"DATABASE={config.DATABASE_NAME};"
                f"UID={config.DATABASE_USERNAME};"
                f"PWD={config.DATABASE_PASSWORD};"
                f"TrustServerCertificate=yes;"
                f"Encrypt=yes;"
            )
        
        with pyodbc.connect(conn_str, timeout=30) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
            logger.info("✓ Database connection successful")
            return True
    except Exception as e:
        # Don't log the full connection string or password
        logger.error(f"✗ Database connection failed: {str(e)}")
        return False
