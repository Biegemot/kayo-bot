#!/bin/bash
# Kayo Bot — Linux Installer
# Full installation with systemd service

set -e

echo "╔══════════════════════════════════╗"
echo "║   🐰 Kayo Bot Linux Installer    ║"
echo "║   Creator: SkyFox                ║"
echo "╚══════════════════════════════════╝"
echo

# Check we're in the repo
if [ ! -f "main.py" ] || [ ! -f "requirements.txt" ]; then
    echo "Error: Run from the kayo-bot repository root."
    echo "Usage: cd kayo-bot && ./install_linux.sh"
    exit 1
fi

# Check dependencies
echo "Checking dependencies..."
MISSING=""
for cmd in python3 git; do
    if ! command -v $cmd &>/dev/null; then
        MISSING="$MISSING $cmd"
    fi
done

# pip might be pip3
if ! command -v pip3 &>/dev/null && ! command -v pip &>/dev/null; then
    MISSING="$MISSING pip"
fi

if [ -n "$MISSING" ]; then
    echo "Error: Missing dependencies:$MISSING"
    echo "Install them first:"
    echo "  sudo apt install python3 python3-pip python3-venv git  # Debian/Ubuntu"
    echo "  sudo dnf install python3 python3-pip git                # Fedora"
    exit 1
fi
echo "✓ Dependencies OK"
echo

# Create virtual environment
echo "Setting up Python environment..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo "✓ Virtual environment created"
fi
source venv/bin/activate
pip install --upgrade pip -q
pip install -r requirements.txt -q
echo "✓ Python packages installed"
echo

# Token setup
if [ ! -f ".env" ]; then
    [ -f "config.example.env" ] && cp config.example.env .env || touch .env
fi

CURRENT_TOKEN=$(grep -oP '(?<=^TELEGRAM_BOT_TOKEN=).*' .env 2>/dev/null | head -1)
if [ -z "$CURRENT_TOKEN" ]; then
    echo "🔑 Telegram bot token not configured."
    echo "   Get one from @BotFather in Telegram."
    echo
    read -p "   Enter token (or Enter to skip): " BOT_TOKEN
    if [ -n "$BOT_TOKEN" ]; then
        grep -v "^TELEGRAM_BOT_TOKEN=" .env > .env.tmp 2>/dev/null || true
        mv .env.tmp .env
        echo "TELEGRAM_BOT_TOKEN=$BOT_TOKEN" >> .env
        echo "✓ Token saved"
    else
        echo "⚠️  Skipped — set later with: ./manage.sh token"
    fi
else
    echo "✓ Token already configured"
fi
echo

# Make scripts executable
chmod +x manage.sh set_token.sh 2>/dev/null || true

# Ask about systemd service
echo "📦 Systemd service installation (recommended for production)."
echo "   This will run the bot automatically on boot."
echo
read -p "   Install as systemd service? (Y/n): " INSTALL_SERVICE
INSTALL_SERVICE=${INSTALL_SERVICE:-y}

if [ "$INSTALL_SERVICE" = "y" ] || [ "$INSTALL_SERVICE" = "Y" ]; then
    if [ -f "install_service.sh" ]; then
        echo
        bash install_service.sh
    else
        echo "⚠️  install_service.sh not found, skipping service setup"
    fi
else
    echo "Skipped service installation."
    echo
    echo "To run manually:"
    echo "  source venv/bin/activate"
    echo "  python main.py"
fi

echo
echo "═══════════════════════════════════"
echo "✅ Installation complete!"
echo
echo "Management commands:"
echo "  ./manage.sh status   — check status"
echo "  ./manage.sh start    — start bot"
echo "  ./manage.sh stop     — stop bot"
echo "  ./manage.sh restart  — restart bot"
echo "  ./manage.sh logs     — view logs"
echo "  ./manage.sh update   — update bot"
echo "  ./manage.sh token    — change token"
echo
echo "Happy bot-keeping! 🐰"
