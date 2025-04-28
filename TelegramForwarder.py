#!/usr/bin/env python3
"""
Telegram Auto Forwarder

This script allows you to forward messages from one Telegram chat to another.
It works with both text messages and media content with captions, and can
forward from public channels to bots like @INRDealsBot.

Features:
- Forward from any source chat (channel, group, or user) to any destination
- Forward media attachments with captions
- Optional keyword filtering
- Configurable delay between forwards (default: 5 seconds)
- Support for both username and ID-based forwarding

Requirements:
- Python 3.7+
- Telethon library (pip install telethon)
- Telegram API credentials (api_id, api_hash) from https://my.telegram.org/apps

Setup instructions:
1. Copy config_template.ini to config.ini
2. Add your Telegram API credentials to config.ini
   (or they will be prompted on first run)
3. Run the script: python telegramForwarder.py

Author: Based on https://github.com/redianmarku/Telegram-Autoforwarder with significant enhancements
"""

import os
import sys
import asyncio
import logging
import configparser
from telethon import TelegramClient, events
from telethon.tl.types import User, Channel, Chat
from telethon.errors import SessionPasswordNeededError

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Global variables
config = configparser.ConfigParser()
config_file = 'config.ini'

def load_config():
    """Load configuration from file or create default if it doesn't exist."""
    if os.path.exists(config_file):
        config.read(config_file)
        print(f"Loaded config from {config_file}")
        print(f"Sections found: {config.sections()}")
    
    # Check all possible section names (case-sensitive)
    telegram_section = None
    forwarding_section = None
    
    for section in config.sections():
        if section.upper() == 'TELEGRAM':
            telegram_section = section
        elif section.upper() == 'FORWARDING':
            forwarding_section = section
    
    # Ensure required sections exist with correct case
    if telegram_section:
        # Use the existing section with the case it has
        if 'Telegram' not in config:
            config['Telegram'] = {}
            # Copy values from the section with different case
            for key in config[telegram_section]:
                config['Telegram'][key] = config[telegram_section][key]
    else:
        config['Telegram'] = {}
        
    if forwarding_section:
        # Use the existing section with the case it has
        if 'Forwarding' not in config:
            config['Forwarding'] = {}
            # Copy values from the section with different case
            for key in config[forwarding_section]:
                config['Forwarding'][key] = config[forwarding_section][key]
    else:
        config['Forwarding'] = {
            'destination_chat_id': '@INRDealsBot',  # Default destination
            'forward_media': 'true',
            'delay_seconds': '5'
        }

def get_api_credentials():
    """
    Get API credentials from environment variables, config file, or prompt user.
    Returns (api_id, api_hash, phone)
    """
    load_config()
    
    # First check environment variables
    api_id = os.environ.get('TELEGRAM_API_ID')
    api_hash = os.environ.get('TELEGRAM_API_HASH')
    phone = os.environ.get('TELEGRAM_PHONE')
    
    # Check for telegram credentials in any section of the config
    for section in config.sections():
        if section.upper() == 'TELEGRAM':
            # Case-insensitive check for keys
            section_keys = {k.lower(): k for k in config[section].keys()}
            
            # Check for api_id with any case
            if not api_id and 'api_id'.lower() in section_keys:
                actual_key = section_keys['api_id'.lower()]
                api_id = config[section][actual_key]
                print(f"Found API ID in config section {section}: {api_id}")
            
            # Check for api_hash with any case
            if not api_hash and 'api_hash'.lower() in section_keys:
                actual_key = section_keys['api_hash'.lower()]
                api_hash = config[section][actual_key]
                print(f"Found API Hash in config section {section}")
            
            # Check for phone with any case
            if not phone and 'phone'.lower() in section_keys:
                actual_key = section_keys['phone'.lower()]
                phone = config[section][actual_key]
                print(f"Found Phone in config section {section}: {phone}")
    
    # Skip prompting if all values already exist
    if api_id and api_hash and phone:
        # Save to config in case they were from env vars
        config['Telegram']['api_id'] = api_id
        config['Telegram']['api_hash'] = api_hash
        config['Telegram']['phone'] = phone
        save_config()
        return api_id, api_hash, phone
        
    # Finally, prompt the user
    print("\n===== Telegram API Credentials Setup =====")
    print("Please enter your Telegram API credentials:")
    print("(You can get these from https://my.telegram.org/apps)")
    api_id = input("API ID: ")
    api_hash = input("API Hash: ")
    phone = input("Phone number (with country code, e.g. +1234567890): ")
    
    # Save credentials to config
    config['Telegram']['api_id'] = api_id
    config['Telegram']['api_hash'] = api_hash
    config['Telegram']['phone'] = phone
    save_config()
    
    return api_id, api_hash, phone

# [Keep the rest of the original functions]

async def main():
    """Main function to run the script."""
    try:
        # Get API credentials
        api_id, api_hash, phone = get_api_credentials()
        
        # Convert api_id to int to prevent errors
        try:
            api_id = int(api_id)
        except ValueError:
            print(f"Error: API ID must be a number, got: {api_id}")
            api_id, api_hash, phone = get_api_credentials()
            api_id = int(api_id)
        
        # Create the client
        client = TelegramClient('telegram_forwarder_session', api_id, api_hash)
        
        print(f"Connecting to Telegram as {phone}...")
        await client.start()
        
        # Check if authorization is needed
        if not await client.is_user_authorized():
            print(f"Sending code request to {phone}")
            await client.send_code_request(phone)
            code = input('Enter the verification code sent to your Telegram: ')
            
            try:
                await client.sign_in(phone, code)
            except SessionPasswordNeededError:
                # 2FA is enabled
                password = input('Two-step verification is enabled. Enter your password: ')
                await client.sign_in(password=password)
            
            print("Successfully logged in!")
        
        me = await client.get_me()
        print(f"Connected to Telegram as {me.first_name}")
        
        # Display the interactive menu
        await interactive_menu(client)
    
    except KeyboardInterrupt:
        print("\nExiting...")
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        if 'client' in locals() and hasattr(client, 'disconnect'):
            await client.disconnect()

if __name__ == "__main__":
    # Run the main function
    asyncio.run(main())
