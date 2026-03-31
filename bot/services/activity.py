import sqlite3
import os
from datetime import datetime, date
import logging

logger = logging.getLogger(__name__)

class ActivityManager:
    def __init__(self, db_path):
        """Initialize the database connection and create table if not exists."""
        self.db_path = db_path
        # Ensure the directory exists
        os.makedirs(os.path.dirname(os.path.abspath(db_path)), exist_ok=True)
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
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    text TEXT,
                    msg_date TEXT,
                    msg_ts INTEGER
                )
            ''')
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_messages_date ON messages(msg_date)
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
            
            # Add hug_count_today if it doesn't exist
            if 'hug_count_today' not in columns:
                cursor.execute('ALTER TABLE users ADD COLUMN hug_count_today INTEGER DEFAULT 0')
                logger.info("Added hug_count_today column to users table")
            
            # Add bite_count_today if it doesn't exist
            if 'bite_count_today' not in columns:
                cursor.execute('ALTER TABLE users ADD COLUMN bite_count_today INTEGER DEFAULT 0')
                logger.info("Added bite_count_today column to users table")
            
            # Add pat_count_today if it doesn't exist
            if 'pat_count_today' not in columns:
                cursor.execute('ALTER TABLE users ADD COLUMN pat_count_today INTEGER DEFAULT 0')
                logger.info("Added pat_count_today column to users table")
            
            # Add boop_count_today if it doesn't exist
            if 'boop_count_today' not in columns:
                cursor.execute('ALTER TABLE users ADD COLUMN boop_count_today INTEGER DEFAULT 0')
                logger.info("Added boop_count_today column to users table")
                
            # Add last_active_date if it doesn't exist
            if 'last_active_date' not in columns:
                cursor.execute('ALTER TABLE users ADD COLUMN last_active_date TEXT')
                logger.info("Added last_active_date column to users table")
            
            # Create user_profiles table if it doesn't exist
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS user_profiles (
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
            logger.info("Created user_profiles table")
            
            # Create user_titles table if it doesn't exist
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS user_titles (
                    user_id INTEGER,
                    title TEXT,
                    date TEXT,
                    PRIMARY KEY (user_id, date)
                )
            ''')
            logger.info("Created user_titles table")
            
            self.conn.commit()
        except Exception as e:
            logger.error(f"Error migrating schema: {e}")

    def _maybe_reset_today(self, user_id):
        """Reset today counts if the last active date is not today."""
        try:
            self.ensure_connection()
            today = date.today().isoformat()
            
            # Get current user data
            cursor = self.conn.cursor()
            cursor.execute('SELECT last_active_date, today_count, kiss_count_today, slap_count_today, hug_count_today, bite_count_today, pat_count_today, boop_count_today FROM users WHERE user_id = ?', (user_id,))
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
                        hug_count_today = 0,
                        bite_count_today = 0,
                        pat_count_today = 0,
                        boop_count_today = 0,
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

    def increment_hug(self, user_id):
        """Increment hug count for a user, reset today counts if new day."""
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
                    INSERT INTO users (user_id, username, message_count, today_count, kiss_count_today, slap_count_today, hug_count_today, bite_count_today, pat_count_today, boop_count_today, last_message_date, last_active_date, last_message_ts)
                    VALUES (?, ?, 0, 0, 0, 0, 1, 0, 0, 0, ?, ?, ?)
                ''', (user_id, "", today, today, today))
            else:
                # Update existing user
                hug_count = row['hug_count_today'] + 1
                
                cursor.execute('''
                    UPDATE users
                    SET hug_count_today = ?,
                        last_active_date = ?
                    WHERE user_id = ?
                ''', (hug_count, today, user_id))
            
            self.conn.commit()
        except Exception as e:
            logger.error(f"Error incrementing hug for user {user_id}: {e}")

    def increment_bite(self, user_id):
        """Increment bite count for a user, reset today counts if new day."""
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
                    INSERT INTO users (user_id, username, message_count, today_count, kiss_count_today, slap_count_today, hug_count_today, bite_count_today, pat_count_today, boop_count_today, last_message_date, last_active_date, last_message_ts)
                    VALUES (?, ?, 0, 0, 0, 0, 0, 1, 0, 0, ?, ?, ?)
                ''', (user_id, "", today, today, today))
            else:
                # Update existing user
                bite_count = row['bite_count_today'] + 1
                
                cursor.execute('''
                    UPDATE users
                    SET bite_count_today = ?,
                        last_active_date = ?
                    WHERE user_id = ?
                ''', (bite_count, today, user_id))
            
            self.conn.commit()
        except Exception as e:
            logger.error(f"Error incrementing bite for user {user_id}: {e}")

    def increment_pat(self, user_id):
        """Increment pat count for a user, reset today counts if new day."""
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
                    INSERT INTO users (user_id, username, message_count, today_count, kiss_count_today, slap_count_today, hug_count_today, bite_count_today, pat_count_today, boop_count_today, last_message_date, last_active_date, last_message_ts)
                    VALUES (?, ?, 0, 0, 0, 0, 0, 0, 1, 0, ?, ?, ?)
                ''', (user_id, "", today, today, today))
            else:
                # Update existing user
                pat_count = row['pat_count_today'] + 1
                
                cursor.execute('''
                    UPDATE users
                    SET pat_count_today = ?,
                        last_active_date = ?
                    WHERE user_id = ?
                ''', (pat_count, today, user_id))
            
            self.conn.commit()
        except Exception as e:
            logger.error(f"Error incrementing pat for user {user_id}: {e}")

    def increment_boop(self, user_id):
        """Increment boop count for a user, reset today counts if new day."""
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
                    INSERT INTO users (user_id, username, message_count, today_count, kiss_count_today, slap_count_today, hug_count_today, bite_count_today, pat_count_today, boop_count_today, last_message_date, last_active_date, last_message_ts)
                    VALUES (?, ?, 0, 0, 0, 0, 0, 0, 0, 1, ?, ?, ?)
                ''', (user_id, "", today, today, today))
            else:
                # Update existing user
                boop_count = row['boop_count_today'] + 1
                
                cursor.execute('''
                    UPDATE users
                    SET boop_count_today = ?,
                        last_active_date = ?
                    WHERE user_id = ?
                ''', (boop_count, today, user_id))
            
            self.conn.commit()
        except Exception as e:
            logger.error(f"Error incrementing boop for user {user_id}: {e}")

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
                SELECT user_id, username, message_count, today_count, kiss_count_today, slap_count_today, hug_count_today, bite_count_today, pat_count_today, boop_count_today, last_message_date, last_message_ts
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
            # Update titles for today
            titles = self.determine_titles_today(user_id)
            for title in titles:
                self.save_user_title(user_id, title)
            
            title = self.get_user_title(user_id)
            return title
        except Exception as e:
            logger.error(f"Error getting dynamic title for user {user_id}: {e}")
            return "Пользователь"

    def get_user_titles(self, user_id):
        """Get all titles for user today."""
        try:
            self.ensure_connection()
            cursor = self.conn.cursor()
            today = date.today().isoformat()
            cursor.execute('SELECT title FROM user_titles WHERE user_id = ? AND date = ?', (user_id, today))
            return [row['title'] for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Error getting titles for user {user_id}: {e}")
            return []

    def save_user_title(self, user_id, title):
        """Save a title for user today."""
        try:
            self.ensure_connection()
            cursor = self.conn.cursor()
            today = date.today().isoformat()
            cursor.execute('INSERT OR REPLACE INTO user_titles (user_id, title, date) VALUES (?, ?, ?)', (user_id, title, today))
            self.conn.commit()
        except Exception as e:
            logger.error(f"Error saving title for user {user_id}: {e}")

    def get_all_titles_for_user(self, user_id):
        """Get all titles for user (all time)."""
        try:
            self.ensure_connection()
            cursor = self.conn.cursor()
            cursor.execute('SELECT DISTINCT title FROM user_titles WHERE user_id = ? ORDER BY date DESC', (user_id,))
            return [row['title'] for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Error getting all titles for user {user_id}: {e}")
            return []

    def determine_titles_today(self, user_id):
        """Determine all titles for user today based on action and message statistics."""
        try:
            stats = self.get_user_stats(user_id)
            if not stats:
                return []
            
            titles = []
            
            # Action-based titles
            # Check if user is top slapper today
            top_slap = self.get_slap_top_today(limit=1)
            if top_slap and top_slap[0]['user_id'] == user_id and top_slap[0]['slap_count_today'] > 0:
                titles.append("Шлёпало")
            
            # Check if user is top kisser today
            top_kiss = self.get_kiss_top_today(limit=1)
            if top_kiss and top_kiss[0]['user_id'] == user_id and top_kiss[0]['kiss_count_today'] > 0:
                titles.append("Поцелуйчик")
            
            # Check hug count
            if stats.get('hug_count_today', 0) > 10:
                titles.append("Обнимашка")
            
            # Check bite count
            if stats.get('bite_count_today', 0) > 10:
                titles.append("Злюка")
            
            # Check pat count
            if stats.get('pat_count_today', 0) > 10:
                titles.append("Ласковый")
            
            # Check boop count
            if stats.get('boop_count_today', 0) > 10:
                titles.append("Няшный")
            
            # Message-based titles
            # Check if user is top chatter today
            top_today = self.get_today_top(limit=1)
            if top_today and top_today[0]['user_id'] == user_id and top_today[0]['today_count'] > 0:
                titles.append("Болтун дня")
            
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
                titles.append("Ночной житель")
            elif 5 <= hour <= 11:
                titles.append("Ранний зверь")
            
            # Low message count but active today
            if stats['message_count'] < 10 and stats['today_count'] > 0:
                titles.append("Тихий, но опасный")
            
            # Inactive for a long time
            if days_since_last > 7:
                titles.append("Призрак")
            
            return titles
        except Exception as e:
            logger.error(f"Error determining titles for user {user_id}: {e}")
            return []

    def get_user_title(self, user_id):
        """Get the primary title for user today."""
        titles = self.get_user_titles(user_id)
        if titles:
            return titles[0]
        return "Активный"

    def get_all_user_titles(self, user_id):
        """Get all titles for user today."""
        titles = self.get_user_titles(user_id)
        if titles:
            return titles
        return ["Активный"]

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

    def store_message(self, user_id, text):
        """Store a message for topic extraction."""
        try:
            self.ensure_connection()
            cursor = self.conn.cursor()
            today = date.today().isoformat()
            now_ts = int(datetime.now().timestamp())
            cursor.execute('''
                INSERT INTO messages (user_id, text, msg_date, msg_ts)
                VALUES (?, ?, ?, ?)
            ''', (user_id, text[:500], today, now_ts))
            self.conn.commit()
        except Exception as e:
            logger.error(f"Error storing message: {e}")

    def get_today_messages(self):
        """Get all message texts from today for topic extraction."""
        try:
            self.ensure_connection()
            cursor = self.conn.cursor()
            today = date.today().isoformat()
            cursor.execute('SELECT text FROM messages WHERE msg_date = ?', (today,))
            return [row['text'] for row in cursor.fetchall() if row['text']]
        except Exception as e:
            logger.error(f"Error getting today messages: {e}")
            return []

    def cleanup_old_messages(self, days=7):
        """Remove messages older than N days."""
        try:
            self.ensure_connection()
            cursor = self.conn.cursor()
            cutoff = date.today().isoformat()
            cursor.execute('DELETE FROM messages WHERE msg_date < date(?, ?)',
                           (cutoff, f'-{days} days'))
            self.conn.commit()
        except Exception as e:
            logger.error(f"Error cleaning up old messages: {e}")

    # Profile methods
    def get_profile(self, user_id):
        """Get user profile."""
        try:
            self.ensure_connection()
            cursor = self.conn.cursor()
            cursor.execute('SELECT * FROM user_profiles WHERE user_id = ?', (user_id,))
            row = cursor.fetchone()
            if row:
                return dict(row)
            return None
        except Exception as e:
            logger.error(f"Error getting profile for user {user_id}: {e}")
            return None

    def save_profile_field(self, user_id, field, value):
        """Save a single profile field."""
        try:
            self.ensure_connection()
            cursor = self.conn.cursor()
            
            # Check if profile exists
            cursor.execute('SELECT user_id FROM user_profiles WHERE user_id = ?', (user_id,))
            exists = cursor.fetchone()
            
            if exists:
                # Update existing profile
                cursor.execute(f'UPDATE user_profiles SET {field} = ?, updated_at = CURRENT_TIMESTAMP WHERE user_id = ?', (value, user_id))
            else:
                # Create new profile
                cursor.execute(f'INSERT INTO user_profiles (user_id, {field}) VALUES (?, ?)', (user_id, value))
            
            self.conn.commit()
            return True
        except Exception as e:
            logger.error(f"Error saving profile field for user {user_id}: {e}")
            return False

    def update_profile(self, user_id, data):
        """Update entire profile."""
        try:
            self.ensure_connection()
            cursor = self.conn.cursor()
            
            # Check if profile exists
            cursor.execute('SELECT user_id FROM user_profiles WHERE user_id = ?', (user_id,))
            exists = cursor.fetchone()
            
            if exists:
                # Update existing profile
                set_clause = ', '.join([f"{key} = ?" for key in data.keys()])
                values = list(data.values()) + [user_id]
                cursor.execute(f'UPDATE user_profiles SET {set_clause}, updated_at = CURRENT_TIMESTAMP WHERE user_id = ?', values)
            else:
                # Create new profile
                columns = ', '.join(['user_id'] + list(data.keys()))
                placeholders = ', '.join(['?'] * (len(data) + 1))
                values = [user_id] + list(data.values())
                cursor.execute(f'INSERT INTO user_profiles ({columns}) VALUES ({placeholders})', values)
            
            self.conn.commit()
            return True
        except Exception as e:
            logger.error(f"Error updating profile for user {user_id}: {e}")
            return False