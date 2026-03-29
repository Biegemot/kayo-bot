#!/bin/bash
# Set or update the Telegram bot token in .env

ENV_FILE=".env"

if [ ! -f "$ENV_FILE" ]; then
    echo "Creating .env file..."
    touch "$ENV_FILE"
fi

echo "=== Set Telegram Bot Token ==="
echo "You can get a token from @BotFather in Telegram."
echo
read -p "Enter your Telegram bot token: " BOT_TOKEN

if [ -z "$BOT_TOKEN" ]; then
    echo "Error: No token entered."
    exit 1
fi

# Remove existing TELEGRAM_BOT_TOKEN line
grep -v "^TELEGRAM_BOT_TOKEN=" "$ENV_FILE" > "${ENV_FILE}.tmp" 2>/dev/null || true
mv "${ENV_FILE}.tmp" "$ENV_FILE"

# Add new token
echo "TELEGRAM_BOT_TOKEN=$BOT_TOKEN" >> "$ENV_FILE"

echo "✓ Token saved to $ENV_FILE"
echo "Restart the bot to apply changes."
