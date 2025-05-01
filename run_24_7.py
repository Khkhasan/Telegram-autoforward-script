#!/usr/bin/env python3
"""
Telegram Auto Forwarder 24/7 Runner

This script combines the Telegram Auto Forwarder with a keep-alive server
for running 24/7 on Replit with UptimeRobot. It automatically starts forwarding
without any menu interaction required.

Usage:
    Just run this script and it will:
    1. Start a keep-alive web server for UptimeRobot
    2. Load your existing configuration from config.ini
    3. Connect to Telegram and start forwarding automatically

    python run_24_7.py
"""

import asyncio
import configparser
import logging
import os
import sys
import time
import traceback
from flask import Flask
from threading import Thread

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# ======================== KEEP-ALIVE SERVER ========================

# Create a simple Flask app for UptimeRobot
app = Flask(__name__)

@app.route('/')
def home():
    return "Telegram Forwarder is running 24/7!"

@app.route('/ping')
def ping():
    """This endpoint is specifically for UptimeRobot to ping"""
    return "OK"

def run_keep_alive():
    """Run the Flask server directly on port 8080"""
    # Disable Flask's internal logging
    log = logging.getLogger('werkzeug')
    log.setLevel(logging.ERROR)
    
    try:
        # Run the server
        app.run(host='0.0.0.0', port=8080, debug=False)
    except OSError as e:
        if "Address already in use" in str(e):
            # Port already in use, try another port
            logger.info("Port 8080 already in use, trying port 3000...")
            app.run(host='0.0.0.0', port=3000, debug=False)
        else:
            raise

def start_keep_alive():
    """Start the keep-alive server in a separate thread"""
    t = Thread(target=run_keep_alive)
    t.daemon = True
    t.start()
    logger.info("Keep alive server started on port 8080!")
    logger.info("IMPORTANT: Monitor this URL with UptimeRobot: https://YOUR-REPLIT-NAME.replit.app/ping")

# ======================== TELEGRAM FORWARDER ========================

