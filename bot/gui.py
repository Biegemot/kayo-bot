#!/usr/bin/env python3
"""
KayoBot Windows GUI — Terminal interface for managing the bot.
Provides token setup, bot start/stop, log viewing, and system monitoring.
Enhanced with Windows compatibility and improved UX.

Usage:
    python bot/gui.py          # Interactive menu mode
    python bot/gui.py --run    # Run bot directly (for PyInstaller)
"""
import os
import sys
import time
import subprocess
import threading
import psutil
from pathlib import Path
from datetime import datetime, timedelta

# Determine base directory (works with PyInstaller .exe)
if getattr(sys, 'frozen', False):
    BASE_DIR = Path(sys.executable).parent
else:
    # bot/gui.py -> parent = bot/ -> parent = project root
    BASE_DIR = Path(__file__).parent.parent

ENV_FILE = BASE_DIR / '.env'
LOG_FILE = BASE_DIR / 'bot.log'
VERSION_FILE = BASE_DIR / 'version.txt'

# Import Windows compatibility
try:
    from bot.windows_compat import (
        is_windows, fix_windows_encoding, setup_windows_console,
        initialize_windows_compatibility, get_platform_specific_config
    )
except ImportError:
    # Fallback for non-Windows or missing module
    def is_windows():
        return os.name == 'nt'

    def fix_windows_encoding():
        pass

    def setup_windows_console():
        pass

    def initialize_windows_compatibility():
        pass

    def get_platform_specific_config():
        return {'platform': 'unknown'}

# ANSI colors for terminal
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    WHITE = '\033[97m'
    BOLD = '\033[1m'
    DIM = '\033[2m'
    END = '\033[0m'
    ORANGE = '\033[38;5;208m'
    PURPLE = '\033[38;5;129m'


# Global state
bot_process = None
bot_status = "stopped"
log_lines = []
MAX_LOG_LINES = 50
start_time = None


def clear_screen():
    """Clear terminal screen (cross-platform)."""
    os.system('cls' if os.name == 'nt' else 'clear')


def colored(text, color):
    """Return colored text."""
    return f"{color}{text}{Colors.END}"


def get_version():
    """Read current version from version.txt."""
    if VERSION_FILE.exists():
        try:
            with open(VERSION_FILE, 'r', encoding='utf-8') as f:
                return f.read().strip()
        except Exception:
            pass
    return "unknown"


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


def get_uptime():
    """Get bot uptime as formatted string."""
    global start_time
    if start_time is None:
        return colored("N/A", Colors.DIM)

    delta = datetime.now() - start_time
    hours, remainder = divmod(int(delta.total_seconds()), 3600)
    minutes, seconds = divmod(remainder, 60)

    if hours > 0:
        return colored(f"{hours}h {minutes}m {seconds}s", Colors.GREEN)
    elif minutes > 0:
        return colored(f"{minutes}m {seconds}s", Colors.GREEN)
    else:
        return colored(f"{seconds}s", Colors.GREEN)


def get_system_info():
    """Get system resource information."""
    try:
        cpu = psutil.cpu_percent(interval=0.1)
        mem = psutil.virtual_memory()
        mem_percent = mem.percent
        mem_used = mem.used / (1024 * 1024)
        mem_total = mem.total / (1024 * 1024)

        cpu_color = Colors.GREEN if cpu < 50 else (Colors.YELLOW if cpu < 80 else Colors.RED)
        mem_color = Colors.GREEN if mem_percent < 50 else (Colors.YELLOW if mem_percent < 80 else Colors.RED)

        return {
            'cpu': colored(f"{cpu:.1f}%", cpu_color),
            'mem': colored(f"{mem_percent:.1f}% ({mem_used:.0f}/{mem_total:.0f} MB)", mem_color),
            'disk': colored(f"{psutil.disk_usage(str(BASE_DIR)).percent:.1f}%", Colors.GREEN)
        }
    except Exception:
        return {
            'cpu': colored("N/A", Colors.DIM),
            'mem': colored("N/A", Colors.DIM),
            'disk': colored("N/A", Colors.DIM)
        }


def add_log(message):
    """Add a timestamped log line."""
    timestamp = datetime.now().strftime("%H:%M:%S")
    log_lines.append(f"[{timestamp}] {message}")
    if len(log_lines) > MAX_LOG_LINES:
        log_lines.pop(0)


