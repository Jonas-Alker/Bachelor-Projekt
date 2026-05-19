import sqlite3
import os
import shutil

class DBManager:
    def __init__(self, version= "v1", mode="create", base_path="data/raw/", source_path = None):
        """Initializes the DBManager and establishes the database file path.

        :param version: The version string of the database (used in the filename).
        :param mode: Operation mode; "create" initializes a new DB, "load" expects an existing one
            and "copy" duplicates an existing database file to the new destination.
        :param base_path: The directory path where the database file will be stored.

        Raises:
            FileNotFoundError: If mode is "load" but the database file does not exist,
                or if mode is "copy" but the source_path file does not exist.
            ValueError: If mode is "copy" but no source_path is provided.
        """
        self.db_path = os.path.join(base_path, f"factencheck_{version}.db")

        if mode == "load":
            if not os.path.exists(self.db_path):
                raise FileNotFoundError(f"Version {version} of db file not found: {self.db_path}")

        elif mode == "copy":
            if not source_path:
                raise ValueError("source_path must be provided when mode is 'copy'")
            if not os.path.exists(source_path):
                raise FileNotFoundError(f"Source database file not found: {source_path}")
            if not os.path.exists(base_path):
                os.makedirs(base_path)
            shutil.copy2(source_path, self.db_path)

        else: # mode == "create"
            if not os.path.exists(base_path):
                os.makedirs(base_path)
            self._setup_db()

    def _get_connection(self):
        """Creates and returns a connection to the SQLite database.
        Configures the row factory to `sqlite3.Row` to allow fetching rows
        as dictionary-like objects accessible by column names.

        :return: An active sqlite3.Connection object.
        """
        conn = sqlite3.connect(self.db_path, timeout = 30)
        conn.row_factory = sqlite3.Row
        return conn

    def _setup_db(self):
        """Initializes the database schema by creating the required tables.

        Warning:
            This method drops the existing 'web_cache' table and clears all
            previously stored data if it already exists.
        """
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
        """Retrieves the complete cache record for a specific URL.

        param url: The URL of the webpage to search in the database.

        :return: A dictionary containing 'portal', 'html_content', and 'crawled_at' if the URL exists; None otherwise.
        """
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
        """Saves or updates the HTML content of a URL in the database.

        :param url: The URL of the webpage (serves as the Primary Key).
        :param portal: The name of the web portal
        :param html_content: The raw HTML string content to cache.
        """
        try:
            with self._get_connection() as conn:
                conn.execute("""
                    INSERT OR REPLACE INTO web_cache (url, portal, html_content) VALUES (?, ?, ?)""", (url, portal, html_content))
                conn.commit()
        except sqlite3.Error as e:
            print(f"Error: {e}")

    def get_urls_by_portal(self, portal):
        """Fetches all cached URLs associated with a specific portal.

        :param portal: The name of the portal to filter by.
        :return: A list of URLs (strings) belonging to the specified portal.
        """
        with self._get_connection() as conn:
            cursor = conn.execute("SELECT url FROM web_cache WHERE portal = ?", (portal,))
            urls = [row[0] for row in cursor.fetchall()]
            return urls

    def delete_url(self, url):
        """Deletes the URL associated with a specific portal.

        :param url: The URL of the website entry to be deleted.
        """
        try:
            with self._get_connection() as conn:
                conn.execute("DELETE FROM web_cache WHERE url = ?", (url,))
                conn.commit()
        except sqlite3.Error as e:
            print(f"Error: {e}")

    def delete_urls_bulk(self, url_list):
        """Efficiently deletes a list of URLs in a single transaction.

        :param url_list: A list of URL strings
        """
        if not url_list:
            return

        formatted_data = [(url,) for url in url_list]

        try:
            with self._get_connection() as conn:
                conn.executemany("DELETE FROM web_cache WHERE url = ?", formatted_data)
                conn.commit()
        except sqlite3.Error as e:
            print(f"Error: {e}")