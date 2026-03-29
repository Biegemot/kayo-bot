#!/bin/bash
# Linux installer script for Kayo Bot
# Automates the installation process on Linux systems

set -e  # Exit on any error

echo "=== Kayo Bot Linux Installer ==="
echo "This script will help you install Kayo Bot on your Linux system."
echo

# Check if we're in the kayo-bot directory
if [ ! -f "main.py" ] || [ ! -f "requirements.txt" ]; then
    echo "Error: This script must be run from the kayo-bot repository root."
    echo "Current directory: $(pwd)"
    echo "Please navigate to the kayo-bot directory and run this script again."
    exit 1
fi

# Check if git is available
if ! command -v git &> /dev/null; then
    echo "Error: git is not installed. Please install git first."
    exit 1
fi

# Check if python3 is available
if ! command -v python3 &> /dev/null; then
    echo "Error: python3 is not installed. Please install python3 first."
    exit 1
fi

# Check if pip is available
if ! command -v pip3 &> /dev/null; then
    echo "Error: pip3 is not installed. Please install pip3 first."
    exit 1
fi

echo "✓ All required tools are available"
echo

# Create virtual environment (optional but recommended)
echo "Setting up Python virtual environment..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo "✓ Virtual environment created"
else
    echo "✓ Virtual environment already exists"
fi

# Activate virtual environment
source venv/bin/activate
echo "✓ Virtual environment activated"

# Install dependencies
echo "Installing Python dependencies..."
pip3 install --upgrade pip
pip3 install -r requirements.txt
echo "✓ Dependencies installed"
echo

# Create .env file if it doesn't exist, or update token
if [ ! -f ".env" ]; then
    if [ -f "config.example.env" ]; then
        cp config.example.env .env
        echo "✓ Created .env file from config.example.env"
    else
        touch .env
        echo "✓ Created empty .env file"
    fi
fi

# Check if token is already set
CURRENT_TOKEN=$(grep -oP '(?<=^TELEGRAM_BOT_TOKEN=).*' .env 2>/dev/null | head -1)
if [ -z "$CURRENT_TOKEN" ]; then
    echo
    echo "⚠️  Telegram bot token not found!"
    echo "You can get a token from @BotFather in Telegram."
    echo
    read -p "Enter your Telegram bot token: " BOT_TOKEN
    if [ -n "$BOT_TOKEN" ]; then
        # Remove existing TELEGRAM_BOT_TOKEN line if present
        grep -v "^TELEGRAM_BOT_TOKEN=" .env > .env.tmp 2>/dev/null || true
        mv .env.tmp .env
        # Add new token
        echo "TELEGRAM_BOT_TOKEN=$BOT_TOKEN" >> .env
        echo "✓ Token saved to .env"
    else
        echo "⚠️  No token entered. You can add it later by editing .env"
    fi
else
    echo "✓ Bot token is already configured"
fi

echo
echo "=== Installation Complete ==="
echo
echo "To run the bot:"
echo "  1. Activate virtual environment: source venv/bin/activate"
echo "  2. Run the bot: python main.py"
echo
echo "To change token later, run:"
echo "  ./set_token.sh"
echo
echo "For automatic updates, the bot will check for new releases on startup."
echo
echo "Happy bot-keeping! 🐰"