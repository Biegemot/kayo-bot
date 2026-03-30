import os
import sys
from pathlib import Path
from bot.services.activity import ActivityManager

# Determine base directory (works with PyInstaller .exe)
if getattr(sys, 'frozen', False):
    BASE_DIR = Path(sys.executable).parent
else:
    # bot/services/db_manager.py -> parent=services -> parent=bot -> parent=project root
    BASE_DIR = Path(__file__).parent.parent.parent


class DBManager:
    def __init__(self, base_dir=None):
        """Initialize the DB manager with a base directory for chat databases."""
        if base_dir is None:
            base_dir = str(BASE_DIR / 'bot' / 'data')
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