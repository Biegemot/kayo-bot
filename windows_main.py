#!/usr/bin/env python3
"""
Windows-specific entry point for Kayo Bot.
This script handles Windows path separators and encoding.
"""
import os
import sys

# Fix Windows path issues
if os.name == 'nt':
    # Add current directory to path
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Fix for Windows console encoding - more robust check
if hasattr(sys.stdout, 'encoding') and sys.stdout.encoding != 'utf-8':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
if hasattr(sys.stderr, 'encoding') and sys.stderr.encoding != 'utf-8':
    import io
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# Import bot.gui at TOP LEVEL for PyInstaller to detect it
from bot.gui import main as gui_main

# Import and run main
from main import main

if __name__ == '__main__':
    main()