import sqlite3
from datetime import datetime
from venv import create
import os


class DBManager:
    def __init__(self, version= "v1", mode="create", base_path="data/raw/"):
        self.db_path = os.path.join(base_path, f"factencheck_{version}.db")

        if mode == "load":
            if not os.path.exists(self.db_path):
                raise FileNotFoundError(f"Version {version} of db file not found: {self.db_path}")

        else: # mode == "create"
            if not os.path.exists(base_path):
                os.makedirs(base_path)
            self._setup_db()

    def _get_connection(self):
        conn = sqlite3.connect(self.db_path, timeout = 30)
        conn.row_factory = sqlite3.Row
        return conn

    def _setup_db(self):
        with self._get_connection() as conn:
            conn.execute("DROP TABLE IF EXISTS web_cache")
            conn.execute("""
            CREATE TABLE web_cache (
                url TEXT PRIMARY KEY,
                portal TEXT,
                html_content TEXT,
                crawled_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
            """)
            conn.commit()

    def get_full_entry(self, url):
        with self._get_connection() as conn:
            cursor = conn.execute("SELECT portal, html_content, crawled_at FROM web_cache WHERE url = ?", (url,))
            row = cursor.fetchone()

            if row:
                return{
                    "portal": row["portal"],
                    "html_content": row["html_content"],
                    "crawled_at": row["crawled_at"]
                }
            return None

    def save_html(self, url, portal, html_content):
        try:
            with self._get_connection() as conn:
                conn.execute("""
                    INSERT OR REPLACE INTO web_cache (url, portal, html_content) VALUES (?, ?, ?)""", (url, portal, html_content))
                conn.commit()
        except sqlite3.Error as e:
            print(f"Error: {e}")

    def get_urls_by_portal(self, portal):
        with self._get_connection() as conn:
            cursor = conn.execute("SELECT url FROM web_cache WHERE portal = ?", (portal,))
            urls = [row[0] for row in cursor.fetchall()]
            return urls
