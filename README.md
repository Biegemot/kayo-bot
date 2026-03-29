# Кайо (Kayo) - Furry Bunny Telegram Bot

A Telegram bot named Кайо (Kayo) designed to be a friendly and helpful companion.

## Features

- Activity tracking per chat (separate SQLite database for each chat)
- Auto-update functionality (checks for newer releases on startup)
- Friendly interactive commands: hug, bite, pat, boop
- Statistics and rankings: top users, today's top users, personal stats
- Automatic reactions to messages with various furry-themed responses
- Version information via `/about` command

## Installation

1. Clone the repository:
   ```
   git clone https://github.com/Biegemot/kayo-bot.git
   cd kayo-bot
   ```

2. Install the required Python packages:
   ```
   pip install -r requirements.txt
   ```

3. Create a `.env` file based on `config.example.env` and add your Telegram bot token:
   ```
   TELEGRAM_BOT_TOKEN=your_token_here
   ```

## Usage

Run the bot:
   ```
   python main.py
   ```

The bot will automatically check for updates on startup and notify if a newer version is available.

## Commands

- `/start` - Initialize the bot and get a welcome message
- `/help` - Show help message with available commands
- `/about` - Info about the bot and version
- `/hug [user]` - Hug a user (or yourself if no user mentioned)
- `/bite [user]` - Playfully bite a user
- `/pat [user]` - Pat a user affectionately
- `/boop [user]` - Boop a user's nose
- `/top` - See top users by total message count in current chat
- `/today` - See top users by today's message count in current chat
- `/me` - See your own stats and title in current chat

## Per-Chat Databases

The bot maintains separate SQLite databases for each chat to ensure data isolation. Each chat gets its own database file stored in the `bot/data/` directory (e.g., `data/chat_123456789.db`). This ensures that statistics and user data are specific to each chat and don't mix between different groups or private chats.

## Auto-Update Functionality

On startup, the bot checks the latest release on GitHub (Biegemot/kayo-bot) and compares it with the current version. If a newer release is found, it will:
1. Download the latest release asset (kayo-bot-<version>.exe for Windows)
2. Replace the current executable
3. Restart the bot to apply the update

The update check happens only once at startup to avoid excessive API calls. Ensure the bot has internet access and write permissions to its directory for the update to work properly.

## Project Structure

```
kayo-bot/
│
├── bot/
│   ├── __init__.py
│   ├── handlers/
│   │   ├── __init__.py
│   │   ├── hug.py
│   │   ├── bite.py
│   │   ├── pat.py
│   │   ├── boop.py
│   │   ├── reactions.py
│   │   └── general.py
│   ├── services/
│   │   ├── __init__.py
│   │   ├── activity.py
│   │   ├── auto_update.py
│   │   └── db_manager.py
│   └── database/
│       └── __init__.py
│
├── main.py
├── config.example.env
├── requirements.txt
├── .gitignore
└── README.md
```

## License

This project is licensed under the MIT License.