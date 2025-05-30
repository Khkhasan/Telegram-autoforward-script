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

def save_config():
    """Save the current configuration to the config file."""
    with open(config_file, 'w') as f:
        config.write(f)
    print(f"Configuration saved to {config_file}")

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

async def get_entity_name(client, entity_id):
    """Get the name of a Telegram entity (user, chat, channel)."""
    try:
        # Check if it's a username format
        if isinstance(entity_id, str) and entity_id.startswith('@'):
            entity = await client.get_entity(entity_id)
        else:
            try:
                entity = await client.get_entity(int(entity_id))
            except ValueError:
                entity = await client.get_entity(entity_id)
        
        if isinstance(entity, User):
            return f"{entity.first_name} {entity.last_name if entity.last_name else ''} (@{entity.username if entity.username else 'No username'})"
        elif isinstance(entity, (Channel, Chat)):
            return entity.title
        else:
            return f"Entity {entity_id}"
    except Exception as e:
        logger.error(f"Error getting entity name: {e}")
        return f"Unknown Entity {entity_id}"

async def list_chats(client):
    """List all dialogs (chats) that the user is part of."""
    print("\nFetching your chats, please wait...\n")
    print("=" * 60)
    print(f"{'Type':<10} | {'Name':<25} | {'ID':<15} | {'Username':<15}")
    print("=" * 60)
    
    async for dialog in client.iter_dialogs():
        entity = dialog.entity
        
        if isinstance(entity, User):
            name = f"{entity.first_name} {entity.last_name if entity.last_name else ''}"
            username = f"@{entity.username}" if entity.username else "None"
            print(f"{'User':<10} | {name[:25]:<25} | {entity.id:<15} | {username:<15}")
        elif isinstance(entity, (Channel, Chat)):
            chat_type = "Channel" if isinstance(entity, Channel) and entity.broadcast else "Group"
            username = f"@{entity.username}" if hasattr(entity, 'username') and entity.username else "None"
            print(f"{chat_type:<10} | {entity.title[:25]:<25} | {entity.id:<15} | {username:<15}")
        
        print("-" * 60)

async def setup_forwarding(client):
    """Configure forwarding settings."""
    load_config()
    
    print("\n===== Forwarding Setup =====")
    
    # Source chat configuration
    if 'source_chat_id' in config['Forwarding']:
        current = config['Forwarding']['source_chat_id']
        print(f"Current source chat ID: {current}")
        try:
            name = await get_entity_name(client, current)
            print(f"Current source chat name: {name}")
        except Exception as e:
            print(f"Unable to get source chat name: {e}")
        change = input("Change source chat? (y/n): ").lower() == 'y'
    else:
        change = True
    
    if change:
        source_chat_id = input("Enter source chat ID (where to monitor messages from): ")
        config['Forwarding']['source_chat_id'] = source_chat_id
        
    # Destination chat configuration (default to @INRDealsBot)
    if 'destination_chat_id' in config['Forwarding']:
        current = config['Forwarding']['destination_chat_id']
        print(f"Current destination chat ID: {current}")
        try:
            name = await get_entity_name(client, current)
            print(f"Current destination chat name: {name}")
        except Exception as e:
            print(f"Unable to get destination chat name: {e}")
        change = input("Change destination chat? (y/n, default is @INRDealsBot): ").lower() == 'y'
    else:
        change = False
        config['Forwarding']['destination_chat_id'] = '@INRDealsBot'
    
    if change:
        destination_chat_id = input("Enter destination chat ID (where to forward messages to, default @INRDealsBot): ") or '@INRDealsBot'
        config['Forwarding']['destination_chat_id'] = destination_chat_id
    
    # Keywords configuration
    if 'keywords' in config['Forwarding']:
        current = config['Forwarding']['keywords']
        print(f"Current keywords filter: {current if current else 'None (forwarding all messages)'}")
        change = input("Change keywords? (y/n): ").lower() == 'y'
    else:
        change = True
    
    if change:
        keywords = input("Enter keywords to filter (comma-separated, leave empty to forward all messages): ")
        config['Forwarding']['keywords'] = keywords
    
    # Media forwarding configuration
    if 'forward_media' in config['Forwarding']:
        current = config['Forwarding']['forward_media']
        print(f"Forward media with captions: {current}")
        change = input("Change media forwarding setting? (y/n): ").lower() == 'y'
    else:
        change = False
        config['Forwarding']['forward_media'] = 'true'
    
    if change:
        forward_media = input("Forward media with captions? (y/n, default y): ").lower()
        config['Forwarding']['forward_media'] = 'true' if forward_media != 'n' else 'false'
    
    # Delay between forwards option
    if 'delay_seconds' in config['Forwarding']:
        current = config['Forwarding']['delay_seconds']
        print(f"Current delay between forwards (seconds): {current}")
        change = input("Change delay setting? (y/n): ").lower() == 'y'
    else:
        config['Forwarding']['delay_seconds'] = '5'  # Default to 5 seconds
        change = False
    
    if change:
        try:
            delay = int(input("Enter delay between forwards in seconds (default: 5): ") or "5")
            config['Forwarding']['delay_seconds'] = str(delay)
        except ValueError:
            print("Invalid input. Using default delay of 5 seconds.")
            config['Forwarding']['delay_seconds'] = '5'
    
    save_config()
    print("\nForwarding configuration saved!")
    
    return config['Forwarding']['source_chat_id'], config['Forwarding']['destination_chat_id'], \
           config['Forwarding']['keywords'].split(',') if config['Forwarding']['keywords'] else [], \
           config['Forwarding']['forward_media'].lower() == 'true'

