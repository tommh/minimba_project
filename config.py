"""
Configuration management for MinimBA Energy Certificate Processing System
Loads settings from environment variables and provides default values
"""

import os
from pathlib import Path
from typing import Optional
import logging

logger = logging.getLogger(__name__)

class Config:
    """Application configuration loaded from environment variables"""
    
    def __init__(self, env_file: Optional[str] = None):
        """
        Initialize configuration
        
        Args:
            env_file: Optional path to .env file to load
        """
        # Load .env file if specified or if it exists
        if env_file:
            self._load_env_file(env_file)
        elif Path('.env').exists():
            self._load_env_file('.env')
    
    # Database Configuration
    @property
    def DATABASE_SERVER(self) -> str:
        return os.getenv('DATABASE_SERVER', 'localhost')
    
    @property
    def DATABASE_NAME(self) -> str:
        return os.getenv('DATABASE_NAME', 'MinimBAEnergyDB')
    
    @property
    def DATABASE_USERNAME(self) -> Optional[str]:
        return os.getenv('DATABASE_USERNAME')
    
    @property
    def DATABASE_PASSWORD(self) -> Optional[str]:
        return os.getenv('DATABASE_PASSWORD')
    
    @property
    def DATABASE_DRIVER(self) -> str:
        return os.getenv('DATABASE_DRIVER', 'ODBC Driver 17 for SQL Server')
    
    @property
    def DATABASE_PORT(self) -> int:
        return int(os.getenv('DATABASE_PORT', '1433'))
    
    @property
    def DATABASE_TRUSTED_CONNECTION(self) -> bool:
        return os.getenv('DATABASE_TRUSTED_CONNECTION', 'yes').lower() in ('yes', 'true', '1')
    
    @property
    def CONNECTION_STRING(self) -> str:
        """Generate SQL Server connection string"""
        if self.DATABASE_TRUSTED_CONNECTION:
            return (
                f"mssql+pyodbc://@{self.DATABASE_SERVER}:{self.DATABASE_PORT}/"
                f"{self.DATABASE_NAME}?driver={self.DATABASE_DRIVER.replace(' ', '+')}"
                f"&trusted_connection=yes"
            )
        else:
            return (
                f"mssql+pyodbc://{self.DATABASE_USERNAME}:{self.DATABASE_PASSWORD}@"
                f"{self.DATABASE_SERVER}:{self.DATABASE_PORT}/{self.DATABASE_NAME}"
                f"?driver={self.DATABASE_DRIVER.replace(' ', '+')}"
            )
    
    # File Storage Configuration
    @property
    def BASE_DATA_PATH(self) -> str:
        return os.getenv('BASE_DATA_PATH', './data')
    
    @property
    def DOWNLOAD_CSV_PATH(self) -> str:
        base_path = Path(self.BASE_DATA_PATH)
        return str(base_path / 'downloads' / 'csv')
    
    @property
    def DOWNLOAD_PDF_PATH(self) -> str:
        base_path = Path(self.BASE_DATA_PATH)
        return str(base_path / 'downloads' / 'pdfs')
    
    @property
    def PROCESSED_TEXT_PATH(self) -> str:
        base_path = Path(self.BASE_DATA_PATH)
        return str(base_path / 'processed' / 'cleaned_text')
    
    @property
    def LOGS_PATH(self) -> str:
        base_path = Path(self.BASE_DATA_PATH)
        return str(base_path / 'logs')
    
    # API Configuration
    @property
    def ENOVA_API_BASE_URL(self) -> str:
        return os.getenv('ENOVA_API_BASE_URL', 'https://api.data.enova.no/ems/offentlige-data/v1')
    
    @property
    def ENOVA_API_KEY(self) -> Optional[str]:
        return os.getenv('ENOVA_API_KEY')
    
    @property
    def ENOVA_API_TIMEOUT(self) -> int:
        return int(os.getenv('ENOVA_API_TIMEOUT', '30'))
    
    @property
    def ENOVA_API_RETRY_COUNT(self) -> int:
        return int(os.getenv('ENOVA_API_RETRY_COUNT', '3'))
    
    @property
    def ENOVA_API_DELAY(self) -> float:
        return float(os.getenv('ENOVA_API_DELAY', '0.5'))  # Default 0.5 seconds between requests
    
    # OpenAI Configuration
    @property
    def OPENAI_API_KEY(self) -> Optional[str]:
        return os.getenv('OPENAI_API_KEY')
    
    @property
    def OPENAI_MODEL(self) -> str:
        return os.getenv('OPENAI_MODEL', 'gpt-4o-mini')
    
    @property
    def OPENAI_MAX_TOKENS(self) -> int:
        return int(os.getenv('OPENAI_MAX_TOKENS', '2000'))
    
    @property
    def OPENAI_TEMPERATURE(self) -> float:
        return float(os.getenv('OPENAI_TEMPERATURE', '0.3'))
    
    # LangSmith Configuration
    @property
    def LANGSMITH_API_KEY(self) -> Optional[str]:
        return os.getenv('LANGSMITH_API_KEY')
    
    @property
    def LANGSMITH_ENDPOINT(self) -> str:
        return os.getenv('LANGSMITH_ENDPOINT', 'https://api.smith.langchain.com')
    
    @property
    def LANGSMITH_PROJECT(self) -> str:
        return os.getenv('LANGSMITH_PROJECT', 'minimba-energy-certificates')
    
    @property
    def LANGSMITH_TRACING_ENABLED(self) -> bool:
        return os.getenv('LANGSMITH_TRACING_ENABLED', 'true').lower() in ('yes', 'true', '1')
    
    # Processing Configuration
    @property
    def BATCH_SIZE(self) -> int:
        return int(os.getenv('BATCH_SIZE', '100'))
    
    @property
    def MAX_CONCURRENT_DOWNLOADS(self) -> int:
        return int(os.getenv('MAX_CONCURRENT_DOWNLOADS', '5'))
    
    @property
    def PDF_TEXT_EXTRACTION_TIMEOUT(self) -> int:
        return int(os.getenv('PDF_TEXT_EXTRACTION_TIMEOUT', '60'))
    
    # Logging Configuration
    @property
    def LOG_LEVEL(self) -> str:
        return os.getenv('LOG_LEVEL', 'INFO').upper()
    
    @property
    def LOG_FORMAT(self) -> str:
        return os.getenv('LOG_FORMAT', '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    @property
    def LOG_TO_FILE(self) -> bool:
        return os.getenv('LOG_TO_FILE', 'true').lower() in ('yes', 'true', '1')
    
    @property
    def LOG_TO_CONSOLE(self) -> bool:
        return os.getenv('LOG_TO_CONSOLE', 'true').lower() in ('yes', 'true', '1')
    
    def _load_env_file(self, env_file: str):
        """Load environment variables from a .env file"""
        try:
            with open(env_file, 'r', encoding='utf-8') as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    
                    # Skip empty lines and comments
                    if not line or line.startswith('#'):
                        continue
                    
                    # Parse KEY=VALUE format
                    if '=' in line:
                        key, value = line.split('=', 1)
                        key = key.strip()
                        value = value.strip()
                        
                        # Remove quotes if present
                        if value.startswith('"') and value.endswith('"'):
                            value = value[1:-1]
                        elif value.startswith("'") and value.endswith("'"):
                            value = value[1:-1]
                        
                        # Only set if not already in environment
                        if key not in os.environ:
                            os.environ[key] = value
                    else:
                        logger.warning(f"Invalid line in {env_file}:{line_num}: {line}")
                        
            logger.info(f"Loaded environment variables from {env_file}")
            
        except FileNotFoundError:
            logger.warning(f"Environment file not found: {env_file}")
        except Exception as e:
            logger.error(f"Error loading environment file {env_file}: {str(e)}")
    
    def validate_config(self) -> bool:
        """
        Validate required configuration values
        
        Returns:
            True if configuration is valid, False otherwise
        """
        errors = []
        
        # Check database configuration
        if not self.DATABASE_SERVER:
            errors.append("DATABASE_SERVER is required")
        
        if not self.DATABASE_NAME:
            errors.append("DATABASE_NAME is required")
        
        if not self.DATABASE_TRUSTED_CONNECTION:
            if not self.DATABASE_USERNAME:
                errors.append("DATABASE_USERNAME is required when not using trusted connection")
            if not self.DATABASE_PASSWORD:
                errors.append("DATABASE_PASSWORD is required when not using trusted connection")
        
        # Check OpenAI configuration if being used
        if not self.OPENAI_API_KEY:
            logger.warning("OPENAI_API_KEY not set - OpenAI features will be disabled")
        
        # Check LangSmith configuration if tracing is enabled
        if self.LANGSMITH_TRACING_ENABLED:
            if not self.LANGSMITH_API_KEY:
                logger.warning("LANGSMITH_API_KEY not set - LangSmith tracing will be disabled")
            else:
                logger.info(f"LangSmith tracing enabled for project: {self.LANGSMITH_PROJECT}")
        else:
            logger.info("LangSmith tracing disabled")
        
        # Create required directories
        try:
            for path in [self.DOWNLOAD_CSV_PATH, self.DOWNLOAD_PDF_PATH, 
                        self.PROCESSED_TEXT_PATH, self.LOGS_PATH]:
                Path(path).mkdir(parents=True, exist_ok=True)
        except Exception as e:
            errors.append(f"Could not create required directories: {str(e)}")
        
        if errors:
            for error in errors:
                logger.error(f"Configuration error: {error}")
            return False
        
        logger.info("Configuration validation passed")
        return True
    
    def get_config_summary(self) -> dict:
        """Get a summary of current configuration (excluding sensitive values)"""
        return {
            'database_server': self.DATABASE_SERVER,
            'database_name': self.DATABASE_NAME,
            'database_driver': self.DATABASE_DRIVER,
            'trusted_connection': self.DATABASE_TRUSTED_CONNECTION,
            'base_data_path': self.BASE_DATA_PATH,
            'enova_api_base_url': self.ENOVA_API_BASE_URL,
            'batch_size': self.BATCH_SIZE,
            'log_level': self.LOG_LEVEL,
            'openai_model': self.OPENAI_MODEL,
            'openai_configured': bool(self.OPENAI_API_KEY),
            'langsmith_project': self.LANGSMITH_PROJECT,
            'langsmith_tracing_enabled': self.LANGSMITH_TRACING_ENABLED and bool(self.LANGSMITH_API_KEY)
        }

# Global config instance
_config = None

def get_config() -> Config:
    """Get global configuration instance"""
    global _config
    if _config is None:
        _config = Config()
    return _config