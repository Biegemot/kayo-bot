import os
import sys
from pathlib import Path
from bot.services.activity import ActivityManager


class DBManager:
    def __init__(self, base_dir=None):
        """Initialize the DB manager with a base directory for chat databases."""
        if base_dir is None:
            # Determine base directory dynamically (works with PyInstaller .exe)
            if getattr(sys, 'frozen', False):
                # When running from PyInstaller, use the executable's directory
                base_dir = str(Path(sys.executable).parent / 'bot' / 'data')
            else:
                # For development, use the project's bot/data directory
                # bot/services/db_manager.py -> parent=services -> parent=bot -> parent=project root
                base_dir = str(Path(__file__).parent.parent.parent / 'bot' / 'data')
            
            # If the candidate directory is not writable, use a user directory
            try:
                os.makedirs(base_dir, exist_ok=True)
                # Test write permission
                test_file = Path(base_dir) / '.write_test'
                test_file.touch()
                test_file.unlink()
            except (OSError, PermissionError):
                # Fallback to user's home directory
                base_dir = str(Path.home() / '.kayo-bot' / 'data')
        
        self.base_dir = base_dir
        # Ensure the base directory exists
        os.makedirs(self.base_dir, exist_ok=True)
        # Cache for activity managers per chat_id to avoid reopening connections excessively
        self._managers = {}

    def get_activity_manager(self, chat_id):
        """Get an ActivityManager instance for the given chat_id.
        If not cached, create a new one pointing to the chat-specific database."""
        if chat_id not in self._managers:
            db_path = os.path.join(self.base_dir, f'chat_{chat_id}.db')
            self._managers[chat_id] = ActivityManager(db_path=db_path)
        return self._managers[chat_id]

    # Optional: cleanup method to close connections (if needed)
    def close_all(self):
        """Close all database connections."""
        for manager in self._managers.values():
            if hasattr(manager, 'conn') and manager.conn:
                manager.conn.close()
        self._managers.clear()