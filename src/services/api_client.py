"""
Enova API Client for Energy Certificate Data Processing
Handles API calls to retrieve detailed energy certificate information
"""

import pyodbc
import requests
import time
import json
from requests.adapters import HTTPAdapter
from datetime import datetime
from urllib3.util.retry import Retry
from typing import Dict, Any, List, Optional
import logging

logger = logging.getLogger(__name__)

class EnovaApiClient:
    """Client for interacting with Enova Energy Certificate API"""
    
    def __init__(self, config):
        self.config = config
        self.api_url = f"{config.ENOVA_API_BASE_URL}/Energiattest"
        self.session = self._setup_session()
        self.insert_count = 0
        self.api_call_count = 0
        self.log_count = 0
        
        # Rate limiting configuration
        self.requests_per_second = 2  # Adjust based on API limits
        self.delay_between_requests = 1.0 / self.requests_per_second
    
    def _setup_session(self):
        """Setup requests session with retry strategy and headers"""
        session = requests.Session()
        
        # Configure retry strategy
        retry_strategy = Retry(
            total=self.config.ENOVA_API_RETRY_COUNT,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        # Set headers
        headers = {
            "Content-Type": "application/json",
            "Cache-Control": "no-cache"
        }
        
        # Add API key
        if self.config.ENOVA_API_KEY:
            headers["x-api-key"] = self.config.ENOVA_API_KEY
        
        session.headers.update(headers)
        return session
    
    def _get_database_connection(self):
        """Get database connection using configuration"""
        try:
            # Build connection string based on configuration
            if self.config.DATABASE_TRUSTED_CONNECTION:
                conn_str = (
                    f"DRIVER={{{self.config.DATABASE_DRIVER}}};"
                    f"SERVER={self.config.DATABASE_SERVER};"
                    f"DATABASE={self.config.DATABASE_NAME};"
                    f"Trusted_Connection=yes;"
                )
            else:
                conn_str = (
                    f"DRIVER={{{self.config.DATABASE_DRIVER}}};"
                    f"SERVER={self.config.DATABASE_SERVER};"
                    f"DATABASE={self.config.DATABASE_NAME};"
                    f"UID={self.config.DATABASE_USERNAME};"
                    f"PWD={self.config.DATABASE_PASSWORD};"
                )
            
            logger.info(f"Connecting to database: {self.config.DATABASE_SERVER}/{self.config.DATABASE_NAME}")
            return pyodbc.connect(conn_str)
            
        except Exception as e:
            logger.error(f"Database connection failed: {str(e)}")
            raise
    
    def get_api_parameters(self, top_rows: int = 10) -> List[Dict[str, Any]]:
        """
        Get parameters for API calls from stored procedure
        
        Args:
            top_rows: Number of rows to retrieve (default: 10)
            
        Returns:
            List of parameter dictionaries
        """
        conn = None
        try:
            conn = self._get_database_connection()
            cursor = conn.cursor()
            
            # Call stored procedure
            logger.info(f"Calling stored procedure with TopRows = {top_rows}")
            cursor.execute("{CALL ev_enova.Get_Enova_API_Parameters (?)}", top_rows)
            rows = cursor.fetchall()
            
            logger.info(f"Retrieved {len(rows)} rows from stored procedure")
            
            # Convert rows to list of dictionaries
            parameters = []
            for row in rows:
                param_dict = {
                    'certificate_id': row.CertificateID,
                    'kommunenummer': row.kommunenummer,
                    'gardsnummer': row.gardsnummer, 
                    'bruksnummer': row.bruksnummer,
                    'seksjonsnummer': row.seksjonsnummer,
                    'bruksenhetnummer': row.bruksenhetnummer,
                    'bygningsnummer': row.bygningsnummer,
                    'attestnummer': row.Attestnummer
                }
                parameters.append(param_dict)
            
            return parameters
            
        except Exception as e:
            logger.error(f"Error retrieving API parameters: {str(e)}")
            raise
        finally:
            if conn:
                conn.close()
    
    def log_api_parameters(self, parameters: List[Dict[str, Any]], batch_datetime: datetime) -> int:
        """
        Log all API parameters before processing
        
        Args:
            parameters: List of parameter dictionaries
            batch_datetime: Timestamp for this batch
            
        Returns:
            Number of parameters logged
        """
        conn = None
        log_count = 0
        
        try:
            conn = self._get_database_connection()
            cursor = conn.cursor()
            
            logger.info("Logging all parameters...")
            for param in parameters:
                try:
                    cursor.execute("""
                        INSERT INTO [ev_enova].[EnovaApi_Energiattest_url_log] 
                        (CertificateID, LogDate, kommunenummer, gardsnummer, bruksnummer, 
                         seksjonsnummer, bruksenhetnummer, bygningsnummer, Attestnummer, 
                         records_returned, status_message, Created)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        param['certificate_id'],
                        batch_datetime,
                        param['kommunenummer'],
                        param['gardsnummer'], 
                        param['bruksnummer'],
                        param['seksjonsnummer'],
                        param['bruksenhetnummer'],
                        param['bygningsnummer'],
                        param['attestnummer'],
                        None,  # Will be updated after API call
                        'Pending',  # Initial status
                        batch_datetime
                    ))
                    log_count += 1
                except Exception as e:
                    logger.error(f"Error logging parameters for CertificateID {param['certificate_id']}: {e}")
            
            conn.commit()
            logger.info(f"Logged {log_count} parameter sets to log table")
            return log_count
            
        except Exception as e:
            logger.error(f"Error logging API parameters: {str(e)}")
            raise
        finally:
            if conn:
                conn.close()
    
    def update_api_log(self, certificate_id: int, records_returned: int, status_message: str) -> bool:
        """
        Update the API log with results after processing
        
        Args:
            certificate_id: The certificate ID that was processed
            records_returned: Number of records returned from API
            status_message: Status message (Success, No records found, Error, etc.)
            
        Returns:
            True if update successful, False otherwise
        """
        conn = None
        try:
            conn = self._get_database_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                UPDATE [ev_enova].[EnovaApi_Energiattest_url_log] 
                SET records_returned = ?, 
                    status_message = ?
                WHERE CertificateID = ? 
                  AND status_message = 'Pending'
            """, (
                records_returned,
                status_message,
                certificate_id
            ))
            
            conn.commit()
            rows_affected = cursor.rowcount
            
            if rows_affected > 0:
                logger.debug(f"Updated log for CertificateID {certificate_id}: {records_returned} records, status: {status_message}")
                return True
            else:
                logger.warning(f"No pending log entry found for CertificateID {certificate_id}")
                return False
            
        except Exception as e:
            logger.error(f"Error updating API log for CertificateID {certificate_id}: {str(e)}")
            return False
        finally:
            if conn:
                conn.close()
    
    def call_energiattest_api(self, parameters: Dict[str, Any]) -> Optional[List[Dict[str, Any]]]:
        """
        Call the Energiattest API with given parameters
        
        Args:
            parameters: Dictionary containing API parameters
            
        Returns:
            List of energy certificate data or None if failed
        """
        # Prepare payload, removing None/empty values
        payload = {
            k: str(v) if isinstance(v, int) or v is not None else v
            for k, v in {
                "kommunenummer": parameters.get('kommunenummer'),
                "gardsnummer": parameters.get('gardsnummer'),
                "bruksnummer": parameters.get('bruksnummer'),
                "seksjonsnummer": parameters.get('seksjonsnummer'),
                "bruksenhetnummer": parameters.get('bruksenhetnummer'),
                "bygningsnummer": parameters.get('bygningsnummer')
            }.items()
            if v not in (None, "", " ")
        }
        
        try:
            # Add delay before API call (except for first request)
            if self.api_call_count > 0:
                time.sleep(self.delay_between_requests)
            
            response = self.session.post(
                self.api_url, 
                json=payload, 
                timeout=self.config.ENOVA_API_TIMEOUT
            )
            self.api_call_count += 1
            
            # Handle rate limiting
            if response.status_code == 429:
                logger.warning("Rate limited, waiting 60 seconds...")
                time.sleep(60)
                response = self.session.post(
                    self.api_url, 
                    json=payload, 
                    timeout=self.config.ENOVA_API_TIMEOUT
                )
                self.api_call_count += 1
            
            if response.status_code != 200:
                if response.status_code == 400:
                    try:
                        error_data = response.json()
                        if ("errors" in error_data and 
                            "EnergiattestResponse" in error_data["errors"] and
                            any("more than twenty five" in str(err).lower() for err in error_data["errors"]["EnergiattestResponse"])):
                            logger.warning(f"API returned too many results (25+ eiendommer): {response.text}")
                            return "TOO_MANY_RESULTS"  # Special return value
                    except:
                        pass  # Fall through to general error handling
                
                logger.error(f"API call failed with status {response.status_code}: {response.text}")
                return None
            
            return response.json()
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Request error: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error during API call: {e}")
            return None
    
    def save_energiattest_data(self, data_list: List[Dict[str, Any]], 
                             original_params: Dict[str, Any], 
                             batch_datetime: datetime) -> int:
        """
        Save energy certificate data to database
        
        Args:
            data_list: List of energy certificate data from API
            original_params: Original parameters used for the API call
            batch_datetime: Timestamp for this batch
            
        Returns:
            Number of records inserted
        """
        conn = None
        insert_count = 0
        
        try:
            conn = self._get_database_connection()
            cursor = conn.cursor()
            
            for data in data_list:
                try:
                    # Extract energiattest data
                    energiattest = data.get("energiattest", {})
                    attestnummer = energiattest.get("attestnummer")
                    attest_url = energiattest.get("attestUrl")
                    filename = attest_url.split("/")[-1].split(".pdf")[0] if attest_url else None
                    energikarakter = str(energiattest.get("energikarakter")) if energiattest.get("energikarakter") is not None else None
                    oppvarmingskarakter = str(energiattest.get("oppvarmingskarakter")) if energiattest.get("oppvarmingskarakter") is not None else None
                    utstedelsesdato = energiattest.get("utstedelsesdato")
                    
                    # Extract enhet data
                    enhet = data.get("enhet", {})
                    bruksareal = enhet.get("bruksareal")
                    
                    # Extract adresse data
                    adresse = enhet.get("adresse", {})
                    adresse_gatenavn = adresse.get("gatenavn")
                    adresse_postnummer = adresse.get("postnummer")
                    adresse_poststed = adresse.get("poststed")
                    
                    # Extract registering data
                    registering = energiattest.get("registering", {})
                    registering_type = registering.get("type")
                    beregnet_levert_energi_totalt_kwh_m2 = registering.get("beregnetLevertEnergiTotaltkWhm2")
                    beregnet_levert_energi_totalt_kwh = registering.get("beregnetLevertEnergiTotaltkWh")
                    har_energivurdering = str(registering.get("harEnergivurdering")) if registering.get("harEnergivurdering") is not None else None
                    energivurdering_dato = registering.get("energivurderingdato")
                    beregnet_fossilandel = registering.get("beregnetFossilandel")
                    materialvalg = registering.get("materialvalg")
                    
                    # Extract organisasjonsnummer
                    organisasjonsnummer = data.get("organisasjonsnummer")
                    
                    # Extract matrikkel data
                    matrikkel = enhet.get("matrikkel", {})
                    matrikkel_kommunenummer = matrikkel.get("kommunenummer")
                    matrikkel_gardsnummer = matrikkel.get("gårdsnummer")
                    matrikkel_bruksnummer = matrikkel.get("bruksnummer")
                    matrikkel_festenummer = matrikkel.get("festenummer")
                    matrikkel_seksjonsnummer = matrikkel.get("seksjonsnummer")
                    matrikkel_andelsnummer = matrikkel.get("andelsnummer")
                    matrikkel_bruksenhetsnummer = matrikkel.get("bruksenhetsnummer")
                    
                    # Extract bygg data
                    bygg = enhet.get("bygg", {})
                    bygg_bygningsnummer = bygg.get("bygningsnummer")
                    bygg_byggear = str(bygg.get("byggeår")) if bygg.get("byggeår") is not None else None
                    bygg_kategori = bygg.get("kategori")
                    bygg_type = bygg.get("type")
                    
                    # Insert data into database
                    cursor.execute("""
                        INSERT INTO [ev_enova].[EnovaApi_Energiattest_url] (
                            ImportDate, CertificateID, paramKommunenummer, paramGardsnummer, 
                            paramBruksnummer, paramSeksjonsnummer, paramBruksenhetnummer, 
                            paramBygningsnummer, attestnummer, merkenummer, bruksareal, 
                            energikarakter, oppvarmingskarakter, attest_url, 
                            matrikkel_kommunenummer, matrikkel_gardsnummer, matrikkel_bruksnummer,
                            matrikkel_festenummer, matrikkel_seksjonsnummer, matrikkel_andelsnummer,
                            matrikkel_bruksenhetsnummer, bygg_bygningsnummer, bygg_byggear,
                            bygg_kategori, bygg_type, utstedelsesdato,
                            adresse_gatenavn, adresse_postnummer, adresse_poststed,
                            registering_RegisteringType, registering_BeregnetLevertEnergiTotaltkWhm2,
                            registering_BeregnetLevertEnergiTotaltkWh, registering_HarEnergivurdering,
                            registering_Energivurderingdato, registering_BeregnetFossilandel,
                            registering_Materialvalg, OrganisasjonsNummer, Created
                        )
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        batch_datetime, 
                        original_params['certificate_id'],
                        original_params.get('kommunenummer'),
                        original_params.get('gardsnummer'), 
                        original_params.get('bruksnummer'),
                        original_params.get('seksjonsnummer'), 
                        original_params.get('bruksenhetnummer'), 
                        original_params.get('bygningsnummer'),
                        attestnummer, filename, bruksareal, energikarakter, oppvarmingskarakter, 
                        attest_url, matrikkel_kommunenummer, matrikkel_gardsnummer, 
                        matrikkel_bruksnummer, matrikkel_festenummer, matrikkel_seksjonsnummer,
                        matrikkel_andelsnummer, matrikkel_bruksenhetsnummer, bygg_bygningsnummer,
                        bygg_byggear, bygg_kategori, bygg_type, utstedelsesdato,
                        adresse_gatenavn, adresse_postnummer, adresse_poststed,
                        registering_type, beregnet_levert_energi_totalt_kwh_m2,
                        beregnet_levert_energi_totalt_kwh, har_energivurdering,
                        energivurdering_dato, beregnet_fossilandel, materialvalg,
                        organisasjonsnummer, batch_datetime
                    ))
                    
                    insert_count += 1
                    
                except Exception as e:
                    logger.error(f"Error inserting data for attestnummer {attestnummer}: {e}")
            
            conn.commit()
            return insert_count
            
        except Exception as e:
            logger.error(f"Error saving energiattest data: {str(e)}")
            raise
        finally:
            if conn:
                conn.close()
    
    def process_certificates(self, top_rows: int = 10) -> Dict[str, Any]:
        """
        Main processing function - get parameters, call API, save results
        
        Args:
            top_rows: Number of certificates to process
            
        Returns:
            Dictionary with processing statistics
        """
        start_time = time.perf_counter()
        batch_datetime = datetime.now()
        
        try:
            # Step 0: Clean up old pending records from previous interrupted runs
            cleanup_count = self.cleanup_old_pending_records(hours_old=1)  # Clean records older than 1 hour
            if cleanup_count > 0:
                logger.info(f"Cleaned up {cleanup_count} stale pending records from previous runs")
            
            # Step 1: Get parameters from database
            logger.info(f"Starting certificate processing for {top_rows} rows")
            parameters = self.get_api_parameters(top_rows)
            
            if not parameters:
                logger.warning("No parameters retrieved from database")
                return {
                    'success': False,
                    'message': 'No parameters found',
                    'api_calls': 0,
                    'records_inserted': 0,
                    'processing_time': 0
                }
            
            # Step 2: Log all parameters
            self.log_count = self.log_api_parameters(parameters, batch_datetime)
            
            # Step 3: Process each parameter set
            for i, param in enumerate(parameters):
                certificate_id = param['certificate_id']
                records_returned = 0
                status_message = "Error"
                
                try:
                    logger.info(f"Processing {i+1}/{len(parameters)}: CertificateID {certificate_id}")
                    
                    # Call API
                    api_data = self.call_energiattest_api(param)
                    
                    if api_data == "TOO_MANY_RESULTS":
                        records_returned = 0
                        status_message = "Too many results (25+ eiendommer)"
                        logger.warning(f"CertificateID {certificate_id}: Too many results returned by API")
                    elif api_data:
                        records_returned = len(api_data)
                        # Save results
                        records_saved = self.save_energiattest_data(api_data, param, batch_datetime)
                        self.insert_count += records_saved
                        
                        if records_saved > 0:
                            status_message = "Success"
                            logger.info(f"Saved {records_saved} records for CertificateID {certificate_id}")
                        else:
                            status_message = "API returned data but no records saved"
                            logger.warning(f"API returned {records_returned} records but none were saved for CertificateID {certificate_id}")
                    else:
                        records_returned = 0
                        status_message = "No records found"
                        logger.warning(f"No data returned for CertificateID {certificate_id}")
                    
                    # Update the log with results
                    self.update_api_log(certificate_id, records_returned, status_message)
                    
                    # Progress reporting
                    if (i + 1) % 10 == 0:
                        logger.info(f"Processed {i + 1}/{len(parameters)} requests, {self.insert_count} records inserted")
                
                except Exception as e:
                    logger.error(f"Error processing CertificateID {certificate_id}: {e}")
                    status_message = f"Error: {str(e)[:200]}"  # Truncate error message
                    self.update_api_log(certificate_id, 0, status_message)
                    continue
            
            # Calculate statistics
            end_time = time.perf_counter()
            total_time = end_time - start_time
            avg_time_per_insert = total_time / self.insert_count if self.insert_count else 0
            avg_time_per_api_call = total_time / self.api_call_count if self.api_call_count else 0
            
            # Get detailed statistics from log
            log_stats = self.get_processing_statistics(batch_datetime)
            
            # Log summary
            logger.info(f"=== Processing Summary ===")
            logger.info(f"Parameters logged: {self.log_count}")
            logger.info(f"API calls made: {self.api_call_count}")
            logger.info(f"Records inserted: {self.insert_count}")
            logger.info(f"Total time: {total_time:.3f} sec")
            logger.info(f"Average per insert: {avg_time_per_insert:.4f} sec")
            logger.info(f"Average per API call: {avg_time_per_api_call:.4f} sec")
            
            # Log detailed status breakdown
            if log_stats:
                logger.info(f"=== Status Breakdown ===")
                for status, info in log_stats.items():
                    if status != '_totals':
                        logger.info(f"{status}: {info['count']} calls, {info['records']} records returned")
            
            return {
                'success': True,
                'message': 'Processing completed successfully',
                'parameters_logged': self.log_count,
                'api_calls': self.api_call_count,
                'records_inserted': self.insert_count,
                'processing_time': total_time,
                'avg_time_per_insert': avg_time_per_insert,
                'avg_time_per_api_call': avg_time_per_api_call,
                'status_breakdown': log_stats
            }
            
        except Exception as e:
            logger.error(f"Error during certificate processing: {str(e)}")
            return {
                'success': False,
                'message': f'Processing failed: {str(e)}',
                'api_calls': self.api_call_count,
                'records_inserted': self.insert_count,
                'processing_time': time.perf_counter() - start_time
            }
    
    def cleanup_old_pending_records(self, hours_old: int = 24) -> int:
        """
        Clean up old pending records that were never completed
        
        Args:
            hours_old: Age in hours for records to be considered stale (default: 24)
            
        Returns:
            Number of records cleaned up
        """
        conn = None
        try:
            conn = self._get_database_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                DELETE FROM [ev_enova].[EnovaApi_Energiattest_url_log] 
                WHERE status_message = 'Pending' 
                  AND LogDate < DATEADD(HOUR, ?, GETDATE())
            """, (-hours_old,))
            
            conn.commit()
            deleted_count = cursor.rowcount
            
            if deleted_count > 0:
                logger.info(f"Cleaned up {deleted_count} old pending records (older than {hours_old} hours)")
            else:
                logger.debug(f"No old pending records found (older than {hours_old} hours)")
            
            return deleted_count
            
        except Exception as e:
            logger.error(f"Error cleaning up old pending records: {str(e)}")
            return 0
        finally:
            if conn:
                conn.close()
    
    def get_processing_statistics(self, batch_datetime: datetime) -> Dict[str, Any]:
        """
        Get processing statistics from the log table
        
        Args:
            batch_datetime: Timestamp for this batch
            
        Returns:
            Dictionary with processing statistics
        """
        conn = None
        try:
            conn = self._get_database_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT 
                    status_message,
                    COUNT(*) as count,
                    SUM(ISNULL(records_returned, 0)) as total_records
                FROM [ev_enova].[EnovaApi_Energiattest_url_log] 
                WHERE LogDate = ?
                GROUP BY status_message
            """, (batch_datetime,))
            
            stats = {}
            total_calls = 0
            total_records = 0
            
            for row in cursor.fetchall():
                status = row.status_message
                count = row.count
                records = row.total_records or 0
                
                stats[status] = {
                    'count': count,
                    'records': records
                }
                total_calls += count
                total_records += records
            
            stats['_totals'] = {
                'total_calls': total_calls,
                'total_records_returned': total_records
            }
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting processing statistics: {str(e)}")
            return {}
        finally:
            if conn:
                conn.close()
