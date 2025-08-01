# 📚 Examples & Demonstrations

This directory contains example scripts and demonstrations showing how to use various components of the Energy Certificate project.

## 🎯 Available Examples

### `openai_usage_example.py`
**Purpose**: Demonstrates how to use the OpenAI Energy Service for processing energy certificate data

**What it shows**:
- How to initialize the OpenAI service
- Processing prompts from the database
- Getting processing statistics
- Retrieving sample responses
- Single prompt testing

**Usage**:
```bash
# Run the full example
python examples/openai_usage_example.py
```

**Features demonstrated**:
- ✅ Batch processing with configurable limits
- ✅ API call delays to respect rate limits
- ✅ Error handling and logging
- ✅ Statistics retrieval
- ✅ Sample response inspection
- ✅ Single prompt testing

## 🚀 Running Examples

All examples can be run from the project root directory:

```bash
# OpenAI service example
python examples/openai_usage_example.py

# Future examples...
# python examples/csv_processing_example.py
# python examples/pdf_pipeline_example.py
```

## 📋 Example Categories

### API Integration Examples
- `openai_usage_example.py` - OpenAI API integration

### Future Example Ideas
- `csv_processing_example.py` - CSV import and processing workflows
- `pdf_pipeline_example.py` - Complete PDF processing pipeline
- `database_operations_example.py` - Database operations and queries
- `api_client_example.py` - Enova API client usage
- `text_cleaning_example.py` - Text processing and cleaning

## 🛠️ Creating New Examples

When adding new example scripts:

1. **Create descriptive filename**: Use `*_example.py` pattern
2. **Add comprehensive docstring**: Explain purpose and usage
3. **Include error handling**: Show proper exception handling
4. **Add logging**: Demonstrate logging best practices
5. **Document in this README**: Update this file with new examples

### Example Template
```python
#!/usr/bin/env python3
\"\"\"
Example: [Description of what this example demonstrates]
Shows how to [specific functionality]
\"\"\"

import sys
import logging
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from config import get_config
# Import relevant services

def setup_logging():
    \"\"\"Setup logging configuration\"\"\"
    logging.basicConfig(level=logging.INFO)

def main():
    \"\"\"Main example function\"\"\"
    setup_logging()
    logger = logging.getLogger(__name__)
    
    try:
        # Example code here
        pass
    except Exception as e:
        logger.error(f"Example failed: {e}")
        raise

if __name__ == "__main__":
    main()
```

## 💡 Best Practices for Examples

- **Keep examples focused**: Each example should demonstrate one main concept
- **Use realistic data**: Show practical, real-world usage scenarios  
- **Include error cases**: Demonstrate how to handle common errors
- **Add comments**: Explain what each section does
- **Make them runnable**: Examples should work out of the box
- **Show configuration**: Demonstrate proper setup and configuration

## 🔗 Integration with Main Project

Examples use the same services and configuration as the main application:

```python
from config import get_config
from src.services.openai_service import OpenAIEnergyService
from src.services.csv_processor import CSVProcessor
# ... other services
```

This ensures examples stay up-to-date with the main codebase and serve as living documentation.

---

**Note**: Examples are for demonstration and learning purposes. For production use, refer to the main application in `src/` and deployment scripts in `scripts/`.
