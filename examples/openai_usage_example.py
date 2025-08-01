#!/usr/bin/env python3
"""
Sample script demonstrating how to use the OpenAI Energy Service
Run this script to process energy certificate prompts with OpenAI API
"""

import sys
import os
import logging
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from config import get_config
from src.services.openai_service import OpenAIEnergyService

def setup_logging():
    """Setup logging configuration"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

def main():
    """Main function to demonstrate OpenAI service usage"""
    setup_logging()
    logger = logging.getLogger(__name__)
    
    try:
        # Get configuration
        config = get_config()
        
        # Validate configuration
        if not config.validate_config():
            logger.error("Configuration validation failed")
            return
        
        # Initialize OpenAI service
        logger.info("Initializing OpenAI Energy Service...")
        openai_service = OpenAIEnergyService(config)
        
        # Process prompts with PROMPT_V1_NOR column
        logger.info("Processing prompts with PROMPT_V1_NOR...")
        results_v1 = openai_service.process_prompts(
            prompt_column="PROMPT_V1_NOR",
            limit=10,  # Process only 10 records for testing
            delay_between_calls=2.0  # 2 second delay between API calls
        )
        
        # Display results
        print("\n" + "="*50)
        print("PROCESSING RESULTS - PROMPT_V1_NOR")
        print("="*50)
        for key, value in results_v1.items():
            print(f"{key}: {value}")
        
        # Get processing statistics
        logger.info("Getting processing statistics...")
        stats = openai_service.get_processing_statistics("PROMPT_V1_NOR")
        
        if stats:
            print("\n" + "="*50)
            print("PROCESSING STATISTICS")
            print("="*50)
            for prompt_version, stat_data in stats.items():
                print(f"\nPrompt Version: {prompt_version}")
                for stat_key, stat_value in stat_data.items():
                    print(f"  {stat_key}: {stat_value}")
        
        # Get sample responses for review
        logger.info("Getting sample responses...")
        samples = openai_service.get_sample_responses("PROMPT_V1_NOR", limit=3)
        
        if samples:
            print("\n" + "="*50)
            print("SAMPLE RESPONSES")
            print("="*50)
            for i, sample in enumerate(samples, 1):
                print(f"\nSample {i} (File ID: {sample['file_id']}):")
                print(f"  About Estate: {sample['about_estate'][:100]}...")
                print(f"  Positives: {sample['positives'][:100]}...")
                print(f"  Evaluation: {sample['evaluation'][:100]}...")
                print(f"  Created: {sample['created']}")
        
        # Example: Process with PROMPT_V2_NOR (if available)
        # Uncomment the following lines if you have PROMPT_V2_NOR column
        """
        logger.info("Processing prompts with PROMPT_V2_NOR...")
        results_v2 = openai_service.process_prompts(
            prompt_column="PROMPT_V2_NOR",
            limit=5,
            delay_between_calls=2.0
        )
        
        print("\n" + "="*50)
        print("PROCESSING RESULTS - PROMPT_V2_NOR")
        print("="*50)
        for key, value in results_v2.items():
            print(f"{key}: {value}")
        """
        
        logger.info("OpenAI processing completed successfully")
        
    except Exception as e:
        logger.error(f"Error in main processing: {str(e)}")
        raise

def process_single_prompt_example():
    """Example of processing a single prompt manually"""
    setup_logging()
    logger = logging.getLogger(__name__)
    
    try:
        config = get_config()
        openai_service = OpenAIEnergyService(config)
        
        # Example prompt (using the sample from your document)
        sample_prompt = """Opptre som ekspert i et selskap som lever av å selge informasjon om eiendom og bygninger. Du skal oppsummere relevante forhold knyttet til energimerke fra Enova med Energikarakter A og Oppvarmingskarakter Green for boligen. Merkenummer er 'Energiattest-2025-107518' datert April 15, 2025. Hold deg til fakta og ikke gå ut over 500 ord. Byggeår er 2025 og bygningskategori er Boligblokker. Attesten dekker 4 registrerte enheter. Energiattesten er innmeldt av ARCANOVAENTREPRENØRAS. Innmeldt adresse Otterstadveien 7, 1651 SELLEBAKK. Bruksareal 364.00 kvadratmeter. Beregnet Levert Energi Totalt kWh/m2: 86.16. Beregnet Levert Energi Totalt kWh: 31362.00. Beregnet Fossilandel er 27%. [Additional energy certificate data...]

Svaret skal være på dette formatet: 
Eiendom: Litt om eiendommen 
Positive ting: Hva er bra i forhold til Energiattesten 
Kort vurdering: Spesielle forhold som bør trekkes frem av en eller annen art."""

        logger.info("Testing single prompt processing...")
        
        # Call OpenAI API with the sample prompt
        response = openai_service.call_openai_api(sample_prompt)
        
        if response:
            print("\n" + "="*50)
            print("SINGLE PROMPT TEST RESULT")
            print("="*50)
            print(f"About Estate: {response['AboutEstate']}")
            print(f"Positives: {response['Positives']}")
            print(f"Evaluation: {response['Evaluation']}")
        else:
            print("Failed to get response from OpenAI API")
            
    except Exception as e:
        logger.error(f"Error in single prompt example: {str(e)}")
        raise

if __name__ == "__main__":
    # You can choose which function to run:
    
    # Option 1: Process prompts from database
    main()
    
    # Option 2: Test with a single prompt (uncomment to use)
    # process_single_prompt_example()
