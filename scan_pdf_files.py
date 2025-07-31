#!/usr/bin/env python3
"""
DEPRECATED: This file has been moved to src/services/pdf_scanner.py

This is a backward compatibility wrapper. Please update your imports to:
from src.services.pdf_scanner import PDFFileScanner

Or use the new location directly:
python src/services/pdf_scanner.py
"""

import sys
import warnings
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

# Show deprecation warning
warnings.warn(
    "scan_pdf_files.py has been moved to src/services/pdf_scanner.py. "
    "Please update your imports and scripts to use the new location.",
    DeprecationWarning,
    stacklevel=2
)

# Import everything from the new location for backward compatibility
try:
    from src.services.pdf_scanner import PDFFileScanner, main
except ImportError as e:
    print(f"❌ Error importing from new location: {e}")
    print("   Please check that src/services/pdf_scanner.py exists")
    sys.exit(1)

if __name__ == "__main__":
    print("⚠️  DEPRECATED: scan_pdf_files.py has been moved to src/services/pdf_scanner.py")
    print("   Please use: python src/services/pdf_scanner.py")
    print("   Continuing with deprecated wrapper...\n")
    sys.exit(main())