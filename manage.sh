#!/bin/bash
# Kayo Bot — Management Script
# Usage: kayo-bot [status|start|stop|restart|logs|update|token]

SERVICE_NAME="kayo-bot"
INSTALL_DIR="/opt/kayo-bot"
REPO_DIR="${INSTALL_DIR}"

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
BOLD='\033[1m'
NC='\033[0m'

show_help() {
    echo -e "${BOLD}🐰 Kayo Bot Management${NC}"
    echo
    echo "Usage: kayo-bot <command>"
    echo
    echo "Commands:"
    echo "  status    — show bot status"
    echo "  start     — start the bot"
    echo "  stop      — stop the bot"
    echo "  restart   — restart the bot"
    echo "  logs      — show recent logs (follow with -f)"
    echo "  update    — pull latest code and restart"
    echo "  token     — change Telegram bot token"
    echo "  version   — show current version"
    echo "  help      — show this help"
}

show_status() {
    echo -e "${BOLD}🐰 Kayo Bot Status${NC}"
    echo
    
    # Service status
    if systemctl --user is-active $SERVICE_NAME &>/dev/null; then
        echo -e "Service: ${GREEN}running${NC}"
    elif systemctl is-active $SERVICE_NAME &>/dev/null; then
        echo -e "Service: ${GREEN}running${NC} (system)"
    else
        echo -e "Service: ${RED}stopped${NC}"
    fi
    
    # Version
    if [ -f "$REPO_DIR/version.txt" ]; then
        echo "Version: v$(cat $REPO_DIR/version.txt)"
    fi
    
    # Uptime
    if systemctl --user is-active $SERVICE_NAME &>/dev/null; then
        echo "Uptime: $(systemctl --user show $SERVICE_NAME --property=ActiveEnterTimestamp --value 2>/dev/null || echo 'unknown')"
    fi
}

do_start() {
    if systemctl --user start $SERVICE_NAME 2>/dev/null; then
        echo -e "${GREEN}✓ Bot started${NC}"
    elif sudo systemctl start $SERVICE_NAME 2>/dev/null; then
        echo -e "${GREEN}✓ Bot started (system)${NC}"
    else
        echo -e "${YELLOW}Starting directly...${NC}"
        cd "$REPO_DIR" && source venv/bin/activate && nohup python main.py > bot.log 2>&1 &
        echo -e "${GREEN}✓ Bot started in background${NC}"
    fi
}

do_stop() {
    if systemctl --user stop $SERVICE_NAME 2>/dev/null; then
        echo -e "${GREEN}✓ Bot stopped${NC}"
    elif sudo systemctl stop $SERVICE_NAME 2>/dev/null; then
        echo -e "${GREEN}✓ Bot stopped (system)${NC}"
    else
        pkill -f "python.*main.py" 2>/dev/null && echo -e "${GREEN}✓ Bot stopped${NC}" || echo -e "${RED}Bot not running${NC}"
    fi
}

do_restart() {
    do_stop
    sleep 1
    do_start
}

show_logs() {
    if [ "$2" = "-f" ] || [ "$2" = "--follow" ]; then
        journalctl --user -u $SERVICE_NAME -f 2>/dev/null || tail -f "$REPO_DIR/bot.log"
    else
        journalctl --user -u $SERVICE_NAME -n 50 --no-pager 2>/dev/null || tail -50 "$REPO_DIR/bot.log"
    fi
}

do_update() {
    echo -e "${BOLD}🔄 Updating Kayo Bot...${NC}"
    echo
    
    cd "$REPO_DIR" || { echo -e "${RED}Cannot cd to $REPO_DIR${NC}"; exit 1; }
    
    # Check git
    if ! command -v git &>/dev/null; then
        echo -e "${RED}Error: git not found${NC}"
        exit 1
    fi
    
    # Save current version
    OLD_VERSION=$(cat version.txt 2>/dev/null || echo "unknown")
    echo "Current version: v$OLD_VERSION"
    
    # Fetch and check
    echo "Fetching latest..."
    git fetch origin 2>/dev/null || { echo -e "${RED}Failed to fetch${NC}"; exit 1; }
    
    LOCAL=$(git rev-parse HEAD)
    REMOTE=$(git rev-parse origin/main)
    
    if [ "$LOCAL" = "$REMOTE" ]; then
        echo -e "${GREEN}Already up to date!${NC}"
        return 0
    fi
    
    # Pull changes
    echo "Pulling updates..."
    git pull origin main || { echo -e "${RED}Failed to pull${NC}"; exit 1; }
    
    # Update dependencies if requirements.txt changed
    if git diff --name-only HEAD@{1} HEAD 2>/dev/null | grep -q "requirements.txt"; then
        echo "Updating dependencies..."
        source venv/bin/activate
        pip install -r requirements.txt -q
    fi
    
    NEW_VERSION=$(cat version.txt 2>/dev/null || echo "unknown")
    echo -e "${GREEN}✓ Updated: v$OLD_VERSION → v$NEW_VERSION${NC}"
    
    # Restart
    echo "Restarting bot..."
    do_restart
    
    echo -e "${GREEN}✓ Update complete!${NC}"
}

do_token() {
    cd "$REPO_DIR" || exit 1
    ENV_FILE=".env"
    
    echo -e "${BOLD}🔑 Set Telegram Bot Token${NC}"
    echo "Get a token from @BotFather in Telegram."
    echo
    read -p "Enter token (or press Enter to cancel): " BOT_TOKEN
    
    if [ -z "$BOT_TOKEN" ]; then
        echo "Cancelled."
        return 0
    fi
    
    grep -v "^TELEGRAM_BOT_TOKEN=" "$ENV_FILE" > "${ENV_FILE}.tmp" 2>/dev/null || true
    mv "${ENV_FILE}.tmp" "$ENV_FILE"
    echo "TELEGRAM_BOT_TOKEN=$BOT_TOKEN" >> "$ENV_FILE"
    
    echo -e "${GREEN}✓ Token saved${NC}"
    echo "Restarting bot..."
    do_restart
}

show_version() {
    if [ -f "$REPO_DIR/version.txt" ]; then
        echo "Kayo Bot v$(cat $REPO_DIR/version.txt)"
    else
        echo "Version unknown"
    fi
}

# Main
case "${1:-help}" in
    status)   show_status ;;
    start)    do_start ;;
    stop)     do_stop ;;
    restart)  do_restart ;;
    logs)     show_logs "$@" ;;
    update)   do_update ;;
    token)    do_token ;;
    version)  show_version ;;
    help|*)   show_help ;;
esac
