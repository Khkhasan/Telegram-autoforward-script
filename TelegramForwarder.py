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
