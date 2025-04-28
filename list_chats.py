#!/usr/bin/env python3
"""
A simple utility script to list all the Telegram chats you are part of.
This helps you identify the correct source chat IDs for forwarding.
"""
import os
import asyncio
import configparser
import logging
from telethon import TelegramClient
from telethon.tl.types import User, Channel, Chat
from telethon.errors import SessionPasswordNeededError

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

async def main():
    """Main function to list all chats."""
    config = configparser.ConfigParser()
    if os.path.exists('config.ini'):
        config.read('config.ini')
    
    # Get API credentials
    if 'Telegram' in config and 'api_id' in config['Telegram'] and 'api_hash' in config['Telegram'] and 'phone' in config['Telegram']:
        api_id = config['Telegram']['api_id']
        api_hash = config['Telegram']['api_hash']
        phone = config['Telegram']['phone']
    else:
        # Try environment variables
        api_id = os.environ.get('TELEGRAM_API_ID')
        api_hash = os.environ.get('TELEGRAM_API_HASH')
        phone = os.environ.get('TELEGRAM_PHONE')
        
        if not (api_id and api_hash and phone):
            print("API credentials not found in config.ini or environment variables.")
            print("Please enter your Telegram API credentials:")
            api_id = input("API ID: ")
            api_hash = input("API Hash: ")
            phone = input("Phone number (with country code, e.g. +1234567890): ")
            
            # Save to config for future use
            if 'Telegram' not in config:
                config['Telegram'] = {}
            config['Telegram']['api_id'] = api_id
            config['Telegram']['api_hash'] = api_hash
            config['Telegram']['phone'] = phone
            with open('config.ini', 'w') as f:
                config.write(f)
    
    # Create the client
    client = TelegramClient('telegram_forwarder_session', api_id, api_hash)
    
    try:
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
                password = input('Two factor authentication enabled. Enter your password: ')
                await client.sign_in(password=password)
            
            print("Successfully logged in!")
        
        me = await client.get_me()
        print(f"Connected to Telegram as {me.first_name}")
        
        # List all dialogs (chats)
        print("\n===== Your Telegram Chats =====")
        print("Use these IDs to configure your forwarding source\n")
        print("=" * 70)
        print(f"{'Type':<10} | {'Name':<30} | {'ID':<15} | {'Username':<15}")
        print("=" * 70)
        
        async for dialog in client.iter_dialogs():
            entity = dialog.entity
            
            if isinstance(entity, User):
                name = f"{entity.first_name} {entity.last_name if entity.last_name else ''}"
                username = f"@{entity.username}" if entity.username else "None"
                print(f"{'User':<10} | {name[:30]:<30} | {entity.id:<15} | {username:<15}")
            elif isinstance(entity, (Channel, Chat)):
                chat_type = "Channel" if isinstance(entity, Channel) and entity.broadcast else "Group"
                username = f"@{entity.username}" if hasattr(entity, 'username') and entity.username else "None"
                print(f"{chat_type:<10} | {entity.title[:30]:<30} | {entity.id:<15} | {username:<15}")
            
            print("-" * 70)
        
        print("\nTip: For public channels/groups with usernames, you can use either the numeric ID")
        print("     or the username format (e.g., @channelname) as your source chat ID.")
        print("\nTip: For the destination, using @INRDealsBot is recommended.")
    
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        await client.disconnect()

if __name__ == "__main__":
    asyncio.run(main())