import sqlite3
import os
import shutil
import logging

#Getting Logger
logger = logging.getLogger(__name__)

class HTMLCacheManager:
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
        self.db_path = os.path.join(base_path, f"html_raw_{version}.db")

        logger.debug(f"Initializing HTMLCacheManager in '{mode}' mode (version: {version})")
        if mode == "load":
            if not os.path.exists(self.db_path):
                logger.error(f"Version {version} of db file not found: {self.db_path}")
                raise FileNotFoundError(f"Version {version} of db file not found: {self.db_path}")

        elif mode == "copy":
            if not source_path:
                logger.error("source_path must be provided when mode is 'copy'")
                raise ValueError("source_path must be provided when mode is 'copy'")
            if not os.path.exists(source_path):
                logger.error(f"Source database file not found: {source_path}")
                raise FileNotFoundError(f"Source database file not found: {source_path}")
            if not os.path.exists(base_path):
                os.makedirs(base_path)
            shutil.copy2(source_path, self.db_path)
            logger.debug(f"Successfully copied database from {source_path} to {self.db_path}")

        else: # mode == "create"
            if not os.path.exists(base_path):
                os.makedirs(base_path)
            self._setup_db()
        self._ensure_indexes()

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
                portal_url TEXT,
                portal TEXT,
                html_content TEXT,
                crawled_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
            """)
            conn.commit()
            logger.debug("Database schema (web_cache) setup complete.")

    def _ensure_indexes(self):
        """Ensures that the indexes exist in the database."""
        with self._get_connection() as conn:
            conn.execute("CREATE INDEX IF NOT EXISTS idx_crawled_at ON web_cache(crawled_at)")
            conn.commit()
            logger.debug("Database indexes ensured.")

    def get_full_entry(self, url):
        """Retrieves the complete cache record for a specific URL.

        param url: The URL of the webpage to search in the database.

        :return: A dictionary containing 'portal', 'html_content', and 'crawled_at' if the URL exists; None otherwise.
        """
        with self._get_connection() as conn:
            cursor = conn.execute(
                "SELECT portal, portal_url, html_content, crawled_at FROM web_cache WHERE url = ?", (url,))
            row = cursor.fetchone()

            if row:
                return{
                    "portal": row["portal"],
                    "portal_url": row["portal_url"],
                    "html_content": row["html_content"],
                    "crawled_at": row["crawled_at"]
                }
            return None

    def save_html(self, url, portal, portal_url, html_content):
        """Saves or updates the HTML content of a URL in the database.

        :param url: The URL of the webpage (serves as the Primary Key).
        :param portal: The name of the web portal
        :param portal_url: The URL of the web portal (domain)
        :param html_content: The raw HTML string content to cache.
        """
        try:
            with self._get_connection() as conn:
                conn.execute("""
                    INSERT OR REPLACE INTO web_cache (url, portal, portal_url, html_content) VALUES (?, ?, ?, ?)""",
                             (url, portal, portal_url, html_content))
                conn.commit()
        except sqlite3.Error as e:
            logger.error(f"SQLite error saving URL {url}: {e}")

    def get_urls_by_portal(self, portal):
        """Fetches all cached URLs associated with a specific portal.

        :param portal: The name of the portal to filter by.
        :return: A list of URLs (strings) belonging to the specified portal.
        """
        with self._get_connection() as conn:
            cursor = conn.execute("SELECT url FROM web_cache WHERE portal = ?", (portal,))
            urls = [row[0] for row in cursor.fetchall()]
            logger.debug(f"Fetched {len(urls)} URLs for portal '{portal}'.")
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
            logger.error(f"SQLite error deleting URL {url}: {e}")

    def delete_urls_bulk(self, url_list):
        """Efficiently deletes a list of URLs in a single transaction.

        :param url_list: A list of URL strings
        """
        if not url_list:
            return

        logger.debug(f"Executing bulk deletion for {len(url_list)} URLs.")
        formatted_data = [(url,) for url in url_list]

        try:
            with self._get_connection() as conn:
                conn.executemany("DELETE FROM web_cache WHERE url = ?", formatted_data)
                conn.commit()
        except sqlite3.Error as e:
            logger.error(f"SQLite error in bulk deletion: {e}")

    def pop_next_page(self):
        with self._get_connection() as conn:
            row = conn.execute("""
                SELECT url, portal, portal_url, html_content
                FROM web_cache
                ORDER BY crawled_at ASC LIMIT 1
            """).fetchone()
            if row:
                page = dict(row)
                conn.execute("DELETE FROM web_cache WHERE url = ?", (page['url'],))
                conn.commit()
                logger.debug(f"Popped next page from queue: {page['url']}")
                return page
            return None