async def start_forwarding(client, source_chat_id, destination_chat_id, keywords, forward_media=True):
    """Start the forwarding process."""
    # Try to get source and destination chat names
    try:
        # First try to interpret it as an integer (channel/chat ID)
        try:
            if source_chat_id.startswith('@'):
                # It's a username
                source_entity = await client.get_entity(source_chat_id)
            else:
                # Try as an integer
                source_entity = await client.get_entity(int(source_chat_id))
        except ValueError:
            # Not an integer, treat as username or phone
            source_entity = await client.get_entity(source_chat_id)
            
        source_name = source_entity.title if hasattr(source_entity, 'title') else f"Chat {source_chat_id}"
    except Exception as e:
        logger.error(f"Error getting source entity: {e}")
        source_name = f"Chat {source_chat_id}"
    
    # Try to handle destination - could be int, string (username) or phone number
    try:
        # Check if it's a username format
        if destination_chat_id.startswith('@'):
            print(f"Using username format: {destination_chat_id}")
            destination_entity = await client.get_entity(destination_chat_id)
        else:
            # Try as an integer
            try:
                destination_entity = await client.get_entity(int(destination_chat_id))
            except ValueError:
                # Not an integer, treat as username or phone
                destination_entity = await client.get_entity(destination_chat_id)
            
        destination_name = destination_entity.title if hasattr(destination_entity, 'title') else f"Chat {destination_chat_id}"
    except Exception as e:
        logger.error(f"Error getting destination entity: {e}")
        destination_name = f"Chat {destination_chat_id}"
    
    # Get the delay from config
    forward_delay = int(config['Forwarding'].get('delay_seconds', '5'))
    
    print(f"\nMonitoring messages from {source_name}...")
    if keywords and keywords != ['']:
        keywords = [k.strip() for k in keywords if k.strip()]
        if keywords:
            print(f"Filtering for messages containing any of these keywords: {', '.join(keywords)}")
        else:
            print("No valid keywords specified, forwarding all messages")
    else:
        print("No keywords filter, forwarding all messages")
    print(f"Forwarding to {destination_name} ({destination_chat_id})")
    print(f"Media forwarding: {'Enabled' if forward_media else 'Disabled'}")
    print(f"Delay between forwards: {forward_delay} seconds")
    print("\nPress Ctrl+C to stop\n")
    
    @client.on(events.NewMessage(chats=int(source_chat_id) if source_chat_id.strip('-').isdigit() else source_chat_id))
    async def message_handler(event):
        """Handle new messages in the source chat."""
        message = event.message
        
        # Check if message contains any of the keywords
        if keywords and keywords != ['']:
            # Check if message text contains any of the keywords
            message_text = message.message or ""
            found_keyword = False
            for keyword in keywords:
                if keyword.lower() in message_text.lower():
                    found_keyword = True
                    break
            
            if not found_keyword:
                return  # Skip this message
        
        try:
            # Try to forward the message with media if it has any
            if message.media and forward_media:
                logger.info(f"Forwarding message {message.id} with media to {destination_chat_id}")
                await client.send_message(destination_chat_id, message)
                await asyncio.sleep(forward_delay)  # Wait to avoid rate limiting
            else:
                if message.message:  # Only forward if there's actual text content
                    logger.info(f"Forwarding message {message.id} text to {destination_chat_id}")
                    await client.send_message(destination_chat_id, message.message)
                    await asyncio.sleep(forward_delay)  # Wait to avoid rate limiting
        except Exception as e:
            logger.error(f"Error forwarding message: {e}")

    # Keep running until interrupted
    print("Forwarding is now active. Press Ctrl+C to stop.")
    
    # Return the event handler for later use
    return message_handler

