#!/usr/bin/env python3
"""
Windows compatibility utilities for Kayo Bot.
This module provides Windows-specific fixes and improvements.
"""

import os
import sys
import platform
import subprocess
import ctypes
from pathlib import Path, PureWindowsPath, PurePosixPath

def is_windows() -> bool:
    """Check if running on Windows."""
    return os.name == 'nt'

def is_linux() -> bool:
    """Check if running on Linux."""
    return os.name == 'posix' and platform.system() == 'Linux'

def fix_windows_paths():
    """
    Fix common Windows path issues.
    - Convert forward slashes to backslashes where needed
    - Handle Windows drive letters
    - Fix path encoding issues
    """
    if not is_windows():
        return
    
    # Fix sys.path for Windows
    current_dir = os.path.dirname(os.path.abspath(__file__))
    if current_dir not in sys.path:
        sys.path.insert(0, current_dir)
    
    # Fix for relative imports
    project_root = Path(__file__).parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

def fix_windows_encoding():
    """
    Fix Windows console encoding issues.
    Windows console often uses cp1251 instead of UTF-8.
    """
    if not is_windows():
        return
    
    try:
        # Try to set UTF-8 encoding for Windows console
        if sys.stdout.encoding != 'utf-8':
            import io
            sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
            sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')
    except:
        pass  # Silently fail if we can't fix encoding

def setup_windows_environment():
    """
    Setup Windows-specific environment variables and settings.
    """
    if not is_windows():
        return
    
    # Set environment variables for Windows
    os.environ['PYTHONIOENCODING'] = 'utf-8'
    os.environ['PYTHONUTF8'] = '1'
    
    # Add Windows-specific paths
    appdata = os.getenv('APPDATA')
    if appdata:
        config_dir = Path(appdata) / 'kayo-bot'
        config_dir.mkdir(exist_ok=True)
        os.environ['KAYO_CONFIG_DIR'] = str(config_dir)

def get_windows_special_paths():
    """
    Get Windows special folder paths.
    Returns dict with paths to common Windows directories.
    """
    if not is_windows():
        return {}
    
    paths = {}
    
    # Get common Windows folders
    try:
        import winreg
        
        # Desktop
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, 
                            r"Software\Microsoft\Windows\CurrentVersion\Explorer\User Shell Folders")
        desktop, _ = winreg.QueryValueEx(key, "Desktop")
        paths['desktop'] = desktop
        
        # Documents
        documents, _ = winreg.QueryValueEx(key, "Personal")
        paths['documents'] = documents
        
        winreg.CloseKey(key)
    except:
        # Fallback to environment variables
        paths['desktop'] = os.path.join(os.path.expanduser('~'), 'Desktop')
        paths['documents'] = os.path.join(os.path.expanduser('~'), 'Documents')
    
    # AppData
    paths['appdata'] = os.getenv('APPDATA', '')
    paths['localappdata'] = os.getenv('LOCALAPPDATA', '')
    
    return paths

def create_windows_shortcut(target_path: str, shortcut_path: str, 
                           description: str = "Kayo Bot", 
                           icon_path: str = None):
    """
    Create a Windows shortcut (.lnk file).
    Requires pywin32 or comtypes.
    """
    if not is_windows():
        return False
    
    try:
        import win32com.client
        shell = win32com.client.Dispatch("WScript.Shell")
        shortcut = shell.CreateShortCut(shortcut_path)
        shortcut.Targetpath = target_path
        shortcut.WorkingDirectory = os.path.dirname(target_path)
        shortcut.Description = description
        if icon_path:
            shortcut.IconLocation = icon_path
        shortcut.save()
        return True
    except ImportError:
        # Try comtypes as fallback
        try:
            import comtypes.client
            shell = comtypes.client.CreateObject("WScript.Shell")
            shortcut = shell.CreateShortcut(shortcut_path)
            shortcut.TargetPath = target_path
            shortcut.WorkingDirectory = os.path.dirname(target_path)
            shortcut.Description = description
            if icon_path:
                shortcut.IconLocation = icon_path
            shortcut.Save()
            return True
        except:
            pass
    
    return False

