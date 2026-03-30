#!/usr/bin/env python3
"""
KayoBot Windows GUI — terminal interface for managing the bot.
Provides token setup, bot start/stop, and log viewing.
Uses standard input/output (works reliably on Windows).
"""
import os
import sys
import time
import subprocess
import threading
from pathlib import Path
from datetime import datetime

# Determine base directory (works with PyInstaller .exe)
if getattr(sys, 'frozen', False):
    BASE_DIR = Path(sys.executable).parent
else:
    # bot/gui.py -> parent = bot/ -> parent = project root
    BASE_DIR = Path(__file__).parent.parent

ENV_FILE = BASE_DIR / '.env'
LOG_FILE = BASE_DIR / 'bot.log'

# ANSI colors for terminal
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BOLD = '\033[1m'
    DIM = '\033[2m'
    END = '\033[0m'
    ORANGE = '\033[38;5;208m'

# Global state
bot_process = None
bot_status = "stopped"
log_lines = []
MAX_LOG_LINES = 20


def clear_screen():
    """Clear terminal screen (cross-platform)."""
    os.system('cls' if os.name == 'nt' else 'clear')


def colored(text, color):
    """Return colored text."""
    return f"{color}{text}{Colors.END}"


def get_current_token():
    """Read current token from .env file."""
    if ENV_FILE.exists():
        try:
            with open(ENV_FILE, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line.startswith('TELEGRAM_BOT_TOKEN='):
                        return line.split('=', 1)[1].strip().strip('"').strip("'")
        except Exception:
            pass
    return ""


def save_token(new_token):
    """Save token to .env file."""
    new_token = new_token.strip().strip('"').strip("'")
    if not new_token:
        return False

    lines = []
    token_found = False
    if ENV_FILE.exists():
        try:
            with open(ENV_FILE, 'r', encoding='utf-8') as f:
                lines = f.readlines()
        except Exception:
            pass

    new_lines = []
    for line in lines:
        if line.strip().startswith('TELEGRAM_BOT_TOKEN='):
            new_lines.append(f'TELEGRAM_BOT_TOKEN={new_token}\n')
            token_found = True
        else:
            new_lines.append(line)

    if not token_found:
        new_lines.append(f'TELEGRAM_BOT_TOKEN={new_token}\n')

    try:
        with open(ENV_FILE, 'w', encoding='utf-8') as f:
            f.writelines(new_lines)
        return True
    except Exception as e:
        print(colored(f"Error saving token: {e}", Colors.RED))
        return False


def mask_token(token):
    """Return masked token for display."""
    if not token:
        return colored("NOT SET", Colors.RED)
    if len(token) <= 8:
        return colored("****", Colors.GREEN)
    return colored(f"{token[:4]}...{token[-4:]}", Colors.GREEN)


def status_color(status):
    """Return colored status string."""
    colors = {
        "running": Colors.GREEN,
        "stopped": Colors.RED,
        "starting": Colors.YELLOW,
        "stopping": Colors.YELLOW,
    }
    return colored(status, colors.get(status, Colors.WHITE))


def add_log(message):
    """Add a timestamped log line."""
    timestamp = datetime.now().strftime("%H:%M:%S")
    log_lines.append(f"[{timestamp}] {message}")
    if len(log_lines) > MAX_LOG_LINES:
        log_lines.pop(0)


def read_bot_output(proc):
    """Read bot output in background thread."""
    global bot_status
    while proc and proc.poll() is None:
        try:
            line = proc.stdout.readline()
            if line:
                line = line.rstrip()
                if line:
                    add_log(line)
        except Exception:
            break
    # Process ended
    if proc:
        try:
            stderr = proc.stderr.read()
            if stderr:
                for err_line in stderr.strip().split('\n'):
                    if err_line.strip():
                        add_log(colored(f"ERR: {err_line.strip()}", Colors.RED))
        except Exception:
            pass
    bot_status = "stopped"


def start_bot():
    """Start the bot process."""
    global bot_process, bot_status

    if bot_status == "running":
        add_log(colored("Bot is already running!", Colors.YELLOW))
        return

    token = get_current_token()
    if not token:
        add_log(colored("Cannot start: token not set! Use 'token' command.", Colors.RED))
        return

    bot_status = "starting"
    add_log("Starting bot...")

    try:
        if getattr(sys, 'frozen', False):
            # PyInstaller .exe: run self with --run-bot argument
            bot_process = subprocess.Popen(
                [sys.executable, "--run-bot"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
                cwd=str(BASE_DIR)
            )
        else:
            # Development: run main.py directly
            bot_process = subprocess.Popen(
                [sys.executable, str(BASE_DIR / "main.py")],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
                cwd=str(BASE_DIR)
            )
        bot_status = "running"
        add_log(colored("Bot started successfully!", Colors.GREEN))
        threading.Thread(target=read_bot_output, args=(bot_process,), daemon=True).start()
    except Exception as e:
        add_log(colored(f"Failed to start bot: {e}", Colors.RED))
        bot_status = "stopped"


def stop_bot():
    """Stop the bot process."""
    global bot_process, bot_status

    if bot_status != "running":
        add_log(colored("Bot is not running.", Colors.YELLOW))
        return

    bot_status = "stopping"
    add_log("Stopping bot...")

    if bot_process:
        try:
            bot_process.terminate()
            bot_process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            bot_process.kill()
            bot_process.wait(timeout=2)
        except Exception as e:
            add_log(colored(f"Error stopping bot: {e}", Colors.RED))
        finally:
            bot_process = None

    bot_status = "stopped"
    add_log(colored("Bot stopped.", Colors.YELLOW))


def restart_bot():
    """Restart the bot."""
    stop_bot()
    time.sleep(1)
    start_bot()


def show_token_prompt():
    """Show interactive token setup prompt."""
    clear_screen()
    print(colored("=" * 50, Colors.ORANGE))
    print(colored("  🐰 KayoBot — First Time Setup", Colors.ORANGE + Colors.BOLD))
    print(colored("=" * 50, Colors.ORANGE))
    print()
    current = get_current_token()
    if current:
        print(f"  Current token: {mask_token(current)}")
        print()
        change = input("  Change token? (y/N): ").strip().lower()
        if change != 'y':
            return
        print()

    print(colored("  Enter your Telegram bot token.", Colors.CYAN))
    print(colored("  Get it from @BotFather in Telegram.", Colors.DIM))
    print()
    token = input("  Token: ").strip()

    if not token:
        print(colored("  No token entered. Skipping.", Colors.YELLOW))
        time.sleep(1)
        return

    if save_token(token):
        print(colored("  ✅ Token saved!", Colors.GREEN))
    else:
        print(colored("  ❌ Failed to save token!", Colors.RED))
    time.sleep(1)


def show_menu():
    """Display the main menu and process commands."""
    global bot_status

    clear_screen()
    token = get_current_token()

    print(colored("=" * 50, Colors.ORANGE))
    print(colored("  🐰 KayoBot Windows GUI", Colors.ORANGE + Colors.BOLD))
    print(colored(f"  Creator: SkyFox", Colors.DIM))
    print(colored("=" * 50, Colors.ORANGE))
    print()
    print(f"  Status: {status_color(bot_status)}")
    print(f"  Token:  {mask_token(token)}")
    print(f"  Config: {ENV_FILE}")
    print()
    print(colored("  Commands:", Colors.BOLD))
    print("    [1] Start bot")
    print("    [2] Stop bot")
    print("    [3] Restart bot")
    print("    [4] Set/change token")
    print("    [5] View logs")
    print("    [0] Exit")
    print()

    if log_lines:
        print(colored("  Recent logs:", Colors.DIM))
        for line in log_lines[-5:]:
            print(f"    {line}")
        print()


def view_logs():
    """Show full log viewer."""
    clear_screen()
    print(colored("=" * 50, Colors.ORANGE))
    print(colored("  📋 Bot Logs", Colors.ORANGE + Colors.BOLD))
    print(colored("=" * 50, Colors.ORANGE))
    print()

    if not log_lines:
        print(colored("  No logs yet. Start the bot first.", Colors.DIM))
    else:
        for line in log_lines:
            print(f"  {line}")

    print()
    input(colored("  Press Enter to return...", Colors.DIM))


def main():
    """Main GUI loop."""
    # Check for token on first launch
    token = get_current_token()
    if not token:
        show_token_prompt()

    try:
        while True:
            show_menu()
            choice = input(colored("  Enter choice: ", Colors.BOLD)).strip()

            if choice == '1':
                start_bot()
                time.sleep(1)
            elif choice == '2':
                stop_bot()
                time.sleep(1)
            elif choice == '3':
                restart_bot()
                time.sleep(1)
            elif choice == '4':
                show_token_prompt()
            elif choice == '5':
                view_logs()
            elif choice == '0' or choice.lower() == 'exit':
                if bot_status == "running":
                    print(colored("\n  Stopping bot before exit...", Colors.YELLOW))
                    stop_bot()
                print(colored("  Goodbye! 🐰", Colors.ORANGE))
                break
            else:
                add_log(colored(f"Unknown command: {choice}", Colors.RED))
                time.sleep(0.5)

    except KeyboardInterrupt:
        if bot_status == "running":
            print(colored("\n  Stopping bot...", Colors.YELLOW))
            stop_bot()
        print(colored("\n  Goodbye! 🐰", Colors.ORANGE))
    finally:
        pass


if __name__ == "__main__":
    main()