async def start_forwarding():
    """Start the forwarding process with existing configuration"""
    try:
        # Import Telethon first to ensure it's available
        from telethon import TelegramClient, events
        from telethon.errors import SessionPasswordNeededError, FloodWaitError
        
        # Load configuration from config.ini
        config = configparser.ConfigParser()
        if os.path.exists('config.ini'):
            config.read('config.ini')
        else:
            logger.error("Config file not found! Please run TelegramForwarder.py first to set up.")
            return

        # Make sure the sections exist (case-insensitive check)
        telegram_section = None
        forwarding_section = None
        
        for section in config.sections():
            if section.upper() == 'TELEGRAM':
                telegram_section = section
            elif section.upper() == 'FORWARDING':
                forwarding_section = section
        
        if not telegram_section or not forwarding_section:
            logger.error("Required sections missing from config.ini. Please run TelegramForwarder.py to set up.")
            return
            
        # Get API credentials
        api_id = config[telegram_section].get('api_id', '')
        api_hash = config[telegram_section].get('api_hash', '')
        phone = config[telegram_section].get('phone', '')
        
        # Make sure api_id contains only digits and convert to int
        if api_id:
            # Remove any non-digit characters
            api_id = ''.join(filter(str.isdigit, api_id))
            api_id = int(api_id)
        
        # Get forwarding settings
        source_chat_id = config[forwarding_section].get('source_chat_id', '')
        destination_chat_id = config[forwarding_section].get('destination_chat_id', '@INRDealsBot')
        forward_media = config[forwarding_section].get('forward_media', 'true').lower() == 'true'
        
        # Get optional keywords for filtering
        keywords_str = config[forwarding_section].get('keywords', '')
        keywords = [k.strip() for k in keywords_str.split(',')] if keywords_str else []
        
        # Make sure we have the required configuration
        if not all([api_id, api_hash, phone, source_chat_id, destination_chat_id]):
            logger.error("Missing required configuration. Please run TelegramForwarder.py first.")
            return
            
        # Create the Telegram client
        session_file = "telegram_forwarder_session"
        client = TelegramClient(session_file, api_id, api_hash)
        
        # Connect to Telegram
        logger.info("Connecting to Telegram...")
        await client.connect()
        
        # Check if we need to log in
        if not await client.is_user_authorized():
            logger.info(f"Not authorized. Sending code request to {phone}")
            await client.send_code_request(phone)
            
            code = input("Enter the code you received: ")
            
            try:
                await client.sign_in(phone, code)
            except SessionPasswordNeededError:
                password = input("Two-step verification is enabled. Please enter your password: ")
                await client.sign_in(password=password)
        
        # Get information about ourselves
        me = await client.get_me()
        logger.info(f"Connected to Telegram as {me.first_name}")
        
        # Function to handle new messages
        @client.on(events.NewMessage(chats=source_chat_id))
        async def message_handler(event):
            """Handle new messages in the source chat."""
            try:
                # Get the message text
                message_text = event.message.message or ""
                
                # Check if the message contains any of the keywords
                if keywords and not any(keyword.lower() in message_text.lower() for keyword in keywords):
                    logger.info(f"Message doesn't contain keywords: {message_text[:50]}...")
                    return
                
                # Log the message
                logger.info(f"Forwarding message: {message_text[:50]}...")
                
                # Forward the message
                if forward_media and event.message.media:
                    # This is a media message with or without caption
                    await client.send_file(
                        destination_chat_id,
                        file=event.message.media,
                        caption=message_text
                    )
                    logger.info("Media forwarded successfully!")
                else:
                    # This is a text-only message
                    await client.send_message(
                        destination_chat_id,
                        message_text
                    )
                    logger.info("Message forwarded successfully!")
                
                # Sleep to avoid rate limits
                delay = int(config[forwarding_section].get('delay_seconds', '5'))
                logger.info(f"Waiting {delay} seconds before next forward...")
                await asyncio.sleep(delay)
                
            except Exception as e:
                logger.error(f"Error forwarding message: {e}")
                logger.error(traceback.format_exc())
        
        # Start event loop
        logger.info(f"Starting automatic forwarding from {source_chat_id} to {destination_chat_id}")
        logger.info(f"Keywords filter: {keywords if keywords else 'None (all messages will be forwarded)'}")
        logger.info("Press Ctrl+C to stop")
        logger.info("REMINDER: This script will continue running as long as UptimeRobot pings your Replit URL")
        
        # Keep the client running
        await client.run_until_disconnected()
        
    except ImportError:
        logger.error("Telethon library not installed. Install it with: pip install telethon")
        
    except Exception as e:
        logger.error(f"Error during startup: {e}")
        logger.error(traceback.format_exc())
        return False

# ======================== MAIN SCRIPT ========================

async def main():
    try:
        # Start the keep-alive server first
        start_keep_alive()
        
        # Print important info for UptimeRobot setup
        print("\n" + "="*80)
        print("IMPORTANT: SET UP UPTIMEROBOT CORRECTLY")
        print("="*80)
        print("1. Go to uptimerobot.com and create a free account")
        print("2. Click 'Add New Monitor'")
        print("3. Select HTTP(s) monitor type")
        print("4. Set the URL to: https://YOUR-REPLIT-NAME.replit.app/ping")
        print("   (Replace YOUR-REPLIT-NAME with your actual Replit project name)")
        print("5. Set monitoring interval to 5 minutes")
        print("6. Click 'Create Monitor'")
        print("="*80 + "\n")
        
        # Give the keep-alive server a moment to start
        time.sleep(2)
        
        # Start the Telegram forwarder
        logger.info("Starting Telegram Auto Forwarder in 24/7 mode...")
        await start_forwarding()
        
    except Exception as e:
        logger.error(f"Error in main function: {e}")
        logger.error(traceback.format_exc())
        sys.exit(1)


if __name__ == "__main__":
    # Loop forever to restart if there are any issues
    while True:
        try:
            # Use asyncio.run() for Python 3.7+
            asyncio.run(main())
        except KeyboardInterrupt:
            # Exit cleanly on Ctrl+C
            print("\nShutting down by user request...")
            sys.exit(0)
        except Exception as e:
            # Any other exception, log and restart
            print(f"ERROR: {e}")
            print("Restarting in 10 seconds...")
            time.sleep(10)
