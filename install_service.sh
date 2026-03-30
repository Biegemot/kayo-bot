#!/bin/bash
# Kayo Bot — Linux Service Installer
# Installs bot as a systemd user service

set -e

INSTALL_DIR="/opt/kayo-bot"
SERVICE_NAME="kayo-bot"

echo "╔══════════════════════════════╗"
echo "║  Kayo Bot — Service Setup    ║"
echo "║  Creator: SkyFox             ║"
echo "╚══════════════════════════════╝"
echo

# Must be run from repo directory
if [ ! -f "main.py" ] || [ ! -f "requirements.txt" ]; then
    echo "Error: Run this script from the kayo-bot repository root."
    exit 1
fi

# Check dependencies
for cmd in python3 pip3 git; do
    if ! command -v $cmd &> /dev/null; then
        echo "Error: $cmd is not installed."
        exit 1
    fi
done

echo "✓ All dependencies available"
echo

# Get current user
CURRENT_USER=$(whoami)

# Create install directory
echo "Installing to $INSTALL_DIR..."
sudo mkdir -p "$INSTALL_DIR"
sudo cp -r . "$INSTALL_DIR/"
sudo chown -R "$CURRENT_USER":"$CURRENT_USER" "$INSTALL_DIR"
echo "✓ Files copied"

# Setup venv
cd "$INSTALL_DIR"
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi
source venv/bin/activate
pip install --upgrade pip -q
pip install -r requirements.txt -q
echo "✓ Python environment ready"

# Token setup
if [ ! -f ".env" ]; then
    if [ -f "config.example.env" ]; then
        cp config.example.env .env
    else
        touch .env
    fi
fi

CURRENT_TOKEN=$(grep -oP '(?<=^TELEGRAM_BOT_TOKEN=).*' .env 2>/dev/null | head -1)
if [ -z "$CURRENT_TOKEN" ]; then
    echo
    read -p "Enter your Telegram bot token: " BOT_TOKEN
    if [ -n "$BOT_TOKEN" ]; then
        grep -v "^TELEGRAM_BOT_TOKEN=" .env > .env.tmp 2>/dev/null || true
        mv .env.tmp .env
        echo "TELEGRAM_BOT_TOKEN=$BOT_TOKEN" >> .env
        echo "✓ Token saved"
    else
        echo "⚠️  No token — set it later with: $INSTALL_DIR/manage.sh token"
    fi
else
    echo "✓ Token already configured"
fi

# Create systemd service
echo "Creating systemd service..."
sudo tee /etc/systemd/system/${SERVICE_NAME}.service > /dev/null <<EOF
[Unit]
Description=Kayo Telegram Bot — Creator: SkyFox
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=$CURRENT_USER
WorkingDirectory=$INSTALL_DIR
ExecStart=$INSTALL_DIR/venv/bin/python $INSTALL_DIR/main.py
Restart=on-failure
RestartSec=10
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=default.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable $SERVICE_NAME
sudo systemctl start $SERVICE_NAME

echo "✓ Service installed and started"
echo

# Create symlink for manage.sh
ln -sf "$INSTALL_DIR/manage.sh" /usr/local/bin/kayo-bot 2>/dev/null || true

echo "═══════════════════════════════"
echo "✅ Kayo Bot installed!"
echo
echo "Management:"
echo "  kayo-bot status   — check status"
echo "  kayo-bot start    — start bot"
echo "  kayo-bot stop     — stop bot"
echo "  kayo-bot restart  — restart bot"
echo "  kayo-bot logs     — view logs"
echo "  kayo-bot update   — update bot"
echo "  kayo-bot token    — change token"
echo
echo "Or use systemctl:"
echo "  sudo systemctl status $SERVICE_NAME"
echo "═══════════════════════════════"