async def interactive_menu(client):
    """Display interactive menu for the user."""
    while True:
        print("\n===== Telegram Auto Forwarder =====")
        print("1. List all chats")
        print("2. Setup forwarding")
        print("3. Start forwarding")
        print("4. Exit")
        choice = input("\nSelect an option: ")
        
        if choice == '1':
            await list_chats(client)
        elif choice == '2':
            await setup_forwarding(client)
        elif choice == '3':
            # Check if source and destination are configured
            load_config()
            if 'source_chat_id' not in config['Forwarding'] or 'destination_chat_id' not in config['Forwarding']:
                print("Error: Source and destination chats not configured.")
                print("Please choose option 2 first to setup forwarding.")
                continue
            
            source_chat_id = config['Forwarding']['source_chat_id']
            destination_chat_id = config['Forwarding']['destination_chat_id']
            keywords = config['Forwarding'].get('keywords', '').split(',') if config['Forwarding'].get('keywords') else []
            forward_media = config['Forwarding'].get('forward_media', 'true').lower() == 'true'
            
            print("\nStarting forwarding...")
            try:
                await start_forwarding(client, source_chat_id, destination_chat_id, keywords, forward_media)
                # Keep the script running until Ctrl+C
                while True:
                    await asyncio.sleep(1)
            except KeyboardInterrupt:
                print("\nForwarding stopped")
            except Exception as e:
                print(f"Error during forwarding: {e}")
        elif choice == '4':
            print("Exiting...")
            break
        else:
            print("Invalid choice. Please try again.")

async def main():
    """Main function to run the script."""
    try:
        # Get API credentials
        api_id, api_hash, phone = get_api_credentials()
        
        # Convert api_id to int to prevent errors
        try:
            # Clean any non-digit characters from the API ID
            api_id_clean = ''.join(c for c in str(api_id) if c.isdigit())
            api_id = int(api_id_clean)
            print(f"Using API ID: {api_id}")
        except ValueError:
            print(f"Error: API ID must be a number, got: {api_id}")
            # Prompt user for correct API ID
            print("Please enter a valid API ID (must be a number):")
            api_id = input("API ID: ")
            api_id = int(api_id)
            # Update the config with the correct API ID
            config['Telegram']['api_id'] = str(api_id)
            save_config()
        
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
