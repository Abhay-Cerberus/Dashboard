"""
Database management module using SQLite
Handles all data persistence for the dashboard
"""

import sqlite3
import json
from datetime import datetime
from pathlib import Path
import logging

class DatabaseManager:
    def __init__(self, db_path="dashboard.db"):
        self.db_path = db_path
        self.conn = None
        self.init_database()
    
    def init_database(self):
        """Initialize database connection and create tables"""
        try:
            self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
            self.conn.row_factory = sqlite3.Row  # Enable dict-like access
            self.create_tables()
            logging.info("Database initialized successfully")
        except Exception as e:
            logging.error(f"Database initialization failed: {e}")
            raise
    
    def create_tables(self):
        """Create all necessary tables"""
        cursor = self.conn.cursor()
        
        # Settings table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # API usage tracking table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS api_usage (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                api_name TEXT NOT NULL,
                model_name TEXT,
                request_type TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                success BOOLEAN DEFAULT 1,
                error_message TEXT
            )
        ''')
        
        # RSS feeds table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS feeds (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                url TEXT NOT NULL UNIQUE,
                active BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # News items table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS news_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                feed_id INTEGER,
                title TEXT NOT NULL,
                link TEXT,
                description TEXT,
                summary TEXT,
                published TIMESTAMP,
                sent_to_discord BOOLEAN DEFAULT FALSE,
                sent_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (feed_id) REFERENCES feeds (id)
            )
        ''')
        
        # Add sent_to_discord column if it doesn't exist (for existing databases)
        try:
            cursor.execute('ALTER TABLE news_items ADD COLUMN sent_to_discord BOOLEAN DEFAULT FALSE')
        except sqlite3.OperationalError:
            pass  # Column already exists
        
        try:
            cursor.execute('ALTER TABLE news_items ADD COLUMN sent_at TIMESTAMP')
        except sqlite3.OperationalError:
            pass  # Column already exists
        
        # Games table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS games (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                appid TEXT,
                name TEXT NOT NULL,
                platform TEXT NOT NULL,
                playtime INTEGER DEFAULT 0,
                achievements_total INTEGER DEFAULT 0,
                achievements_unlocked INTEGER DEFAULT 0,
                has_achievements BOOLEAN DEFAULT 0,
                icon_url TEXT,
                last_played TIMESTAMP,
                is_completed BOOLEAN DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Tasks table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT,
                due_date TIMESTAMP,
                priority TEXT DEFAULT 'Medium',
                status TEXT DEFAULT 'Pending',
                recurrence TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                completed_at TIMESTAMP
            )
        ''')
        
        self.conn.commit()
        
        # Add is_completed column if it doesn't exist (for existing databases)
        try:
            cursor.execute("ALTER TABLE games ADD COLUMN is_completed BOOLEAN DEFAULT 0")
            self.conn.commit()
        except sqlite3.OperationalError:
            # Column already exists
            pass
    
    # Settings methods
    def get_setting(self, key, default=None):
        """Get a setting value"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT value FROM settings WHERE key = ?", (key,))
        result = cursor.fetchone()
        if result:
            try:
                return json.loads(result['value'])
            except json.JSONDecodeError:
                return result['value']
        return default
    
    def set_setting(self, key, value):
        """Set a setting value"""
        cursor = self.conn.cursor()
        if isinstance(value, (dict, list)):
            value = json.dumps(value)
        cursor.execute('''
            INSERT OR REPLACE INTO settings (key, value, updated_at) 
            VALUES (?, ?, CURRENT_TIMESTAMP)
        ''', (key, value))
        self.conn.commit()
    
    # Feed methods
    def add_feed(self, name, url):
        """Add a new RSS feed"""
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO feeds (name, url) VALUES (?, ?)
        ''', (name, url))
        self.conn.commit()
        return cursor.lastrowid
    
    def get_feeds(self, active_only=True):
        """Get all RSS feeds"""
        cursor = self.conn.cursor()
        if active_only:
            cursor.execute("SELECT * FROM feeds WHERE active = 1")
        else:
            cursor.execute("SELECT * FROM feeds")
        return cursor.fetchall()
    
    def delete_feed(self, feed_id):
        """Delete a feed and its news items"""
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM news_items WHERE feed_id = ?", (feed_id,))
        cursor.execute("DELETE FROM feeds WHERE id = ?", (feed_id,))
        self.conn.commit()
    
    # News methods
    def add_news_item(self, feed_id, title, link, description, summary, published):
        """Add a news item"""
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT OR IGNORE INTO news_items 
            (feed_id, title, link, description, summary, published) 
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (feed_id, title, link, description, summary, published))
        self.conn.commit()
        return cursor.lastrowid
    
    def get_news_items(self, limit=50):
        """Get recent news items with feed info"""
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT n.*, f.name as feed_name 
            FROM news_items n 
            JOIN feeds f ON n.feed_id = f.id 
            ORDER BY n.published DESC, n.created_at DESC 
            LIMIT ?
        ''', (limit,))
        return cursor.fetchall()
    
    def news_item_exists(self, feed_id, title, link):
        """Check if news item already exists"""
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT id FROM news_items 
            WHERE feed_id = ? AND (title = ? OR link = ?)
        ''', (feed_id, title, link))
        return cursor.fetchone() is not None
    
    def get_unsent_news_items(self, limit=10):
        """Get recent news items that haven't been sent to Discord"""
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT n.*, f.name as feed_name 
            FROM news_items n 
            JOIN feeds f ON n.feed_id = f.id 
            WHERE n.sent_to_discord = FALSE OR n.sent_to_discord IS NULL
            ORDER BY n.created_at DESC 
            LIMIT ?
        ''', (limit,))
        return cursor.fetchall()
    
    def mark_news_items_as_sent(self, news_item_ids):
        """Mark news items as sent to Discord"""
        cursor = self.conn.cursor()
        placeholders = ','.join(['?' for _ in news_item_ids])
        cursor.execute(f'''
            UPDATE news_items 
            SET sent_to_discord = TRUE, sent_at = CURRENT_TIMESTAMP 
            WHERE id IN ({placeholders})
        ''', news_item_ids)
        self.conn.commit()
    
    # Game methods
    def add_or_update_game(self, appid, name, platform, **kwargs):
        """Add or update a game, preserving completion status and game name"""
        cursor = self.conn.cursor()
        
        # Check if game exists by appid and platform
        cursor.execute("SELECT * FROM games WHERE appid = ? AND platform = ?", (appid, platform))
        existing = cursor.fetchone()
        
        if existing:
            # Update existing game but preserve user data and name
            preserved_fields = ['is_completed', 'name']  # Fields to preserve from existing record
            
            # Build update query excluding preserved fields
            update_fields = []
            update_values = []
            
            # Update other fields from kwargs, except preserved ones
            for key, value in kwargs.items():
                if key not in preserved_fields:
                    update_fields.append(f"{key} = ?")
                    update_values.append(value)
            
            # Add timestamp if we have fields to update
            if update_fields:
                update_fields.append("updated_at = CURRENT_TIMESTAMP")
                update_values.append(existing['id'])
                
                # Execute update
                update_query = f"UPDATE games SET {', '.join(update_fields)} WHERE id = ?"
                cursor.execute(update_query, update_values)
                self.conn.commit()
            
            return existing['id']
        else:
            # Insert new game
            columns = ["appid", "name", "platform"] + list(kwargs.keys())
            placeholders = ", ".join(["?"] * len(columns))
            values = [appid, name, platform] + list(kwargs.values())
            cursor.execute(f"INSERT INTO games ({', '.join(columns)}) VALUES ({placeholders})", values)
            
            self.conn.commit()
            return cursor.lastrowid
    
    def get_games(self, platform=None):
        """Get all games, optionally filtered by platform"""
        cursor = self.conn.cursor()
        if platform:
            cursor.execute("SELECT * FROM games WHERE platform = ? ORDER BY name", (platform,))
        else:
            cursor.execute("SELECT * FROM games ORDER BY name")
        return cursor.fetchall()
    
    def delete_all_games(self, platform=None):
        """Delete all games, optionally filtered by platform"""
        cursor = self.conn.cursor()
        if platform:
            cursor.execute("DELETE FROM games WHERE platform = ?", (platform,))
        else:
            cursor.execute("DELETE FROM games")
        self.conn.commit()
    
    def mark_game_completed(self, game_id, completed=True):
        """Mark a game as completed or incomplete"""
        cursor = self.conn.cursor()
        cursor.execute('''
            UPDATE games 
            SET is_completed = ?, updated_at = CURRENT_TIMESTAMP 
            WHERE id = ?
        ''', (completed, game_id))
        self.conn.commit()
    
    def get_games_by_completion(self, completed=False, platform=None):
        """Get games filtered by completion status"""
        cursor = self.conn.cursor()
        if platform:
            cursor.execute('''
                SELECT * FROM games 
                WHERE is_completed = ? AND platform = ? 
                ORDER BY name
            ''', (completed, platform))
        else:
            cursor.execute('''
                SELECT * FROM games 
                WHERE is_completed = ? 
                ORDER BY name
            ''', (completed,))
        return cursor.fetchall()
    
    def get_hundred_percent_games(self, platform=None):
        """Get games with 100% achievement completion"""
        cursor = self.conn.cursor()
        if platform:
            cursor.execute('''
                SELECT * FROM games 
                WHERE has_achievements = 1 
                AND achievements_total > 0 
                AND achievements_unlocked = achievements_total 
                AND platform = ?
                ORDER BY name
            ''', (platform,))
        else:
            cursor.execute('''
                SELECT * FROM games 
                WHERE has_achievements = 1 
                AND achievements_total > 0 
                AND achievements_unlocked = achievements_total
                ORDER BY name
            ''')
        return cursor.fetchall()
    
    # Task methods
    def add_task(self, title, description="", due_date=None, priority="Medium", recurrence=None):
        """Add a new task"""
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO tasks (title, description, due_date, priority, recurrence) 
            VALUES (?, ?, ?, ?, ?)
        ''', (title, description, due_date, priority, recurrence))
        self.conn.commit()
        return cursor.lastrowid
    
    def get_tasks(self, status=None):
        """Get tasks, optionally filtered by status"""
        cursor = self.conn.cursor()
        if status:
            cursor.execute("SELECT * FROM tasks WHERE status = ? ORDER BY due_date, priority", (status,))
        else:
            cursor.execute("SELECT * FROM tasks ORDER BY due_date, priority")
        return cursor.fetchall()
    
    def update_task(self, task_id, **kwargs):
        """Update a task"""
        cursor = self.conn.cursor()
        set_clause = ", ".join([f"{k} = ?" for k in kwargs.keys()] + ["updated_at = CURRENT_TIMESTAMP"])
        values = list(kwargs.values()) + [task_id]
        cursor.execute(f"UPDATE tasks SET {set_clause} WHERE id = ?", values)
        self.conn.commit()
    
    def complete_task(self, task_id):
        """Mark a task as completed"""
        cursor = self.conn.cursor()
        cursor.execute('''
            UPDATE tasks 
            SET status = 'Completed', completed_at = CURRENT_TIMESTAMP, updated_at = CURRENT_TIMESTAMP 
            WHERE id = ?
        ''', (task_id,))
        self.conn.commit()
    
    def delete_task(self, task_id):
        """Delete a task"""
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
        self.conn.commit()
    
    # API usage tracking methods
    def log_api_usage(self, api_name, model_name=None, request_type="generate", success=True, error_message=None):
        """Log API usage for quota tracking"""
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO api_usage (api_name, model_name, request_type, success, error_message) 
            VALUES (?, ?, ?, ?, ?)
        ''', (api_name, model_name, request_type, success, error_message))
        self.conn.commit()
    
    def get_api_usage_count(self, api_name, model_name=None, hours=24):
        """Get API usage count for the last N hours"""
        cursor = self.conn.cursor()
        if model_name:
            cursor.execute('''
                SELECT COUNT(*) FROM api_usage 
                WHERE api_name = ? AND model_name = ? 
                AND timestamp > datetime('now', '-{} hours')
                AND success = 1
            '''.format(hours), (api_name, model_name))
        else:
            cursor.execute('''
                SELECT COUNT(*) FROM api_usage 
                WHERE api_name = ? 
                AND timestamp > datetime('now', '-{} hours')
                AND success = 1
            '''.format(hours), (api_name,))
        
        result = cursor.fetchone()
        return result[0] if result else 0
    
    def get_api_usage_stats(self, api_name, model_name=None):
        """Get comprehensive API usage statistics"""
        cursor = self.conn.cursor()
        stats = {}
        
        # Usage in last hour, day, and total
        for period, hours in [("hour", 1), ("day", 24), ("total", 24*365)]:
            if model_name:
                cursor.execute('''
                    SELECT COUNT(*) FROM api_usage 
                    WHERE api_name = ? AND model_name = ? 
                    AND timestamp > datetime('now', '-{} hours')
                    AND success = 1
                '''.format(hours), (api_name, model_name))
            else:
                cursor.execute('''
                    SELECT COUNT(*) FROM api_usage 
                    WHERE api_name = ? 
                    AND timestamp > datetime('now', '-{} hours')
                    AND success = 1
                '''.format(hours), (api_name,))
            
            result = cursor.fetchone()
            stats[period] = result[0] if result else 0
        
        return stats
    
    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()