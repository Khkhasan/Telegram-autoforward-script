#!/usr/bin/env python3
"""
Telegram Auto Forwarder Wrapper

This wrapper ensures the main script is called correctly, regardless of case sensitivity.
It also provides detailed logging to help troubleshoot issues.

Usage:
    Simply run this script to start the Telegram Auto Forwarder.

    python telegramForwarder.py
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

# Run the actual file with proper capitalization
if __name__ == "__main__":
    try:
        logger.info("Starting Telegram Auto Forwarder")
        logger.info(f"Current directory: {os.getcwd()}")
        
        # Execute the main script
        logger.info("Loading TelegramForwarder.py")
        
        # Using exec instead of runpy for better error visibility
        with open("TelegramForwarder.py", "r") as f:
            code = compile(f.read(), "TelegramForwarder.py", 'exec')
            exec(code, globals())
            
    except Exception as e:
        logger.error(f"Error running TelegramForwarder.py: {e}")
        logger.error(traceback.format_exc())
        sys.exit(1)
