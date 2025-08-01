#!/usr/bin/env python3
"""
Configuration for different database environments
"""

import os
from typing import Dict, Any

DATABASE_CONFIGS: Dict[str, Dict[str, Any]] = {
    'development': {
        'database_name': 'EnergyCertificate_Dev',
        'connection_string_env': 'DEV_DATABASE_CONNECTION_STRING',
        'description': 'Development database'
    },
    'staging': {
        'database_name': 'EnergyCertificate_Staging', 
        'connection_string_env': 'STAGING_DATABASE_CONNECTION_STRING',
        'description': 'Staging database'
    },
    'production': {
        'database_name': 'EnergyCertificate',
        'connection_string_env': 'PROD_DATABASE_CONNECTION_STRING',
        'description': 'Production database'
    }
}

def get_config(environment: str = 'development') -> Dict[str, Any]:
    """Get configuration for specified environment"""
    config = DATABASE_CONFIGS.get(environment, DATABASE_CONFIGS['development'])
    
    # Get connection string from environment variable
    conn_str_env = config['connection_string_env']
    connection_string = os.getenv(conn_str_env) or os.getenv('DATABASE_CONNECTION_STRING')
    
    return {
        **config,
        'connection_string': connection_string,
        'environment': environment
    }

def list_environments() -> list:
    """List available environments"""
    return list(DATABASE_CONFIGS.keys())

def validate_config(environment: str) -> bool:
    """Validate configuration for environment"""
    config = get_config(environment)
    
    if not config['connection_string']:
        print(f"❌ No connection string found for {environment}")
        print(f"   Set {config['connection_string_env']} or DATABASE_CONNECTION_STRING")
        return False
    
    return True

if __name__ == "__main__":
    print("Available environments:")
    for env in list_environments():
        config = get_config(env)
        status = "✅" if config['connection_string'] else "❌"
        print(f"  {status} {env}: {config['description']}")
