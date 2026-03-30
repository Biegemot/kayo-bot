"""Profile manager for user fursona profiles."""
import sqlite3
import os
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class ProfileManager:
    def __init__(self, db_path):
        """Initialize the profile database connection."""
        self.db_path = db_path
        os.makedirs(os.path.dirname(os.path.abspath(db_path)), exist_ok=True)
        self.ensure_connection()
        self.create_table()
        self.migrate_schema()

    def ensure_connection(self):
        """Ensure we have a valid database connection."""
        if not hasattr(self, 'conn') or self.conn is None:
            self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
            self.conn.row_factory = sqlite3.Row

    def create_table(self):
        """Create the profiles table if it doesn't exist."""
        try:
            self.ensure_connection()
            cursor = self.conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS profiles (
                    user_id INTEGER PRIMARY KEY,
                    fursona_name TEXT,
                    species TEXT,
                    birth_date TEXT,
                    age INTEGER,
                    orientation TEXT,
                    city TEXT,
                    looking_for TEXT,
                    personality_type TEXT,
                    reference_photo TEXT,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            self.conn.commit()
        except Exception as e:
            logger.error(f"Error creating profiles table: {e}")

    def migrate_schema(self):
        """Migrate existing database schema to add new columns if they don't exist."""
        try:
            self.ensure_connection()
            cursor = self.conn.cursor()
            
            # Get current columns
            cursor.execute("PRAGMA table_info(profiles)")
            columns = [column[1] for column in cursor.fetchall()]
            
            # Add missing columns
            new_columns = [
                ('looking_for', 'TEXT'),
                ('personality_type', 'TEXT'),
            ]
            
            for col_name, col_type in new_columns:
                if col_name not in columns:
                    cursor.execute(f'ALTER TABLE profiles ADD COLUMN {col_name} {col_type}')
                    logger.info(f"Added {col_name} column to profiles table")
            
            self.conn.commit()
        except Exception as e:
            logger.error(f"Error migrating profiles schema: {e}")

    def get_profile(self, user_id):
        """Get profile for a user."""
        try:
            self.ensure_connection()
            cursor = self.conn.cursor()
            cursor.execute('SELECT * FROM profiles WHERE user_id = ?', (user_id,))
            row = cursor.fetchone()
            if row:
                return dict(row)
            return None
        except Exception as e:
            logger.error(f"Error getting profile for user {user_id}: {e}")
            return None

    def update_profile_field(self, user_id, field, value):
        """Update a specific field in user's profile."""
        try:
            self.ensure_connection()
            cursor = self.conn.cursor()
            
            # Check if profile exists
            cursor.execute('SELECT user_id FROM profiles WHERE user_id = ?', (user_id,))
            exists = cursor.fetchone()
            
            if exists:
                # Update existing profile
                cursor.execute(
                    f'UPDATE profiles SET {field} = ?, updated_at = ? WHERE user_id = ?',
                    (value, datetime.now().isoformat(), user_id)
                )
            else:
                # Create new profile
                cursor.execute(
                    f'INSERT INTO profiles (user_id, {field}, updated_at) VALUES (?, ?, ?)',
                    (user_id, value, datetime.now().isoformat())
                )
            
            self.conn.commit()
            return True
        except Exception as e:
            logger.error(f"Error updating profile field for user {user_id}: {e}")
            return False

    def get_all_profiles(self):
        """Get all profiles."""
        try:
            self.ensure_connection()
            cursor = self.conn.cursor()
            cursor.execute('SELECT * FROM profiles')
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"Error getting all profiles: {e}")
            return []

    def get_profile_summary(self, user_id):
        """Get profile summary for display."""
        profile = self.get_profile(user_id)
        if not profile:
            return None
        
        return {
            'fursona_name': profile.get('fursona_name', 'Не указано'),
            'species': profile.get('species', 'Не указано'),
            'birth_date': profile.get('birth_date', 'Не указана'),
            'age': profile.get('age', 'Не указан'),
            'orientation': profile.get('orientation', 'Не указана'),
            'city': profile.get('city', 'Не указан'),
            'looking_for': profile.get('looking_for', 'Не указано'),
            'personality_type': profile.get('personality_type', 'Не указано'),
            'reference_photo': profile.get('reference_photo', None),
        }
