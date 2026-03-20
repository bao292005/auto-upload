import sqlite3
import hashlib
import logging
import datetime
import os

logger = logging.getLogger(__name__)

class DBManager:
    def __init__(self, db_path="history.sqlite"):
        self.db_path = db_path
        self.conn = None
        self._init_db()

    def _init_db(self):
        try:
            self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
            cursor = self.conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS uploaded_history (
                    hash_id TEXT PRIMARY KEY,
                    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            self.conn.commit()
            logger.info(f"Database initialized and connected at {self.db_path}")
        except sqlite3.Error as e:
            logger.error(f"Database initialization error: {e}")

    def close(self):
        if self.conn:
            self.conn.close()

    @staticmethod
    def get_file_hash(filepath: str) -> str:
        """Returns the SHA-256 hash of a file."""
        hasher = hashlib.sha256()
        try:
            with open(filepath, 'rb') as f:
                while chunk := f.read(8192):
                    hasher.update(chunk)
            return hasher.hexdigest()
        except Exception as e:
            logger.error(f"Failed to hash file {filepath}: {e}")
            return ""

    def is_uploaded(self, hash_id: str) -> bool:
        """Checks if a hash_id exists in the history."""
        if not hash_id or not self.conn:
            return False
            
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT 1 FROM uploaded_history WHERE hash_id = ?", (hash_id,))
            return bool(cursor.fetchone())
        except sqlite3.Error as e:
            logger.error(f"Database read error: {e}")
            return False

    def mark_success(self, hash_id: str):
        """Marks a file hash as successfully uploaded."""
        if not hash_id or not self.conn:
            return
            
        try:
            cursor = self.conn.cursor()
            cursor.execute(
                "INSERT OR IGNORE INTO uploaded_history (hash_id, uploaded_at) VALUES (?, ?)", 
                (hash_id, datetime.datetime.now())
            )
            self.conn.commit()
            logger.info(f"Successfully tracked upload for hash: {hash_id}")
        except sqlite3.Error as e:
            logger.error(f"Database write error: {e}")
