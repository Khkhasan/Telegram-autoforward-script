# Telegram Auto Forwarder

A simple and powerful Python tool that automatically forwards messages from one Telegram chat to another. It can forward both text messages and media with captions, with a configurable delay to avoid rate limiting.

## Features

- Forward messages from any source chat (channel, group, or user) to any destination
- Forward media attachments with captions
- Optional keyword filtering (forward only messages containing specific keywords)
- Configurable delay between forwards (default: 5 seconds) to avoid rate limiting
- Support for both username and ID-based forwarding
- Default configuration for forwarding to @INRDealsBot
- Simple setup with detailed user guidance

## Requirements

- Python 3.6+
- Telethon library (`pip install telethon`)
- Telegram API credentials (API ID and API Hash)

## Getting Started

### 1. Get your Telegram API credentials

1. Visit https://my.telegram.org/auth
2. Log in with your phone number
3. Click on "API development tools"
4. Create a new application (fill in any details you want)
5. Note down your **API ID** and **API Hash**

### 2. Installation

1. Clone this repository or download the files
