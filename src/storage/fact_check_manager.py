import sqlite3
import os
import shutil

class FactCheckManager:
    def __init__(self, version= "v1", mode="create", base_path="data/", source_path = None):
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
        conn.execute("PRAGMA foreign_keys = ON;")
        return conn

    def _setup_db(self):
        """Initializes the database schema by creating the required tables.

        Warning:
            This method drops the existing 'web_cache' table and clears all
            previously stored data if it already exists.
        """
        with self._get_connection() as conn:
            # 1. Portal
            conn.execute("""
                CREATE TABLE IF NOT EXISTS portals
                (
                    id          INTEGER PRIMARY KEY AUTOINCREMENT,
                    name        TEXT UNIQUE,
                    portal_url  TEXT UNIQUE
                )""")

            # 2. claim_reviews
            conn.execute("""
                CREATE TABLE IF NOT EXISTS claim_reviews
                (
                    id          INTEGER PRIMARY KEY AUTOINCREMENT,
                    portal_id   INTEGER,
                    headline    TEXT,
                    body        TEXT,
                    author      TEXT,
                    published   DATE,
                    url         TEXT UNIQUE,
                    language    TEXT,
                    FOREIGN KEY (portal_id) REFERENCES portals (id)
                )""")

            # 3. claims
            conn.execute("""
                CREATE TABLE IF NOT EXISTS claims
                (
                    id          INTEGER PRIMARY KEY AUTOINCREMENT,
                    claim       TEXT UNIQUE,
                    author      TEXT,
                    stated_at   DATE
                    
                )""")

            # 4. claim_ratings
            conn.execute("""
                CREATE TABLE IF NOT EXISTS claim_ratings
                (
                    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
                    claim_review_id     INTEGER,
                    claim_id            INTEGER,
                    rating_original     TEXT,
                    FOREIGN KEY (claim_review_id) REFERENCES claim_reviews (id),
                    FOREIGN KEY (claim_id) REFERENCES claims (id)
                )""")
            conn.commit()

    def add_fact_check(self, portal_name, portal_url, factcheck_url, claims_data):
        """
        :param
        """
        with self._get_connection() as conn:
            #Portal
            conn.execute("INSERT OR IGNORE INTO portals (name, portal_url) VALUES (?, ?)", (portal_name,portal_url))
            portal_id = conn.execute("SELECT id FROM sources WHERE name = ?", (portal_name,)).fetchone()[0]

            #Because of possible multiple claims in claims_data
            for claim in claims_data:

                #Review
                conn.execute("INSERT OR IGNORE INTO claim_reviews (portal_id, headline, body, author, published, url) VALUES (?, ?, ?, ?, ?,?)",
                             (portal_id, claim["headline"], claim["body"], claim["author"],
                                        claim["published_at"],factcheck_url))
                review_id = conn.execute("SELECT id FROM claim_reviews WHERE url = ?", (factcheck_url,)).fetchone()[0]

                #Claim
                conn.execute(
                    "INSERT OR IGNORE INTO claims (claim, author, stated_at) VALUES (?, ?, ?)",
                    (claim["claim"], claim["claim_author"], claim["stated_at"]))
                claim_id = conn.execute("SELECT id FROM claims WHERE claim = ? AND author = ?",
                                        (claim["claim"], claim["claim_author"])).fetchone()[0]

                #claim_ratings
                conn.execute("""INSERT INTO claim_ratings (claim_review_id, claim_id, rating_original)
                                    VALUES (?, ?, ?)""",
                                 (review_id, claim_id, claim["rating"]))
                conn.commit()