def is_admin_windows():
    """
    Check if running with administrator privileges on Windows.
    """
    if not is_windows():
        return False
    
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def run_as_admin_windows():
    """
    Restart the script with administrator privileges.
    Only works on Windows.
    """
    if not is_windows():
        return False
    
    if is_admin_windows():
        return True
    
    try:
        # Re-run with admin privileges
        script = sys.argv[0]
        params = ' '.join([f'"{x}"' for x in sys.argv[1:]])
        
        ctypes.windll.shell32.ShellExecuteW(
            None, "runas", sys.executable, f'"{script}" {params}', None, 1
        )
        sys.exit(0)
    except:
        pass
    
    return False

def fix_windows_file_permissions(path: str):
    """
    Fix file permissions on Windows.
    Ensures files are readable/writable.
    """
    if not is_windows():
        return
    
    try:
        import stat
        os.chmod(path, stat.S_IRUSR | stat.S_IWUSR | stat.S_IRGRP | stat.S_IROTH)
    except:
        pass

def get_windows_version():
    """
    Get Windows version information.
    Returns tuple of (major, minor, build).
    """
    if not is_windows():
        return (0, 0, 0)
    
    try:
        ver = platform.win32_ver()
        if len(ver) >= 2:
            version_str = ver[1]
            parts = version_str.split('.')
            if len(parts) >= 3:
                return tuple(int(p) for p in parts[:3])
    except:
        pass
    
    return (0, 0, 0)

def is_windows_10_or_later():
    """
    Check if running Windows 10 or later.
    """
    if not is_windows():
        return False
    
    major, _, _ = get_windows_version()
    return major >= 10

def setup_windows_console():
    """
    Setup Windows console for better UTF-8 support.
    """
    if not is_windows():
        return
    
    try:
        # Enable virtual terminal processing for Windows 10+
        if is_windows_10_or_later():
            import ctypes
            kernel32 = ctypes.windll.kernel32
            STD_OUTPUT_HANDLE = -11
            
            h_out = kernel32.GetStdHandle(STD_OUTPUT_HANDLE)
            mode = ctypes.c_ulong()
            kernel32.GetConsoleMode(h_out, ctypes.byref(mode))
            mode.value |= 0x0004  # ENABLE_VIRTUAL_TERMINAL_PROCESSING
            kernel32.SetConsoleMode(h_out, mode)
    except:
        pass

def normalize_path(path: str) -> str:
    """
    Normalize path for current OS.
    Converts path separators appropriately.
    """
    if is_windows():
        return str(PureWindowsPath(path))
    else:
        return str(PurePosixPath(path))

def get_platform_specific_config():
    """
    Get platform-specific configuration.
    Returns dict with platform-specific settings.
    """
    config = {
        'is_windows': is_windows(),
        'is_linux': is_linux(),
        'platform': platform.system(),
        'version': platform.version(),
        'python_version': platform.python_version(),
    }
    
    if is_windows():
        config.update({
            'windows_version': get_windows_version(),
            'windows_10_or_later': is_windows_10_or_later(),
            'is_admin': is_admin_windows(),
            'special_paths': get_windows_special_paths(),
        })
    
    return config

def initialize_windows_compatibility():
    """
    Initialize all Windows compatibility fixes.
    Call this at the start of the application on Windows.
    """
    if is_windows():
        print("🐰 Initializing Windows compatibility layer...")
        fix_windows_paths()
        fix_windows_encoding()
        setup_windows_environment()
        setup_windows_console()
        
        # Print platform info
        config = get_platform_specific_config()
        print(f"   Platform: {config['platform']} {config['version']}")
        print(f"   Python: {config['python_version']}")
        
        if config['is_windows']:
            print(f"   Windows: {config['windows_version']}")
            if config['is_admin']:
                print("   ⚠️  Running as administrator")
        
        print("   ✅ Windows compatibility initialized")
        return True
    
    return False

if __name__ == '__main__':
    # Test the compatibility functions
    print("Testing Windows compatibility utilities...")
    
    if is_windows():
        print("Running on Windows")
        initialize_windows_compatibility()
        
        # Test path normalization
        test_path = "bot/data/chat_123.db"
        normalized = normalize_path(test_path)
        print(f"Normalized path: {normalized}")
        
        # Test platform config
        config = get_platform_specific_config()
        print(f"Platform config: {config}")
    else:
        print(f"Running on {platform.system()}")
        config = get_platform_specific_config()
        print(f"Platform config: {config}")