def read_bot_output(proc):
    """Read bot output in background thread."""
    global bot_status
    # Read combined stdout/stderr
    while proc and proc.poll() is None:
        try:
            line = proc.stdout.readline()
            if line:
                line = line.rstrip()
                if line:
                    # Check if line contains error indicators
                    if ' - ERROR - ' in line or ' - CRITICAL - ' in line or 'Traceback' in line or 'PYI-' in line:
                        add_log(colored(f"ERR: {line}", Colors.RED))
                    else:
                        add_log(line)
        except Exception:
            break
    # Read remaining output on exit
    if proc:
        try:
            remaining = proc.stdout.read()
            if remaining:
                for line in remaining.strip().split('\n'):
                    line = line.strip()
                    if not line:
                        continue
                    # Check if line contains error indicators
                    if ' - ERROR - ' in line or ' - CRITICAL - ' in line or 'Traceback' in line or 'PYI-' in line:
                        add_log(colored(f"ERR: {line}", Colors.RED))
                    else:
                        add_log(line)
        except Exception:
            pass
    bot_status = "stopped"


def start_bot():
    """Start the bot process."""
    global bot_process, bot_status, start_time

    if bot_status == "running":
        add_log(colored("Bot is already running!", Colors.YELLOW))
        return

    token = get_current_token()
    if not token:
        add_log(colored("Cannot start: token not set! Use 'token' command.", Colors.RED))
        return

    bot_status = "starting"
    start_time = None
    add_log("Starting bot...")

    try:
        if getattr(sys, 'frozen', False):
            # PyInstaller .exe: run self with --run-bot argument
            bot_process = subprocess.Popen(
                [sys.executable, "--run-bot"],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                cwd=str(BASE_DIR)
            )
        else:
            # Development: run main.py directly
            bot_process = subprocess.Popen(
                [sys.executable, str(BASE_DIR / "main.py")],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                cwd=str(BASE_DIR)
            )
        bot_status = "running"
        start_time = datetime.now()
        add_log(colored("Bot started successfully!", Colors.GREEN))
        threading.Thread(target=read_bot_output, args=(bot_process,), daemon=True).start()
    except Exception as e:
        add_log(colored(f"Failed to start bot: {e}", Colors.RED))
        bot_status = "stopped"
        start_time = None


def stop_bot():
    """Stop the bot process."""
    global bot_process, bot_status, start_time

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
            start_time = None

    bot_status = "stopped"
    add_log(colored("Bot stopped.", Colors.YELLOW))


def restart_bot():
    """Restart the bot."""
    stop_bot()
    time.sleep(1)
    start_bot()


def check_for_updates():
    """Check for updates and apply if available."""
    add_log("Checking for updates...")
    try:
        from bot.services.auto_update import (
            check_and_apply_update, get_current_version,
            get_latest_release_info, restart_application
        )

        current = get_current_version()
        add_log(f"Current version: v{current}")

        # Check what GitHub has
        latest_tag, assets = get_latest_release_info()
        if latest_tag:
            add_log(f"Latest release: v{latest_tag}")
        else:
            add_log(colored("Cannot reach GitHub API. Check internet/proxy.", Colors.RED))
            return

        updated, msg = check_and_apply_update(force=True)
        add_log(msg)

        if updated:
            add_log(colored("Restarting with new version...", Colors.GREEN))
            time.sleep(1)
            stop_bot()
            restart_application()

    except Exception as e:
        add_log(colored(f"Update failed: {type(e).__name__}: {e}", Colors.RED))


def show_token_prompt():
    """Show interactive token setup prompt."""
    clear_screen()
    print(colored("=" * 60, Colors.ORANGE))
    print(colored("  🐰 KayoBot — Token Setup", Colors.ORANGE + Colors.BOLD))
    print(colored("=" * 60, Colors.ORANGE))
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


def show_system_info():
    """Show detailed system information."""
    clear_screen()
    print(colored("=" * 60, Colors.CYAN))
    print(colored("  📊 System Information", Colors.CYAN + Colors.BOLD))
    print(colored("=" * 60, Colors.CYAN))
    print()

    config = get_platform_specific_config()

    print(f"  Platform:     {colored(config.get('platform', 'Unknown'), Colors.GREEN)}")
    print(f"  Python:       {colored(sys.version.split()[0], Colors.GREEN)}")
    print(f"  Version:      {colored(get_version(), Colors.GREEN)}")
    print(f"  Working Dir:  {colored(str(BASE_DIR), Colors.DIM)}")
    print(f"  Config File:  {colored(str(ENV_FILE), Colors.DIM)}")
    print()

    sys_info = get_system_info()
    print(f"  CPU Usage:    {sys_info['cpu']}")
    print(f"  Memory:       {sys_info['mem']}")
    print(f"  Disk:         {sys_info['disk']}")
    print()

    if is_windows():
        print(colored("  [Windows Mode]", Colors.YELLOW))
    else:
        print(colored("  [Unix/Linux Mode]", Colors.GREEN))

    print()
    input(colored("  Press Enter to return...", Colors.DIM))


