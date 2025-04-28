#!/usr/bin/env python3
"""
Telegram Auto Forwarder Wrapper

This wrapper ensures the main script is called correctly and keeps the script running 24/7.
It starts a web server that can be pinged by UptimeRobot to keep the Replit instance alive.

Usage:
    Simply run this script to start the Telegram Auto Forwarder.

    python telegramForwarder.py
"""

import os
import sys
import traceback
import logging
from keep_alive import keep_alive

# Set up detailed logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Start the keep-alive server for UptimeRobot
keep_alive()
logger.info("Keep-alive server started for UptimeRobot monitoring")
logger.info("Your Replit URL can now be monitored at: https://YOUR-REPLIT-URL.repl.co")
logger.info("Add this URL to UptimeRobot to keep the script running 24/7")

# Simply run the actual file with proper capitalization
if __name__ == "__main__":
    try:
        logger.info("Starting TelegramForwarder.py wrapper")
        logger.info(f"Current directory: {os.getcwd()}")
        
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
