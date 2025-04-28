#!/usr/bin/env python3
"""
Wrapper to call TelegramForwarder.py with correct capitalization
"""

import os
import sys
import traceback
import logging

# Set up detailed logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Simply run the actual file with proper capitalization
if __name__ == "__main__":
    try:
        logger.info("Starting TelegramForwarder.py wrapper")
        logger.info(f"Current directory: {os.getcwd()}")
        logger.info(f"Files in directory: {os.listdir('.')}")
        
        # Execute the main script
        logger.info("About to execute TelegramForwarder.py")
        
        # Using exec instead of runpy for better error visibility
        with open("TelegramForwarder.py", "r") as f:
            code = compile(f.read(), "TelegramForwarder.py", 'exec')
            exec(code, globals())
            
    except Exception as e:
        logger.error(f"Error running TelegramForwarder.py: {e}")
        logger.error(traceback.format_exc())
        sys.exit(1)
