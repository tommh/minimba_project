"""
Logging configuration for MinimBA Energy Certificate Processing System
Provides structured logging with file and console output
"""

import logging
import logging.handlers
from pathlib import Path
from datetime import datetime
import sys
import os

def setup_logger(name: str = None, config