def view_logs():
    """Show full log viewer."""
    clear_screen()
    print(colored("=" * 60, Colors.ORANGE))
    print(colored("  📋 Bot Logs", Colors.ORANGE + Colors.BOLD))
    print(colored("=" * 60, Colors.ORANGE))
    print()

    if not log_lines:
        print(colored("  No logs yet. Start the bot first.", Colors.DIM))
    else:
        # Show last 30 lines
        display_lines = log_lines[-30:]
        for i, line in enumerate(display_lines, 1):
            line_num = colored(f"{i:2d}.", Colors.DIM)
            print(f"  {line_num} {line}")

    print()
    print(colored(f"  Total: {len(log_lines)} lines | Showing last 30", Colors.DIM))
    print()
    input(colored("  Press Enter to return...", Colors.DIM))


def show_menu():
    """Display the main menu and process commands."""
    global bot_status

    clear_screen()
    token = get_current_token()
    version = get_version()
    sys_info = get_system_info()

    # Header
    print(colored("╔" + "═" * 58 + "╗", Colors.ORANGE))
    print(colored("║", Colors.ORANGE) + colored("  🐰 KayoBot Windows GUI", Colors.ORANGE + Colors.BOLD).center(58) + colored("║", Colors.ORANGE))
    print(colored("║", Colors.ORANGE) + colored(f"  Creator: SkyFox | v{version}", Colors.DIM).center(58) + colored("║", Colors.ORANGE))
    print(colored("╚" + "═" * 58 + "╝", Colors.ORANGE))
    print()

    # Status panel
    print(colored("  ┌─── Status ───────────────────────────────────┐", Colors.DIM))
    print(colored("  │", Colors.DIM) + f"  Bot:    {status_color(bot_status)}".ljust(49) + colored("│", Colors.DIM))
    print(colored("  │", Colors.DIM) + f"  Token:  {mask_token(token)}".ljust(49) + colored("│", Colors.DIM))
    print(colored("  │", Colors.DIM) + f"  Uptime: {get_uptime()}".ljust(49) + colored("│", Colors.DIM))
    print(colored("  └──────────────────────────────────────────────┘", Colors.DIM))
    print()

    # System info
    print(colored("  ┌─── System ───────────────────────────────────┐", Colors.DIM))
    print(colored("  │", Colors.DIM) + f"  CPU:    {sys_info['cpu']}".ljust(49) + colored("│", Colors.DIM))
    print(colored("  │", Colors.DIM) + f"  Memory: {sys_info['mem']}".ljust(49) + colored("│", Colors.DIM))
    print(colored("  └──────────────────────────────────────────────┘", Colors.DIM))
    print()

    # Commands
    print(colored("  Commands:", Colors.BOLD))
    print("    [1] Start bot")
    print("    [2] Stop bot")
    print("    [3] Restart bot")
    print("    [4] Set/change token")
    print("    [5] Check for updates")
    print("    [6] View logs")
    print("    [7] System info")
    print("    [0] Exit")
    print()

    # Recent logs
    if log_lines:
        print(colored("  ─── Recent Logs ─────────────────────────────", Colors.DIM))
        for line in log_lines[-3:]:
            print(colored(f"    {line}", Colors.DIM))
        print()


def main():
    """Main GUI loop."""
    # Initialize Windows compatibility
    if is_windows():
        fix_windows_encoding()
        setup_windows_console()

    # Check for --run-bot argument (for PyInstaller)
    if len(sys.argv) > 1 and sys.argv[1] == '--run-bot':
        # Run bot directly
        add_log("Running bot in direct mode...")
        try:
            from main import main as bot_main
            bot_main()
        except Exception as e:
            add_log(colored(f"Bot error: {e}", Colors.RED))
            sys.exit(1)
        return

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
                check_for_updates()
                time.sleep(2)
            elif choice == '6':
                view_logs()
            elif choice == '7':
                show_system_info()
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


def run_bot():
    """Run bot directly (for PyInstaller --run-bot mode)."""
    try:
        from main import main as bot_main
        bot_main()
    except Exception as e:
        print(f"Bot error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
