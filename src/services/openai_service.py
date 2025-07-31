"""
OpenAI Service for Energy Certificate Text Analysis
Processes energy certificate prompts using OpenAI API and stores structured responses
"""

import pyodbc
import openai
import time
import json
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple
import logging
import re

logger = logging.getLogger(__name__)

class OpenAIEnergyService:
    """Service for processing energy certificate data with OpenAI API"""
    
    def __init__(self, config):
        self.config = config
        self.client = None
        self.processed_count = 0
        self.error_count = 0
        
        # Initialize OpenAI client
        if config.OPENAI_API_KEY:
            openai.api_key = config.OPENAI_API_KEY
            self.client = openai.OpenAI(api_key=config.OPENAI_API_KEY)
            logger.info("OpenAI client initialized")
        else:
            logger.error("OpenAI API key not configured")
            raise ValueError("OPENAI_API_KEY is required")
    
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
            
            logger.debug(f"Connecting to database: {self.config.DATABASE_SERVER}/{self.config.DATABASE_NAME}")
            return pyodbc.connect(conn_str)
            
        except Exception as e:
            logger.error(f"Database connection failed: {str(e)}")
            raise
    
    def get_prompts_data(self, prompt_column: str = "PROMPT_V1_NOR", limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Get prompts data from database
        
        Args:
            prompt_column: Column name for the prompt (e.g., PROMPT_V1_NOR, PROMPT_V2_NOR)
            limit: Optional limit for number of records to process
            
        Returns:
            List of dictionaries containing FILE_ID and prompt data
        """
        conn = None
        try:
            conn = self._get_database_connection()
            cursor = conn.cursor()
            
            # Build the query
            query = f"SELECT FILE_ID, {prompt_column} FROM [ev_enova].[SampleTestDataForOpenAI]"
            
            # Add limit if specified
            if limit:
                # For SQL Server, use TOP
                query = f"SELECT TOP {limit} FILE_ID, {prompt_column} FROM [ev_enova].[SampleTestDataForOpenAI]"
            
            # Add filter to exclude already processed records
            query += f"""
                WHERE FILE_ID NOT IN (
                    SELECT file_id 
                    FROM [ev_enova].[OpenAIAnswers] 
                    WHERE PromptVersion = '{prompt_column}'
                )
                AND {prompt_column} IS NOT NULL 
                AND LEN(TRIM({prompt_column})) > 0
                ORDER BY FILE_ID
            """
            
            logger.info(f"Executing query to get prompts: {query}")
            cursor.execute(query)
            rows = cursor.fetchall()
            
            logger.info(f"Retrieved {len(rows)} prompt records from database")
            
            # Convert rows to list of dictionaries
            prompts_data = []
            for row in rows:
                prompt_dict = {
                    'file_id': row.FILE_ID,
                    'prompt_text': row[1],  # The prompt column value
                    'prompt_version': prompt_column
                }
                prompts_data.append(prompt_dict)
            
            return prompts_data
            
        except Exception as e:
            logger.error(f"Error retrieving prompts data: {str(e)}")
            raise
        finally:
            if conn:
                conn.close()
    
    def call_openai_api(self, prompt_text: str) -> Optional[Dict[str, str]]:
        """
        Call OpenAI API with the prompt and parse the response
        
        Args:
            prompt_text: The prompt text to send to OpenAI
            
        Returns:
            Dictionary with parsed response containing AboutEstate, Positives, Evaluation
            or None if API call failed
        """
        try:
            # Call OpenAI API
            response = self.client.chat.completions.create(
                model=self.config.OPENAI_MODEL,
                messages=[
                    {
                        "role": "system", 
                        "content": "Du er ekspert i energiattester og eiendomsanalyse. Analyser den gitte energiattesten og gi en strukturert respons i det spesifiserte formatet."
                    },
                    {
                        "role": "user", 
                        "content": prompt_text
                    }
                ],
                max_tokens=self.config.OPENAI_MAX_TOKENS,
                temperature=self.config.OPENAI_TEMPERATURE
            )
            
            # Extract the response text
            response_text = response.choices[0].message.content.strip()
            logger.debug(f"OpenAI API response received: {len(response_text)} characters")
            
            # Parse the structured response
            parsed_response = self._parse_openai_response(response_text)
            
            return parsed_response
            
        except Exception as e:
            logger.error(f"Error calling OpenAI API: {str(e)}")
            return None
    
    def _parse_openai_response(self, response_text: str) -> Dict[str, str]:
        """
        Parse the structured response from OpenAI
        
        Args:
            response_text: Raw response text from OpenAI
            
        Returns:
            Dictionary with AboutEstate, Positives, and Evaluation sections
        """
        # Initialize result dictionary
        result = {
            'AboutEstate': '',
            'Positives': '', 
            'Evaluation': ''
        }
        
        try:
            # Define patterns to match the expected format
            patterns = {
                'AboutEstate': r'Eiendom:\s*(.*?)(?=Positive ting:|$)',
                'Positives': r'Positive ting:\s*(.*?)(?=Kort vurdering:|$)',
                'Evaluation': r'Kort vurdering:\s*(.*?)$'
            }
            
            # Clean the response text
            clean_text = response_text.strip()
            
            # Try to extract each section using regex
            for key, pattern in patterns.items():
                match = re.search(pattern, clean_text, re.DOTALL | re.IGNORECASE)
                if match:
                    # Extract and clean the matched text
                    extracted_text = match.group(1).strip()
                    # Remove any trailing punctuation or newlines
                    extracted_text = re.sub(r'\n+', ' ', extracted_text)
                    # Clean up Markdown formatting
                    extracted_text = self._clean_markdown_formatting(extracted_text)
                    extracted_text = extracted_text.strip()
                    result[key] = extracted_text
                else:
                    logger.warning(f"Could not extract section '{key}' from OpenAI response")
            
            # If regex parsing failed, try alternative parsing
            if not any(result.values()):
                logger.info("Regex parsing failed, attempting alternative parsing")
                result = self._alternative_response_parsing(clean_text)
            
            # Ensure all fields have some content, even if parsing failed
            for key in result:
                if not result[key]:
                    result[key] = "Ikke tilgjengelig i responsen"
            
            # Truncate fields to database limits (assuming NVARCHAR(2000))
            for key in result:
                if len(result[key]) > 1990:  # Leave some margin
                    result[key] = result[key][:1987] + "..."
                    logger.warning(f"Truncated {key} field due to length limit")
            
            logger.debug(f"Parsed response: AboutEstate={len(result['AboutEstate'])} chars, "
                        f"Positives={len(result['Positives'])} chars, "
                        f"Evaluation={len(result['Evaluation'])} chars")
            
            return result
            
        except Exception as e:
            logger.error(f"Error parsing OpenAI response: {str(e)}")
            # Return the raw response in AboutEstate if parsing fails completely
            return {
                'AboutEstate': response_text[:1987] + "..." if len(response_text) > 1990 else response_text,
                'Positives': 'Feil ved parsing av respons',
                'Evaluation': 'Feil ved parsing av respons'
            }
    
    def _alternative_response_parsing(self, response_text: str) -> Dict[str, str]:
        """
        Alternative parsing method if regex fails
        
        Args:
            response_text: Raw response text from OpenAI
            
        Returns:
            Dictionary with parsed sections
        """
        result = {
            'AboutEstate': '',
            'Positives': '',
            'Evaluation': ''
        }
        
        try:
            # Split by common section indicators
            lines = response_text.split('\n')
            current_section = None
            current_content = []
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                
                # Check for section headers
                line_lower = line.lower()
                if 'eiendom:' in line_lower or 'om eiendommen' in line_lower:
                    if current_section and current_content:
                        result[current_section] = ' '.join(current_content)
                    current_section = 'AboutEstate'
                    current_content = []
                    # Add content after the colon if present
                    if ':' in line:
                        content_after_colon = line.split(':', 1)[1].strip()
                        if content_after_colon:
                            current_content.append(content_after_colon)
                elif 'positive' in line_lower and ('ting' in line_lower or 'forhold' in line_lower):
                    if current_section and current_content:
                        result[current_section] = ' '.join(current_content)
                    current_section = 'Positives'
                    current_content = []
                    if ':' in line:
                        content_after_colon = line.split(':', 1)[1].strip()
                        if content_after_colon:
                            current_content.append(content_after_colon)
                elif 'vurdering' in line_lower or 'konklusjon' in line_lower:
                    if current_section and current_content:
                        result[current_section] = ' '.join(current_content)
                    current_section = 'Evaluation'
                    current_content = []
                    if ':' in line:
                        content_after_colon = line.split(':', 1)[1].strip()
                        if content_after_colon:
                            current_content.append(content_after_colon)
                else:
                    # Add to current section content
                    if current_section:
                        current_content.append(line)
                    elif not result['AboutEstate']:  # If no section identified yet, assume it's about estate
                        current_section = 'AboutEstate'
                        current_content.append(line)
            
            # Don't forget the last section
            if current_section and current_content:
                content_text = ' '.join(current_content)
                # Clean markdown formatting
                content_text = self._clean_markdown_formatting(content_text)
                result[current_section] = content_text
            
            # Clean all results
            for key in result:
                if result[key]:
                    result[key] = self._clean_markdown_formatting(result[key])
            
            logger.debug("Alternative parsing completed")
            return result
            
        except Exception as e:
            logger.error(f"Error in alternative parsing: {str(e)}")
            return result
    
    def _clean_markdown_formatting(self, text: str) -> str:
        """
        Clean Markdown formatting from text
        
        Args:
            text: Text that may contain Markdown formatting
            
        Returns:
            Clean text with Markdown formatting removed
        """
        if not text:
            return text
        
        try:
            # Remove bold formatting (**text** and __text__)
            text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)
            text = re.sub(r'__(.*?)__', r'\1', text)
            
            # Remove italic formatting (*text* and _text_)
            text = re.sub(r'\*(.*?)\*', r'\1', text)
            text = re.sub(r'_(.*?)_', r'\1', text)
            
            # Remove inline code formatting (`code`)
            text = re.sub(r'`(.*?)`', r'\1', text)
            
            # Remove headers (# ## ### etc.)
            text = re.sub(r'^#{1,6}\s*', '', text, flags=re.MULTILINE)
            
            # Remove bullet points and dashes at start of lines
            text = re.sub(r'^[-*+]\s*', '', text, flags=re.MULTILINE)
            
            # Remove numbered lists
            text = re.sub(r'^\d+\.\s*', '', text, flags=re.MULTILINE)
            
            # Clean up extra whitespace
            text = re.sub(r'\s+', ' ', text)
            text = text.strip()
            
            return text
            
        except Exception as e:
            logger.warning(f"Error cleaning markdown formatting: {str(e)}")
            return text
    
    def save_openai_response(self, file_id: int, prompt_version: str, 
                           parsed_response: Dict[str, str]) -> bool:
        """
        Save OpenAI response to database
        
        Args:
            file_id: The file ID from the source data
            prompt_version: The prompt version used (e.g., PROMPT_V1_NOR)
            parsed_response: Dictionary with AboutEstate, Positives, Evaluation
            
        Returns:
            True if successful, False otherwise
        """
        conn = None
        try:
            conn = self._get_database_connection()
            cursor = conn.cursor()
            
            # Insert the response into the database
            insert_query = """
                INSERT INTO [ev_enova].[OpenAIAnswers] 
                (file_id, PromptVersion, AboutEstate, Positives, Evaluation, Created)
                VALUES (?, ?, ?, ?, ?, ?)
            """
            
            cursor.execute(insert_query, (
                file_id,
                prompt_version,
                parsed_response.get('AboutEstate', ''),
                parsed_response.get('Positives', ''),
                parsed_response.get('Evaluation', ''),
                datetime.now()
            ))
            
            conn.commit()
            logger.debug(f"Saved OpenAI response for file_id {file_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving OpenAI response for file_id {file_id}: {str(e)}")
            return False
        finally:
            if conn:
                conn.close()
    
    def process_prompts(self, prompt_column: str = "PROMPT_V1_NOR", 
                       limit: Optional[int] = None, 
                       delay_between_calls: float = 1.0) -> Dict[str, Any]:
        """
        Main processing function - get prompts, call OpenAI, save responses
        
        Args:
            prompt_column: Column name for the prompt (e.g., PROMPT_V1_NOR, PROMPT_V2_NOR)  
            limit: Optional limit for number of records to process
            delay_between_calls: Delay in seconds between OpenAI API calls (default: 1.0)
            
        Returns:
            Dictionary with processing statistics
        """
        start_time = time.perf_counter()
        
        try:
            logger.info(f"Starting OpenAI prompt processing with column: {prompt_column}")
            
            # Step 1: Get prompts from database
            prompts_data = self.get_prompts_data(prompt_column, limit)
            
            if not prompts_data:
                logger.warning("No prompts found for processing")
                return {
                    'success': True,
                    'message': 'No prompts found for processing',
                    'prompts_processed': 0,
                    'errors': 0,
                    'processing_time': 0
                }
            
            logger.info(f"Found {len(prompts_data)} prompts to process")
            
            # Step 2: Process each prompt
            for i, prompt_data in enumerate(prompts_data):
                file_id = prompt_data['file_id']
                prompt_text = prompt_data['prompt_text']
                prompt_version = prompt_data['prompt_version']
                
                try:
                    logger.info(f"Processing {i+1}/{len(prompts_data)}: file_id {file_id}")
                    
                    # Add delay between API calls (except for first request)
                    if i > 0:
                        time.sleep(delay_between_calls)
                    
                    # Call OpenAI API
                    parsed_response = self.call_openai_api(prompt_text)
                    
                    if parsed_response:
                        # Save response to database
                        if self.save_openai_response(file_id, prompt_version, parsed_response):
                            self.processed_count += 1
                            logger.info(f"Successfully processed file_id {file_id}")
                        else:
                            self.error_count += 1
                            logger.error(f"Failed to save response for file_id {file_id}")
                    else:
                        self.error_count += 1
                        logger.error(f"Failed to get valid response from OpenAI for file_id {file_id}")
                    
                    # Progress reporting
                    if (i + 1) % 10 == 0:
                        logger.info(f"Progress: {i + 1}/{len(prompts_data)} processed, "
                                  f"{self.processed_count} successful, {self.error_count} errors")
                
                except Exception as e:
                    self.error_count += 1
                    logger.error(f"Error processing file_id {file_id}: {str(e)}")
                    continue
            
            # Calculate statistics
            end_time = time.perf_counter()
            total_time = end_time - start_time
            avg_time_per_prompt = total_time / len(prompts_data) if prompts_data else 0
            
            # Log summary
            logger.info(f"=== OpenAI Processing Summary ===")
            logger.info(f"Total prompts: {len(prompts_data)}")
            logger.info(f"Successfully processed: {self.processed_count}")
            logger.info(f"Errors: {self.error_count}")
            logger.info(f"Total time: {total_time:.3f} seconds")
            logger.info(f"Average per prompt: {avg_time_per_prompt:.3f} seconds")
            logger.info(f"Success rate: {(self.processed_count / len(prompts_data) * 100):.1f}%")
            
            return {
                'success': True,
                'message': 'Processing completed',
                'total_prompts': len(prompts_data),
                'prompts_processed': self.processed_count,
                'errors': self.error_count,
                'processing_time': total_time,
                'avg_time_per_prompt': avg_time_per_prompt,
                'success_rate': (self.processed_count / len(prompts_data) * 100) if prompts_data else 0
            }
            
        except Exception as e:
            logger.error(f"Error during OpenAI prompt processing: {str(e)}")
            return {
                'success': False,
                'message': f'Processing failed: {str(e)}',
                'prompts_processed': self.processed_count,
                'errors': self.error_count,
                'processing_time': time.perf_counter() - start_time
            }
    
    def get_processing_statistics(self, prompt_version: Optional[str] = None) -> Dict[str, Any]:
        """
        Get processing statistics from the database
        
        Args:
            prompt_version: Optional filter by prompt version
            
        Returns:
            Dictionary with processing statistics
        """
        conn = None
        try:
            conn = self._get_database_connection()
            cursor = conn.cursor()
            
            # Build query with optional filter
            where_clause = ""
            params = []
            if prompt_version:
                where_clause = "WHERE PromptVersion = ?"
                params.append(prompt_version)
            
            query = f"""
                SELECT 
                    PromptVersion,
                    COUNT(*) as total_responses,
                    MIN(Created) as first_processed,
                    MAX(Created) as last_processed,
                    COUNT(CASE WHEN LEN(TRIM(ISNULL(AboutEstate, ''))) > 0 THEN 1 END) as has_about_estate,
                    COUNT(CASE WHEN LEN(TRIM(ISNULL(Positives, ''))) > 0 THEN 1 END) as has_positives,
                    COUNT(CASE WHEN LEN(TRIM(ISNULL(Evaluation, ''))) > 0 THEN 1 END) as has_evaluation
                FROM [ev_enova].[OpenAIAnswers] 
                {where_clause}
                GROUP BY PromptVersion
                ORDER BY PromptVersion
            """
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            statistics = {}
            for row in rows:
                stats = {
                    'total_responses': row.total_responses,
                    'first_processed': row.first_processed,
                    'last_processed': row.last_processed,
                    'has_about_estate': row.has_about_estate,
                    'has_positives': row.has_positives,
                    'has_evaluation': row.has_evaluation,
                    'completion_rate': {
                        'about_estate': (row.has_about_estate / row.total_responses * 100) if row.total_responses > 0 else 0,
                        'positives': (row.has_positives / row.total_responses * 100) if row.total_responses > 0 else 0,
                        'evaluation': (row.has_evaluation / row.total_responses * 100) if row.total_responses > 0 else 0
                    }
                }
                statistics[row.PromptVersion] = stats
            
            return statistics
            
        except Exception as e:
            logger.error(f"Error getting processing statistics: {str(e)}")
            return {}
        finally:
            if conn:
                conn.close()
    
    def get_sample_responses(self, prompt_version: str, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Get sample responses for review
        
        Args:
            prompt_version: The prompt version to get samples for
            limit: Number of samples to return
            
        Returns:
            List of sample responses
        """
        conn = None
        try:
            conn = self._get_database_connection()
            cursor = conn.cursor()
            
            query = f"""
                SELECT TOP {limit}
                    file_id,
                    AboutEstate,
                    Positives,
                    Evaluation,
                    Created
                FROM [ev_enova].[OpenAIAnswers] 
                WHERE PromptVersion = ?
                ORDER BY Created DESC
            """
            
            cursor.execute(query, (prompt_version,))
            rows = cursor.fetchall()
            
            samples = []
            for row in rows:
                sample = {
                    'file_id': row.file_id,
                    'about_estate': row.AboutEstate,
                    'positives': row.Positives,
                    'evaluation': row.Evaluation,
                    'created': row.Created
                }
                samples.append(sample)
            
            return samples
            
        except Exception as e:
            logger.error(f"Error getting sample responses: {str(e)}")
            return []
        finally:
            if conn:
                conn.close()
