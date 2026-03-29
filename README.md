# Кайо (Kayo) - Furry Bunny Telegram Bot

A Telegram bot named Кайо (Kayo) designed to be a friendly and helpful companion.

## Features

- `/start` - Start the bot and get a welcome message
- `/help` - Get help and list of available commands
- `/remind` - Set a reminder (stub)
- `/backup` - Backup data (stub)

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

## Commands

- `/start` - Initialize the bot
- `/help` - Show help message
- `/remind` - Set a reminder (not implemented yet)
- `/backup` - Backup data (not implemented yet)

## Project Structure

```
kayo-bot/
│
├── bot/
│   ├── __init__.py
│   ├── handlers/
│   │   └── __init__.py
│   ├── services/
│   │   └── __init__.py
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