#!/usr/bin/env python3
"""
Script to automatically start Telegram forwarding using the existing configuration.

This script loads your configuration from config.ini and starts forwarding messages
without showing the interactive menu. Great for running as a background service
or automated task.
"""
import asyncio
import os
import configparser
import logging
from telethon import TelegramClient
from telethon.errors import SessionPasswordNeededError

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

async def main():
    """Main function to run the script."""
    try:
        # Load configuration
        config = configparser.ConfigParser()
        if os.path.exists('config.ini'):
            config.read('config.ini')
        else:
            print("Error: config.ini file not found.")
            print("Please run TelegramForwarder.py first to set up your configuration.")
            return
        
        # Check if config is properly set up
        if 'Telegram' not in config or 'Forwarding' not in config:
            print("Error: config.ini is not properly configured.")
            print("Please run TelegramForwarder.py first to set up your configuration.")
            return
        
        # Get API credentials
        if ('api_id' in config['Telegram'] and 
            'api_hash' in config['Telegram'] and 
            'phone' in config['Telegram']):
            api_id = config['Telegram']['api_id']
            api_hash = config['Telegram']['api_hash']
            phone = config['Telegram']['phone']
        else:
            # Try environment variables
            api_id = os.environ.get('TELEGRAM_API_ID')
            api_hash = os.environ.get('TELEGRAM_API_HASH')
            phone = os.environ.get('TELEGRAM_PHONE')
            
            if not (api_id and api_hash and phone):
                print("Error: API credentials not found in config or environment variables.")
                print("Please run TelegramForwarder.py first to set up your configuration.")
                return
        
        # Use a stable session name to avoid re-authentication each time
        session_name = 'telegram_forwarder_session'
        client = TelegramClient(session_name, api_id, api_hash)
        
        # Get verification code from environment
        verification_code = os.environ.get('TELEGRAM_CODE')
        
        print(f"Starting Telegram Forwarder with phone: {phone}")
        if verification_code:
            print("Verification code found in environment variables")
        
        # Custom start function to handle login
        async def custom_start():
            await client.connect()
            if not await client.is_user_authorized():
                print(f"Not logged in. Sending verification code request to {phone}")
                await client.send_code_request(phone)
                
                if verification_code:
                    print(f"Using verification code from environment: {verification_code[:1]}****")
                    try:
                        await client.sign_in(phone, verification_code)
                        print(f"Signed in successfully!")
                        return True
                    except Exception as e:
                        print(f"Error with automatic sign in: {e}")
                
                # Fall back to manual input if automatic fails or no code provided
                try:
                    code = input('Enter the verification code sent to your Telegram: ')
                    print(f"Signing in with code...")
                    await client.sign_in(phone, code)
                    print(f"Signed in successfully!")
                except SessionPasswordNeededError:
                    # 2FA is enabled
                    password = input('Two-factor authentication enabled. Enter your password: ')
                    await client.sign_in(password=password)
                except Exception as e:
                    print(f"Error during sign in: {e}")
                    return False
            
            print("Authenticated with Telegram successfully!")
            return True
        
        # Try to start the client with our custom function
        if not await custom_start():
            print("Authentication failed. Please try again.")
            return
        
        # Import the forwarding function from TelegramForwarder
        try:
            # First try to import directly
            try:
                from TelegramForwarder import start_forwarding
            except ImportError:
                # Try from the package
                from telegram_forwarder_package.TelegramForwarder import start_forwarding
                
            # Load forwarding settings from config
            if ('source_chat_id' in config['Forwarding'] and 
                'destination_chat_id' in config['Forwarding']):
                
                source_chat_id = config['Forwarding']['source_chat_id']
                destination_chat_id = config['Forwarding'].get('destination_chat_id', '@INRDealsBot')
                keywords = config['Forwarding'].get('keywords', '').split(',') if config['Forwarding'].get('keywords') else []
                forward_media = config['Forwarding'].get('forward_media', 'true').lower() == 'true'
                delay_seconds = int(config['Forwarding'].get('delay_seconds', '5'))
                
                print(f"\n===== Starting Telegram Auto Forwarder =====")
                print(f"Source: {source_chat_id}")
                print(f"Destination: {destination_chat_id}")
                print(f"Keywords: {', '.join(keywords) if keywords and keywords != [''] else 'No filter (forwarding all messages)'}")
                print(f"Media forwarding: {'Enabled' if forward_media else 'Disabled'}")
                print(f"Delay between forwards: {delay_seconds} seconds")
                print("\nPress Ctrl+C to stop forwarding.\n")
                
                try:
                    await start_forwarding(client, source_chat_id, destination_chat_id, keywords, forward_media)
                except KeyboardInterrupt:
                    print("\nForwarding stopped by user")
            else:
                print("Error: Forwarding configuration is incomplete.")
                print("Please run TelegramForwarder.py first to set up forwarding source and destination.")
        except ImportError as e:
            print(f"Error importing modules: {e}")
            print("Please make sure TelegramForwarder.py is in the same directory.")
    
    except KeyboardInterrupt:
        print("\nExiting...")
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        if 'client' in locals() and hasattr(client, 'is_connected') and client.is_connected():
            await client.disconnect()

if __name__ == "__main__":
    asyncio.run(main())