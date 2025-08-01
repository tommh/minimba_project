#!/usr/bin/env python3
"""
Test script for LangSmith integration with OpenAI service
"""

import sys
import os
import logging
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from config import get_config
from src.services.openai_service import OpenAIEnergyService

def setup_logging():
    """Setup logging configuration"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

def test_langsmith_configuration():
    """Test LangSmith configuration"""
    setup_logging()
    logger = logging.getLogger(__name__)
    
    try:
        # Get configuration
        config = get_config()
        
        # Validate configuration
        if not config.validate_config():
            logger.error("Configuration validation failed")
            return False
        
        # Check LangSmith configuration
        logger.info("=== LangSmith Configuration Test ===")
        logger.info(f"LangSmith API Key: {'Set' if config.LANGSMITH_API_KEY else 'Not set'}")
        logger.info(f"LangSmith Endpoint: {config.LANGSMITH_ENDPOINT}")
        logger.info(f"LangSmith Project: {config.LANGSMITH_PROJECT}")
        logger.info(f"LangSmith Tracing Enabled: {config.LANGSMITH_TRACING_ENABLED}")
        
        if config.LANGSMITH_TRACING_ENABLED and config.LANGSMITH_API_KEY:
            logger.info("✅ LangSmith tracing is properly configured")
            return True
        else:
            logger.warning("⚠️ LangSmith tracing is not fully configured")
            return False
            
    except Exception as e:
        logger.error(f"Error testing LangSmith configuration: {str(e)}")
        return False

def test_openai_service_with_langsmith():
    """Test OpenAI service with LangSmith tracing"""
    setup_logging()
    logger = logging.getLogger(__name__)
    
    try:
        # Get configuration
        config = get_config()
        
        # Initialize OpenAI service
        logger.info("Initializing OpenAI service with LangSmith...")
        openai_service = OpenAIEnergyService(config)
        
        # Test with a sample prompt
        sample_prompt = """Opptre som ekspert i et selskap som lever av å selge informasjon om eiendom og bygninger. 
Du skal oppsummere relevante forhold knyttet til energimerke fra Enova med Energikarakter A 
og Oppvarmingskarakter Green for boligen. Merkenummer er 'Energiattest-2025-107518' datert 
April 15, 2025. Hold deg til fakta og ikke gå ut over 500 ord.

Svaret skal være på dette formatet:
Eiendom: Litt om eiendommen
Positive ting: Hva er bra i forhold til Energiattesten  
Kort vurdering: Spesielle forhold som bør trekkes frem av en eller annen art."""

        logger.info("Testing OpenAI API call with LangSmith tracing...")
        
        # Call OpenAI API with tracing
        response = openai_service.call_openai_api(
            prompt_text=sample_prompt,
            file_id=99999,  # Test file ID
            prompt_version="TEST_PROMPT"
        )
        
        if response:
            logger.info("✅ OpenAI API call with LangSmith tracing successful")
            logger.info(f"Response sections: {list(response.keys())}")
            for key, value in response.items():
                logger.info(f"  {key}: {len(value)} characters")
            return True
        else:
            logger.error("❌ OpenAI API call failed")
            return False
            
    except Exception as e:
        logger.error(f"Error testing OpenAI service with LangSmith: {str(e)}")
        return False

def main():
    """Main test function"""
    print("=== LangSmith Integration Test ===")
    
    # Test 1: Configuration
    print("\n1. Testing LangSmith configuration...")
    config_ok = test_langsmith_configuration()
    
    # Test 2: OpenAI service with LangSmith
    print("\n2. Testing OpenAI service with LangSmith...")
    service_ok = test_openai_service_with_langsmith()
    
    # Summary
    print("\n=== Test Summary ===")
    print(f"Configuration: {'✅ PASS' if config_ok else '❌ FAIL'}")
    print(f"Service Integration: {'✅ PASS' if service_ok else '❌ FAIL'}")
    
    if config_ok and service_ok:
        print("\n🎉 All tests passed! LangSmith integration is working correctly.")
        print("\nYou can now view traces in your LangSmith dashboard:")
        print(f"  Project: {get_config().LANGSMITH_PROJECT}")
        print(f"  Dashboard: https://smith.langchain.com/")
    else:
        print("\n⚠️ Some tests failed. Please check your configuration.")
        
        if not config_ok:
            print("\nTo fix configuration issues:")
            print("1. Set LANGSMITH_API_KEY in your .env file")
            print("2. Ensure LANGSMITH_TRACING_ENABLED=true")
            print("3. Optionally set LANGSMITH_PROJECT for custom project name")
        
        if not service_ok:
            print("\nTo fix service issues:")
            print("1. Ensure OPENAI_API_KEY is set")
            print("2. Check your internet connection")
            print("3. Verify LangSmith API key is valid")

if __name__ == "__main__":
    main() 