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
                    last_message_date TEXT,
                    last_message_ts INTEGER
                )
            ''')
            self.conn.commit()
        except Exception as e:
            logger.error(f"Error creating table: {e}")

    def increment_message(self, user_id, username):
        """Increment message count for a user, reset today_count if new day."""
        try:
            self.ensure_connection()
            cursor = self.conn.cursor()
            
            today = date.today().isoformat()
            now_ts = int(datetime.now().timestamp())
            
            # Get current user data
            cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
            row = cursor.fetchone()
            
            if row is None:
                # Insert new user
                cursor.execute('''
                    INSERT INTO users (user_id, username, message_count, today_count, last_message_date, last_message_ts)
                    VALUES (?, ?, 1, 1, ?, ?)
                ''', (user_id, username, today, now_ts))
            else:
                # Update existing user
                last_date = row['last_message_date']
                # If last_message_date is not today, reset today_count
                today_count = 1 if last_date != today else row['today_count'] + 1
                
                cursor.execute('''
                    UPDATE users
                    SET username = ?,
                        message_count = message_count + 1,
                        today_count = ?,
                        last_message_date = ?,
                        last_message_ts = ?
                    WHERE user_id = ?
                ''', (username, today_count, today, now_ts, user_id))
            
            self.conn.commit()
        except Exception as e:
            logger.error(f"Error incrementing message for user {user_id}: {e}")

    def get_top(self, limit=10):
        """Get top users by total message count."""
        try:
            self.ensure_connection()
            cursor = self.conn.cursor()
            cursor.execute('''
                SELECT user_id, username, message_count, today_count
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
                SELECT user_id, username, message_count, today_count
                FROM users
                ORDER BY today_count DESC
                LIMIT ?
            ''', (limit,))
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"Error getting today's top users: {e}")
            return []

    def get_user_stats(self, user_id):
        """Get stats for a specific user."""
        try:
            self.ensure_connection()
            cursor = self.conn.cursor()
            cursor.execute('''
                SELECT user_id, username, message_count, today_count, last_message_date, last_message_ts
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
        """Get a dynamic title based on message counts and time of day."""
        try:
            stats = self.get_user_stats(user_id)
            if not stats:
                return "New User"
            
            message_count = stats['message_count']
            # Get current hour from last_message_ts or use current time if not available
            last_ts = stats['last_message_ts']
            if last_ts:
                hour = datetime.fromtimestamp(last_ts).hour
            else:
                hour = datetime.now().hour
            
            # Define time of day
            if 5 <= hour < 12:
                time_of_day = "morning"
            elif 12 <= hour < 17:
                time_of_day = "afternoon"
            elif 17 <= hour < 21:
                time_of_day = "evening"
            else:
                time_of_day = "night"
            
            # Define titles based on message count
            if message_count >= 1000:
                base_title = "Elder"
            elif message_count >= 500:
                base_title = "Veteran"
            elif message_count >= 100:
                base_title = "Active"
            elif message_count >= 10:
                base_title = "Regular"
            else:
                base_title = "Newbie"
            
            return f"{base_title} of the {time_of_day}"
        except Exception as e:
            logger.error(f"Error getting dynamic title for user {user_id}: {e}")
            return "User"