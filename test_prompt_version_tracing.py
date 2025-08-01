#!/usr/bin/env python3
"""
Test script to verify prompt version tracing in LangSmith
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

def test_prompt_version_tracing():
    """Test that different prompt versions are properly traced"""
    setup_logging()
    logger = logging.getLogger(__name__)
    
    try:
        # Get configuration
        config = get_config()
        
        # Initialize OpenAI service
        logger.info("Initializing OpenAI service...")
        openai_service = OpenAIEnergyService(config)
        
        # Test different prompt versions
        prompt_versions = [
            "PROMPT_V1_NOR",
            "PROMPT_V2_NOR", 
            "PROMPT_V5_NOR_BANK",
            "TEST_PROMPT_VERSION"
        ]
        
        sample_prompt = """Opptre som ekspert i et selskap som lever av å selge informasjon om eiendom og bygninger. 
Du skal oppsummere relevante forhold knyttet til energimerke fra Enova med Energikarakter A 
og Oppvarmingskarakter Green for boligen. Merkenummer er 'Energiattest-2025-107518' datert 
April 15, 2025. Hold deg til fakta og ikke gå ut over 500 ord.

Svaret skal være på dette formatet:
Eiendom: Litt om eiendommen
Positive ting: Hva er bra i forhold til Energiattesten  
Kort vurdering: Spesielle forhold som bør trekkes frem av en eller annen art."""

        logger.info("Testing prompt version tracing...")
        
        for i, prompt_version in enumerate(prompt_versions):
            logger.info(f"Testing prompt version: {prompt_version}")
            
            # Call OpenAI API with specific prompt version
            response = openai_service.call_openai_api(
                prompt_text=sample_prompt,
                file_id=100000 + i,  # Unique file ID for each test
                prompt_version=prompt_version
            )
            
            if response:
                logger.info(f"✅ Successfully traced {prompt_version}")
            else:
                logger.error(f"❌ Failed to trace {prompt_version}")
        
        logger.info("=== Prompt Version Tracing Test Complete ===")
        logger.info("You can now filter in LangSmith dashboard by:")
        logger.info("1. Tags: prompt-version:PROMPT_V5_NOR_BANK")
        logger.info("2. Metadata: prompt_version field")
        logger.info("3. Run names: openai-energy-certificate-PROMPT_V5_NOR_BANK")
        
        return True
        
    except Exception as e:
        logger.error(f"Error testing prompt version tracing: {str(e)}")
        return False

def main():
    """Main test function"""
    print("=== Prompt Version Tracing Test ===")
    
    success = test_prompt_version_tracing()
    
    if success:
        print("\n🎉 Prompt version tracing test completed!")
        print("\nTo filter in LangSmith dashboard:")
        print("1. Go to https://smith.langchain.com/")
        print("2. Select your project")
        print("3. Use filters:")
        print("   - Tags: 'prompt-version:PROMPT_V5_NOR_BANK'")
        print("   - Metadata: prompt_version = 'PROMPT_V5_NOR_BANK'")
        print("   - Run names containing: 'PROMPT_V5_NOR_BANK'")
    else:
        print("\n❌ Test failed. Check your configuration.")

if __name__ == "__main__":
    main() 