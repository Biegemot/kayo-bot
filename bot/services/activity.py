import sqlite3
import os
from datetime import datetime, date
import logging

logger = logging.getLogger(__name__)

class ActivityManager:
    def __init__(self, db_path='bot/database/activity.db'):
        """Initialize the database connection and create table if not exists."""
        self.db_path = db_path
        # Ensure the directory exists
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self.ensure_connection()
        self.create_table()
        self.migrate_schema()  # Ensure schema is up to date

    def ensure_connection(self):
        """Ensure we have a valid database connection."""
        if not hasattr(self, 'conn') or self.conn is None:
            self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
            self.conn.row_factory = sqlite3.Row

    def create_table(self):
        """Create the users table if it doesn't exist."""
        try:
            self.ensure_connection()
            cursor = self.conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    username TEXT,
                    message_count INTEGER DEFAULT 0,
                    today_count INTEGER DEFAULT 0,
                    kiss_count_today INTEGER DEFAULT 0,
                    slap_count_today INTEGER DEFAULT 0,
                    last_message_date TEXT,
                    last_active_date TEXT,
                    last_message_ts INTEGER
                )
            ''')
            self.conn.commit()
        except Exception as e:
            logger.error(f"Error creating table: {e}")

    def migrate_schema(self):
        """Migrate existing database schema to add new columns if they don't exist."""
        try:
            self.ensure_connection()
            cursor = self.conn.cursor()
            
            # Check if kiss_count_today column exists
            cursor.execute("PRAGMA table_info(users)")
            columns = [column[1] for column in cursor.fetchall()]
            
            # Add kiss_count_today if it doesn't exist
            if 'kiss_count_today' not in columns:
                cursor.execute('ALTER TABLE users ADD COLUMN kiss_count_today INTEGER DEFAULT 0')
                logger.info("Added kiss_count_today column to users table")
            
            # Add slap_count_today if it doesn't exist
            if 'slap_count_today' not in columns:
                cursor.execute('ALTER TABLE users ADD COLUMN slap_count_today INTEGER DEFAULT 0')
                logger.info("Added slap_count_today column to users table")
                
            # Add last_active_date if it doesn't exist
            if 'last_active_date' not in columns:
                cursor.execute('ALTER TABLE users ADD COLUMN last_active_date TEXT')
                logger.info("Added last_active_date column to users table")
            
            self.conn.commit()
        except Exception as e:
            logger.error(f"Error migrating schema: {e}")

    def _maybe_reset_today(self, user_id):
        """Reset today counts if the last active date is not today."""
        try:
            today = date.today().isoformat()
            
            # Get current user data
            cursor = self.conn.cursor()
            cursor.execute('SELECT last_active_date, today_count, kiss_count_today, slap_count_today FROM users WHERE user_id = ?', (user_id,))
            row = cursor.fetchone()
            
            if row is None:
                return
                
            last_active_date = row['last_active_date']
            
            # If last_active_date is not today, reset today counts
            if last_active_date != today:
                cursor.execute('''
                    UPDATE users
                    SET today_count = 0,
                        kiss_count_today = 0,
                        slap_count_today = 0,
                        last_active_date = ?
                    WHERE user_id = ?
                ''', (today, user_id))
                self.conn.commit()
        except Exception as e:
            logger.error(f"Error resetting today counts for user {user_id}: {e}")

    def increment_message(self, user_id, username):
        """Increment message count for a user, reset today_count if new day."""
        try:
            self.ensure_connection()
            cursor = self.conn.cursor()
            
            today = date.today().isoformat()
            now_ts = int(datetime.now().timestamp())
            
            # Reset today counts if needed
            self._maybe_reset_today(user_id)
            
            # Get current user data
            cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
            row = cursor.fetchone()
            
            if row is None:
                # Insert new user
                cursor.execute('''
                    INSERT INTO users (user_id, username, message_count, today_count, kiss_count_today, slap_count_today, last_message_date, last_active_date, last_message_ts)
                    VALUES (?, ?, 1, 1, 0, 0, ?, ?, ?)
                ''', (user_id, username, today, today, now_ts))
            else:
                # Update existing user
                last_date = row['last_message_date']
                # If last_message_date is not today, reset today_count (but we already reset via _maybe_reset_today)
                today_count = row['today_count'] + 1
                
                cursor.execute('''
                    UPDATE users
                    SET username = ?,
                        message_count = message_count + 1,
                        today_count = ?,
                        last_message_date = ?,
                        last_message_ts = ?,
                        last_active_date = ?
                    WHERE user_id = ?
                ''', (username, today_count, today, now_ts, today, user_id))
            
            self.conn.commit()
        except Exception as e:
            logger.error(f"Error incrementing message for user {user_id}: {e}")

    def increment_kiss(self, user_id):
        """Increment kiss count for a user, reset today counts if new day."""
        try:
            self.ensure_connection()
            cursor = self.conn.cursor()
            
            today = date.today().isoformat()
            
            # Reset today counts if needed
            self._maybe_reset_today(user_id)
            
            # Get current user data
            cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
            row = cursor.fetchone()
            
            if row is None:
                # Insert new user with default values
                cursor.execute('''
                    INSERT INTO users (user_id, username, message_count, today_count, kiss_count_today, slap_count_today, last_message_date, last_active_date, last_message_ts)
                    VALUES (?, ?, 0, 0, 1, 0, ?, ?, ?)
                ''', (user_id, "", today, today, today))
            else:
                # Update existing user
                kiss_count = row['kiss_count_today'] + 1
                
                cursor.execute('''
                    UPDATE users
                    SET kiss_count_today = ?,
                        last_active_date = ?
                    WHERE user_id = ?
                ''', (kiss_count, today, user_id))
            
            self.conn.commit()
        except Exception as e:
            logger.error(f"Error incrementing kiss for user {user_id}: {e}")

    def increment_slap(self, user_id):
        """Increment slap count for a user, reset today counts if new day."""
        try:
            self.ensure_connection()
            cursor = self.conn.cursor()
            
            today = date.today().isoformat()
            
            # Reset today counts if needed
            self._maybe_reset_today(user_id)
            
            # Get current user data
            cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
            row = cursor.fetchone()
            
            if row is None:
                # Insert new user with default values
                cursor.execute('''
                    INSERT INTO users (user_id, username, message_count, today_count, kiss_count_today, slap_count_today, last_message_date, last_active_date, last_message_ts)
                    VALUES (?, ?, 0, 0, 0, 1, ?, ?, ?)
                ''', (user_id, "", today, today, today))
            else:
                # Update existing user
                slap_count = row['slap_count_today'] + 1
                
                cursor.execute('''
                    UPDATE users
                    SET slap_count_today = ?,
                        last_active_date = ?
                    WHERE user_id = ?
                ''', (slap_count, today, user_id))
            
            self.conn.commit()
        except Exception as e:
            logger.error(f"Error incrementing slap for user {user_id}: {e}")

    def get_top(self, limit=10):
        """Get top users by total message count."""
        try:
            self.ensure_connection()
            cursor = self.conn.cursor()
            cursor.execute('''
                SELECT user_id, username, message_count, today_count, kiss_count_today, slap_count_today
                FROM users
                ORDER BY message_count DESC
                LIMIT ?
            ''', (limit,))
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"Error getting top users: {e}")
            return []

    def get_today_top(self, limit=10):
        """Get top users by today's message count."""
        try:
            self.ensure_connection()
            cursor = self.conn.cursor()
            cursor.execute('''
                SELECT user_id, username, message_count, today_count, kiss_count_today, slap_count_today
                FROM users
                ORDER BY today_count DESC
                LIMIT ?
            ''', (limit,))
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"Error getting today's top users: {e}")
            return []

    def get_kiss_top_today(self, limit=1):
        """Get top users by kiss count today."""
        try:
            self.ensure_connection()
            cursor = self.conn.cursor()
            cursor.execute('''
                SELECT user_id, username, kiss_count_today
                FROM users
                WHERE kiss_count_today > 0
                ORDER BY kiss_count_today DESC
                LIMIT ?
            ''', (limit,))
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"Error getting kiss top users today: {e}")
            return []

    def get_slap_top_today(self, limit=1):
        """Get top users by slap count today."""
        try:
            self.ensure_connection()
            cursor = self.conn.cursor()
            cursor.execute('''
                SELECT user_id, username, slap_count_today
                FROM users
                WHERE slap_count_today > 0
                ORDER BY slap_count_today DESC
                LIMIT ?
            ''', (limit,))
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"Error getting slap top users today: {e}")
            return []

    def get_user_stats(self, user_id):
        """Get stats for a specific user."""
        try:
            self.ensure_connection()
            cursor = self.conn.cursor()
            cursor.execute('''
                SELECT user_id, username, message_count, today_count, kiss_count_today, slap_count_today, last_message_date, last_message_ts
                FROM users
                WHERE user_id = ?
            ''', (user_id,))
            row = cursor.fetchone()
            if row:
                return dict(row)
            return None
        except Exception as e:
            logger.error(f"Error getting user stats for {user_id}: {e}")
            return None

    def get_dynamic_title(self, user_id):
        """Get a dynamic title based on actions and message counts."""
        try:
            title = self.get_user_title(user_id)
            return title
        except Exception as e:
            logger.error(f"Error getting dynamic title for user {user_id}: {e}")
            return "Пользователь"

    def get_user_title(self, user_id):
        """Determine user's title based on action and message statistics."""
        try:
            stats = self.get_user_stats(user_id)
            if not stats:
                return "Новый пользователь"
            
            # Action-based titles have priority
            # Check if user is top slapper today
            top_slap = self.get_slap_top_today(limit=1)
            if top_slap and top_slap[0]['user_id'] == user_id and top_slap[0]['slap_count_today'] > 0:
                return "Хорни"
            
            # Check if user is top kisser today
            top_kiss = self.get_kiss_top_today(limit=1)
            if top_kiss and top_kiss[0]['user_id'] == user_id and top_kiss[0]['kiss_count_today'] > 0:
                return "Романтик"
            
            # Message-based titles
            # Check if user is top chatter today
            top_today = self.get_today_top(limit=1)
            if top_today and top_today[0]['user_id'] == user_id and top_today[0]['today_count'] > 0:
                return "Болтун дня"
            
            # Time-based titles
            last_ts = stats['last_message_ts']
            if last_ts:
                hour = datetime.fromtimestamp(last_ts).hour
                now_ts = int(datetime.now().timestamp())
                days_since_last = (now_ts - last_ts) / (24 * 3600)
            else:
                hour = datetime.now().hour
                days_since_last = 999  # never posted
            
            if 22 <= hour <= 23 or 0 <= hour <= 4:
                return "Ночной житель"
            elif 5 <= hour <= 11:
                return "Ранний зверь"
            
            # Low message count but active today
            if stats['message_count'] < 10 and stats['today_count'] > 0:
                return "Тихий, но опасный"
            
            # Inactive for a long time
            if days_since_last > 7:
                return "Призрак"
            
            # Default
            return "Активный"
        except Exception as e:
            logger.error(f"Error determining title for user {user_id}: {e}")
            return "Пользователь"

    def get_user_rank(self, user_id):
        """Get user's rank based on total messages."""
        try:
            self.ensure_connection()
            cursor = self.conn.cursor()
            # Count users with higher message_count
            cursor.execute('''
                SELECT COUNT(*) + 1 as rank
                FROM users
                WHERE message_count > (SELECT message_count FROM users WHERE user_id = ?)
            ''', (user_id,))
            row = cursor.fetchone()
            if row:
                return row['rank']
            return 1
        except Exception as e:
            logger.error(f"Error getting rank for user {user_id}: {e}")
            return 0

    def find_user_by_username(self, username):
        """Find user_id by username (case-insensitive). Returns first match."""
        try:
            self.ensure_connection()
            cursor = self.conn.cursor()
            # Remove leading @ if present
            if username.startswith('@'):
                username = username[1:]
            cursor.execute('''
                SELECT user_id FROM users
                WHERE LOWER(username) = LOWER(?)
                LIMIT 1
            ''', (username,))
            row = cursor.fetchone()
            if row:
                return row['user_id']
            return None
        except Exception as e:
            logger.error(f"Error finding user by username {username}: {e}")
            return None