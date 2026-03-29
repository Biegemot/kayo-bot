#!/usr/bin/env python3
"""
Windows GUI for KayoBot using blessed.
Displays bot status, chat count, and creator.
Accepts commands: start, stop, restart, update, token <TOKEN>, exit.
"""
import os
import sys
import time
import subprocess
import threading
from pathlib import Path
from blessed import Terminal

# Determine base directory (works with PyInstaller .exe)
if getattr(sys, 'frozen', False):
    BASE_DIR = Path(sys.executable).parent
else:
    BASE_DIR = Path(__file__).parent

ENV_FILE = BASE_DIR / '.env'

# Global state
bot_process = None
bot_status = "stopped"  # stopped, running, starting, stopping
chat_count = 0
creator = "Creator: SkyFox"

term = Terminal()


def format_status(status):
    """Return colored status string."""
    if status == "running":
        return term.green(status)
    elif status == "stopped":
        return term.red(status)
    elif status in ("starting", "stopping"):
        return term.yellow(status)
    else:
        return term.white(status)


def update_display():
    """Update the GUI display."""
    current_token = get_current_token()
    token_display = f"{'*' * min(len(current_token), 8)}{'...' if len(current_token) > 8 else ''}" if current_token else term.red("NOT SET")

    print(term.clear)
    print(term.bold_orange("KayoBot Windows GUI"))
    print("=" * 40)
    print(f"Status: {format_status(bot_status)}")
    print(f"Chats: {chat_count}")
    print(f"Creator: {creator}")
    print(f"Token: {token_display}")
    print("-" * 40)
    print("Commands:")
    print("  start         - Start the bot")
    print("  stop          - Stop the bot")
    print("  restart       - Restart the bot")
    print("  update        - Update the bot (pull latest)")
    print("  token <TOKEN> - Set bot token (saves to .env)")
    print("  exit          - Exit GUI")
    print("-" * 40)
    print(term.bold_orange("Enter command: "), end="", flush=True)


def start_bot():
    """Start the bot process."""
    global bot_process, bot_status
    if bot_status == "running":
        print(term.red("Bot is already running."))
        return
    bot_status = "starting"
    update_display()
    try:
        # Start main.py as a subprocess
        bot_process = subprocess.Popen([sys.executable, "main.py"],
                                       stdout=subprocess.PIPE,
                                       stderr=subprocess.PIPE,
                                       text=True)
        bot_status = "running"
        # Start a thread to read output (optional, for debugging)
        threading.Thread(target=read_output, daemon=True).start()
    except Exception as e:
        print(term.red(f"Failed to start bot: {e}"))
        bot_status = "stopped"


def stop_bot():
    """Stop the bot process."""
    global bot_process, bot_status
    if bot_status != "running":
        print(term.red("Bot is not running."))
        return
    bot_status = "stopping"
    update_display()
    if bot_process:
        bot_process.terminate()
        bot_process.wait(timeout=5)
        bot_process = None
    bot_status = "stopped"


def restart_bot():
    """Restart the bot."""
    stop_bot()
    time.sleep(1)
    start_bot()


def update_bot():
    """Update the bot by pulling latest changes."""
    print(term.yellow("Updating bot..."))
    try:
        subprocess.run(["git", "pull"], check=True)
        print(term.green("Update successful."))
    except subprocess.CalledProcessError as e:
        print(term.red(f"Update failed: {e}"))


def get_current_token():
    """Read current token from .env file."""
    if ENV_FILE.exists():
        with open(ENV_FILE, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line.startswith('TELEGRAM_BOT_TOKEN='):
                    return line.split('=', 1)[1].strip().strip('"').strip("'")
    return ""


def set_token(new_token):
    """Set the bot token and save to .env file."""
    new_token = new_token.strip().strip('"').strip("'")
    if not new_token:
        print(term.red("Token cannot be empty!"))
        return

    # Read existing .env content
    lines = []
    token_found = False
    if ENV_FILE.exists():
        with open(ENV_FILE, 'r', encoding='utf-8') as f:
            lines = f.readlines()

    # Update or add TELEGRAM_BOT_TOKEN
    new_lines = []
    for line in lines:
        if line.strip().startswith('TELEGRAM_BOT_TOKEN='):
            new_lines.append(f'TELEGRAM_BOT_TOKEN={new_token}\n')
            token_found = True
        else:
            new_lines.append(line)

    if not token_found:
        new_lines.append(f'TELEGRAM_BOT_TOKEN={new_token}\n')

    # Write back to .env
    with open(ENV_FILE, 'w', encoding='utf-8') as f:
        f.writelines(new_lines)

    print(term.green(f"Token saved to {ENV_FILE}"))
    print(term.green(f"Token length: {len(new_token)}"))


def read_output():
    """Read and print bot output (for debugging)."""
    while bot_process and bot_process.poll() is None:
        line = bot_process.stdout.readline()
        if line:
            print(term.dim(line.rstrip()))
    # Print any remaining stderr
    if bot_process:
        stderr = bot_process.stderr.read()
        if stderr:
            print(term.red(stderr))


def main():
    """Main GUI loop."""
    global bot_status, chat_count
    print(term.enter_alt_screen)
    print(term.clear)

    # Check if token is set
    current_token = get_current_token()
    if not current_token:
        print(term.bold_orange("KayoBot Windows GUI"))
        print("=" * 40)
        print(term.red("⚠️  Telegram bot token not found!"))
        print()
        print("Please enter your Telegram bot token.")
        print("You can get it from @BotFather in Telegram.")
        print()
        token_input = input("Enter token: ").strip()
        if token_input:
            set_token(token_input)
            print()
            print(term.green("Token saved! Starting GUI..."))
            time.sleep(2)
        else:
            print(term.red("No token entered. You can set it later with 'token <TOKEN>' command."))
            time.sleep(2)

    try:
        while True:
            update_display()
            # Simulate chat count updates (in real scenario, this would come from bot)
            if bot_status == "running":
                chat_count += 0  # Placeholder: actual chat count would be retrieved from bot state
            # Non-blocking input with timeout
            if term.inkey(timeout=0.5):
                key = term.inkey()
                if key.name == "KEY_ENTER":
                    # Get the command from input buffer (simplified)
                    # In a real app, we'd use a proper input loop
                    pass
                else:
                    # Build command string
                    cmd = ""
                    while True:
                        k = term.inkey(timeout=0.1)
                        if not k:
                            break
                        if k.name == "KEY_ENTER":
                            break
                        elif k.name == "KEY_BACKSPACE":
                            cmd = cmd[:-1]
                        else:
                            cmd += k
                    # Process command
                    parts = cmd.strip().split()
                    if not parts:
                        continue
                    command = parts[0].lower()
                    if command == "start":
                        start_bot()
                    elif command == "stop":
                        stop_bot()
                    elif command == "restart":
                        restart_bot()
                    elif command == "update":
                        update_bot()
                    elif command == "token" and len(parts) > 1:
                        set_token(" ".join(parts[1:]))
                    elif command == "exit":
                        break
                    else:
                        print(term.red(f"Unknown command: {command}"))
                        time.sleep(1)
            # Update chat count periodically (simulated)
            time.sleep(0.1)
    finally:
        # Cleanup
        if bot_process:
            stop_bot()
        print(term.normal_screen)
        print(term.exit_alt_screen)


if __name__ == "__main__":
    main()