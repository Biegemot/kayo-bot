"""Version management for Kayo Bot."""


def get_current_version():
    """Get the current version from version.txt or VERSION constant."""
    import sys
    from pathlib import Path

    # Try multiple locations for version.txt
    search_paths = []

    if getattr(sys, 'frozen', False):
        # PyInstaller: look next to the .exe
        search_paths.append(Path(sys.executable).parent / 'version.txt')
    else:
        # Development: look next to this file, then project root
        search_paths.append(Path(__file__).parent / 'version.txt')
        search_paths.append(Path(__file__).parent.parent / 'version.txt')

    for path in search_paths:
        if path.exists():
            try:
                return path.read_text(encoding='utf-8').strip()
            except Exception:
                continue

    return "dev"
