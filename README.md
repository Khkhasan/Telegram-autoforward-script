# Telegram Auto Forwarder

This script allows you to forward messages from any Telegram channel, group or chat to another destination (like @INRDealsBot).

## Features

- Forward messages from any source chat (public channel, group, or private chat)
- Forward media attachments with captions
- Filter messages by keywords
- Configurable delay between forwards to avoid rate limits
- Support for both username and ID-based chat identification
- Interactive menu for easy setup and operation

## Requirements

- Python 3.7 or higher
- Telethon library
- Telegram API credentials (from https://my.telegram.org/apps)

## Installation

1. Clone this repository:
   git clone https://github.com/YOUR_USERNAME/telegram-auto-forwarder.git
cd telegram-auto-forwarder

3. Set up configuration:
- Copy `config_template.ini` to `config.ini`
- Fill in your Telegram API credentials (or they will be prompted on first run)

## Usage

Run the script with:
python telegramForwarder.py

On first run, the script will:
1. Ask for your Telegram API credentials if not provided in config.ini
2. Request verification code sent to your Telegram account
3. Present an interactive menu with options:
   - List all chats (to find chat IDs)
   - Setup forwarding (configure source, destination, filters)
   - Start forwarding
   - Exit

## Setting up Forwarding

1. Choose option 1 to list all available chats and get the ID of your source chat
2. Choose option 2 to set up forwarding:
   - Enter source chat ID (where to monitor messages from)
   - Default destination is @INRDealsBot, but you can change it
   - Set keywords to filter (optional)
   - Configure media forwarding and delay settings

## Running in Background

For running on a server continuously:
- Use a terminal multiplexer like `screen` or `tmux`
- Or set up as a systemd service

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgements

Based on https://github.com/redianmarku/Telegram-Autoforwarder with significant enhancements.
