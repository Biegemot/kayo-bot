import sqlite3
import os
from datetime import datetime, date
import traceback

# Импортируем нашу систему логирования
from bot.logging import log_function_call, get_logger

# Создаем логгер для этого модуля
logger = get_logger("kayo-bot.activity")

class ActivityManager:
    def __init__(self, db_path):
        """Initialize the database connection and create table if not exists."""
        self.db_path = db_path
        # Ensure the directory exists
        os.makedirs(os.path.dirname(os.path.abspath(db_path)), exist_ok=True)
        
        logger.info(f"Initializing ActivityManager", db_path=db_path)
        self.ensure_connection()
        self.create_table()
        self.migrate_schema()  # Ensure schema is up to date

    @log_function_call
    def ensure_connection(self):
        """Ensure we have a valid database connection."""
        if not hasattr(self, 'conn') or self.conn is None:
            try:
                self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
                self.conn.row_factory = sqlite3.Row
                logger.debug(f"Database connection established", db_path=self.db_path)
            except Exception as e:
                logger.error(f"Failed to connect to database: {e}", db_path=self.db_path)
                raise

    @log_function_call
    def create_table(self):
        """Create the users table if it doesn't exist."""
        try:
            self.ensure_connection()
            cursor = self.conn.cursor()
            
            # Log table creation
            logger.log_database("CREATE TABLE", "users")
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
            
            logger.log_database("CREATE TABLE", "messages")
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    text TEXT,
                    msg_date TEXT,
                    msg_ts INTEGER
                )
            ''')
            
            # Create user_profiles table
            logger.log_database("CREATE TABLE", "user_profiles")
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS user_profiles (
                    user_id INTEGER PRIMARY KEY,
                    fur_name TEXT DEFAULT '',
                    species TEXT DEFAULT '',
                    birthday TEXT DEFAULT '',
                    age TEXT DEFAULT '',
                    orientation TEXT DEFAULT '',
                    city TEXT DEFAULT '',
                    looking_for TEXT DEFAULT '',
                    personality_type TEXT DEFAULT '',
                    reference TEXT DEFAULT '',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
                )
            ''')
            
            # Create chat_stats table
            logger.log_database("CREATE TABLE", "chat_stats")
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS chat_stats (
                    date TEXT PRIMARY KEY,
                    total_messages INTEGER DEFAULT 0,
                    active_users INTEGER DEFAULT 0,
                    mood TEXT DEFAULT '',
                    topics TEXT DEFAULT ''
                )
            ''')
            
            self.conn.commit()
            logger.info("Database tables created/verified")
            
        except Exception as e:
            logger.error(f"Failed to create tables: {e}", exc_info=True)
            raise

    @log_function_call
    def migrate_schema(self):
        """Migrate database schema if needed."""
        try:
            self.ensure_connection()
            cursor = self.conn.cursor()
            
            # Check if user_profiles table exists
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='user_profiles'")
            if not cursor.fetchone():
                logger.info("Creating user_profiles table via migration")
                cursor.execute('''
                    CREATE TABLE user_profiles (
                        user_id INTEGER PRIMARY KEY,
                        fur_name TEXT DEFAULT '',
                        species TEXT DEFAULT '',
                        birthday TEXT DEFAULT '',
                        age TEXT DEFAULT '',
                        orientation TEXT DEFAULT '',
                        city TEXT DEFAULT '',
                        looking_for TEXT DEFAULT '',
                        personality_type TEXT DEFAULT '',
                        reference TEXT DEFAULT '',
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                self.conn.commit()
                
            # Check for missing columns in user_profiles
            cursor.execute("PRAGMA table_info(user_profiles)")
            columns = [col[1] for col in cursor.fetchall()]
            
            missing_columns = []
            expected_columns = ['fur_name', 'species', 'birthday', 'age', 'orientation', 
                              'city', 'looking_for', 'personality_type', 'reference']
            
            for col in expected_columns:
                if col not in columns:
                    missing_columns.append(col)
            
            if missing_columns:
                logger.info(f"Adding missing columns to user_profiles: {missing_columns}")
                for col in missing_columns:
                    try:
                        cursor.execute(f"ALTER TABLE user_profiles ADD COLUMN {col} TEXT DEFAULT ''")
                    except sqlite3.OperationalError as e:
                        logger.warning(f"Column {col} might already exist: {e}")
                
                self.conn.commit()
            
            logger.debug("Schema migration completed")
            
        except Exception as e:
            logger.error(f"Migration failed: {e}", exc_info=True)

    @log_function_call
    def increment_message(self, user_id, username):
        """Increment message count for a user."""
        try:
            self.ensure_connection()
            cursor = self.conn.cursor()
            
            today = date.today().isoformat()
            now_ts = int(datetime.now().timestamp())
            
            # Check if user exists
            cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
            user = cursor.fetchone()
            
            if user:
                # Update existing user
                if user['last_message_date'] != today:
                    # New day, reset today counters
                    cursor.execute('''
                        UPDATE users 
                        SET message_count = message_count + 1,
                            today_count = 1,
                            kiss_count_today = 0,
                            slap_count_today = 0,
                            last_message_date = ?,
                            last_active_date = ?,
                            last_message_ts = ?,
                            username = ?
                        WHERE user_id = ?
                    ''', (today, today, now_ts, username, user_id))
                else:
                    # Same day, increment today_count
                    cursor.execute('''
                        UPDATE users 
                        SET message_count = message_count + 1,
                            today_count = today_count + 1,
                            last_message_date = ?,
                            last_active_date = ?,
                            last_message_ts = ?,
                            username = ?
                        WHERE user_id = ?
                    ''', (today, today, now_ts, username, user_id))
            else:
                # Insert new user
                cursor.execute('''
                    INSERT INTO users 
                    (user_id, username, message_count, today_count, last_message_date, last_active_date, last_message_ts)
                    VALUES (?, ?, 1, 1, ?, ?, ?)
                ''', (user_id, username, today, today, now_ts))
            
            self.conn.commit()
            
            # Log the operation
            logger.log_database("INCREMENT_MESSAGE", "users", 
                               user_id=user_id, username=username, today_count="incremented")
            
        except Exception as e:
            logger.error(f"Failed to increment message: {e}", 
                         user_id=user_id, username=username, exc_info=True)
            raise

    @log_function_call
    def store_message(self, user_id, text):
        """Store a message for topic analysis."""
        try:
            if not text or len(text.strip()) == 0:
                logger.debug("Empty message, not storing")
                return
                
            self.ensure_connection()
            cursor = self.conn.cursor()
            
            today = date.today().isoformat()
            now_ts = int(datetime.now().timestamp())
            
            cursor.execute('''
                INSERT INTO messages (user_id, text, msg_date, msg_ts)
                VALUES (?, ?, ?, ?)
            ''', (user_id, text[:500], today, now_ts))
            
            self.conn.commit()
            
            # Log the operation
            logger.debug(f"Message stored for topic analysis",
                         user_id=user_id, message_length=len(text))
            
        except Exception as e:
            logger.error(f"Failed to store message: {e}", 
                         user_id=user_id, message_preview=text[:100], exc_info=True)

    @log_function_call
    def get_top_users(self, limit=10):
        """Get top users by message count."""
        try:
            self.ensure_connection()
            cursor = self.conn.cursor()
            
            cursor.execute('''
                SELECT user_id, username, message_count, today_count
                FROM users 
                ORDER BY message_count DESC 
                LIMIT ?
            ''', (limit,))
            
            results = cursor.fetchall()
            
            logger.log_database("GET_TOP_USERS", "users", limit=limit, result_count=len(results))
            return results
            
        except Exception as e:
            logger.error(f"Failed to get top users: {e}", exc_info=True)
            return []

    @log_function_call
    def get_today_top(self, limit=10):
        """Get top users for today."""
        try:
            self.ensure_connection()
            cursor = self.conn.cursor()
            
            today = date.today().isoformat()
            
            cursor.execute('''
                SELECT user_id, username, today_count
                FROM users 
                WHERE last_message_date = ?
                ORDER BY today_count DESC 
                LIMIT ?
            ''', (today, limit))
            
            results = cursor.fetchall()
            
            logger.log_database("GET_TODAY_TOP", "users", limit=limit, result_count=len(results))
            return results
            
        except Exception as e:
            logger.error(f"Failed to get today's top: {e}", exc_info=True)
            return []

    @log_function_call
    def get_user_stats(self, user_id):
        """Get statistics for a specific user."""
        try:
            self.ensure_connection()
            cursor = self.conn.cursor()
            
            cursor.execute('''
                SELECT user_id, username, message_count, today_count,
                       last_message_date, last_active_date
                FROM users 
                WHERE user_id = ?
            ''', (user_id,))
            
            result = cursor.fetchone()
            
            if result:
                logger.log_database("GET_USER_STATS", "users", user_id=user_id, found=True)
                return dict(result)
            else:
                logger.debug(f"User not found in stats", user_id=user_id)
                return None
                
        except Exception as e:
            logger.error(f"Failed to get user stats: {e}", user_id=user_id, exc_info=True)
            return None

    @log_function_call
    def get_profile(self, user_id):
        """Get user profile."""
        try:
            self.ensure_connection()
            cursor = self.conn.cursor()
            
            cursor.execute('''
                SELECT * FROM user_profiles 
                WHERE user_id = ?
            ''', (user_id,))
            
            result = cursor.fetchone()
            
            if result:
                logger.log_database("GET_PROFILE", "user_profiles", user_id=user_id, found=True)
                return dict(result)
            else:
                logger.debug(f"Profile not found", user_id=user_id)
                return None
                
        except Exception as e:
            logger.error(f"Failed to get profile: {e}", user_id=user_id, exc_info=True)
            return None

    @log_function_call
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
                operation = "UPDATE"
            else:
                # Create new profile
                cursor.execute(f'INSERT INTO user_profiles (user_id, {field}) VALUES (?, ?)', (user_id, value))
                operation = "INSERT"
            
            self.conn.commit()
            
            logger.log_database(f"SAVE_PROFILE_FIELD_{operation}", "user_profiles", 
                               user_id=user_id, field=field, value=value)
            
        except Exception as e:
            logger.error(f"Failed to save profile field: {e}", 
                         user_id=user_id, field=field, value=value, exc_info=True)
            raise

    @log_function_call
    def get_today_messages(self):
        """Get all messages from today for topic analysis."""
        try:
            self.ensure_connection()
            cursor = self.conn.cursor()
            
            today = date.today().isoformat()
            
            cursor.execute('''
                SELECT text FROM messages 
                WHERE msg_date = ?
                ORDER BY msg_ts DESC
                LIMIT 100
            ''', (today,))
            
            results = cursor.fetchall()
            messages = [row['text'] for row in results]
            
            logger.log_database("GET_TODAY_MESSAGES", "messages", 
                               today=today, message_count=len(messages))
            return messages
            
        except Exception as e:
            logger.error(f"Failed to get today's messages: {e}", exc_info=True)
            return []

    @log_function_call
    def cleanup_old_messages(self, days_to_keep=7):
        """Clean up old messages to prevent database bloat."""
        try:
            self.ensure_connection()
            cursor = self.conn.cursor()
            
            cutoff_date = (datetime.now() - timedelta(days=days_to_keep)).date().isoformat()
            
            cursor.execute('DELETE FROM messages WHERE msg_date < ?', (cutoff_date,))
            deleted_count = cursor.rowcount
            
            self.conn.commit()
            
            logger.info(f"Cleaned up old messages", 
                        cutoff_date=cutoff_date, deleted_count=deleted_count)
            
            return deleted_count
            
        except Exception as e:
            logger.error(f"Failed to cleanup old messages: {e}", exc_info=True)
            return 0

    @log_function_call
    def close(self):
        """Close database connection."""
        try:
            if hasattr(self, 'conn') and self.conn:
                self.conn.close()
                self.conn = None
                logger.debug("Database connection closed")
        except Exception as e:
            logger.error(f"Failed to close database connection: {e}", exc_info=True)