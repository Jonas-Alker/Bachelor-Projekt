import json
import sqlite3
import os
import shutil
import pandas as pd
import logging

#Getting Logger
logger = logging.getLogger(__name__)

class FactCheckManager:
    def __init__(self, version= "v1", mode="create", base_path="data/", source_path = None):
        """
        Initializes the FactCheckManager and establishes the database file path.

        :param version: The version string of the database (used in the filename).
        :param mode: Operation mode; "create" initializes a new DB, "load" expects an existing one
            and "copy" duplicates an existing database file to the new destination.
        :param base_path: The directory path where the database file will be stored.

        Raises:
            FileNotFoundError:  If mode is "load" but the database file does not exist,
                                or if mode is "copy" but the source_path file does not exist.
            ValueError:         If mode is "copy" but no source_path is provided.
        """
        self.db_path = os.path.join(base_path, f"factencheck_{version}.db")

        if mode == "load":
            if not os.path.exists(self.db_path):
                logger.critical(f"Version {version} of db file not found: {self.db_path}")
                raise FileNotFoundError(f"Version {version} of db file not found: {self.db_path}")

        elif mode == "copy":
            if not source_path:
                logger.critical("source_path must be provided when mode is 'copy'")
                raise ValueError("source_path must be provided when mode is 'copy'")
            if not os.path.exists(source_path):
                logger.critical(f"Source database file not found: {source_path}")
                raise FileNotFoundError(f"Source database file not found: {source_path}")
            if not os.path.exists(base_path):
                os.makedirs(base_path)
            shutil.copy2(source_path, self.db_path)

        else: # mode == "create"
            if not os.path.exists(base_path):
                os.makedirs(base_path)
            self._setup_db()

    def _get_connection(self):
        """
        Creates and returns a connection to the SQLite database.
        Configures the row factory to `sqlite3.Row` to allow fetching rows
        as dictionary-like objects accessible by column names.

        :return: An active sqlite3.Connection object.
        """
        conn = sqlite3.connect(self.db_path, timeout = 30)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON;")
        return conn

    def _setup_db(self):
        """
        Initializes the database schema by creating the required tables.

        Warning:
            This method drops all the existing tables and clears all
            previously stored data.
        """
        with self._get_connection() as conn:
            # 0. Dropping Tables
            conn.execute("PRAGMA foreign_keys = OFF")
            conn.execute("DROP TABLE IF EXISTS portals")
            conn.execute("DROP TABLE IF EXISTS claim_reviews")
            conn.execute("DROP TABLE IF EXISTS claims")
            conn.execute("DROP TABLE IF EXISTS claim_ratings")
            conn.execute("PRAGMA foreign_keys = ON")

            # 1. Portal
            conn.execute("""
                CREATE TABLE IF NOT EXISTS portals
                (
                    id          INTEGER PRIMARY KEY AUTOINCREMENT,
                    portal_name TEXT UNIQUE,
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
                    article_author  TEXT,
                    published_at DATE,
                    article_url TEXT UNIQUE,
                    language    TEXT,
                    FOREIGN KEY (portal_id) REFERENCES portals (id)
                )""")

            # 3. claims
            conn.execute("""
                CREATE TABLE IF NOT EXISTS claims
                (
                    id          INTEGER PRIMARY KEY AUTOINCREMENT,
                    claim       TEXT UNIQUE,
                    claim_author      TEXT,
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
        Adds a fact check to the database. First, it checks whether `claims_data` is a valid JSON object.
        If this is not the case, it attempts to repair it; otherwise, a warning is issued and the process is skipped.

        :param portal_name: name of the portal
        :param portal_url: url of the portal
        :param factcheck_url: url of the fact check
        :param claims_data: claims data, which contains all the extracted data and conforms to the defined JSON format
        """
        if isinstance(claims_data, str):
            claims_data = json.loads(claims_data)

        # Case A: The LLM has accidentally created nested lists: [[{...}]]
        if isinstance(claims_data, list) and len(claims_data) > 0 and isinstance(claims_data[0], list):
            claims_data = claims_data[0]

        # Case B: The LLM has provided just a single dictionary instead of a list: {...}
        elif isinstance(claims_data, dict):
            claims_data = [claims_data]

        # Case C: Handling empty data or a completely corrupted format
        if not claims_data or not isinstance(claims_data, list):
            logger.error(f"Error: Invalid data format for {factcheck_url}. Skipping entry.")
            return

        with self._get_connection() as conn:

            #Portal
            conn.execute("INSERT OR IGNORE INTO portals (portal_name, portal_url) VALUES (?, ?)", (portal_name,portal_url))
            portal_id = conn.execute("SELECT id FROM portals WHERE portal_name = ?", (portal_name,)).fetchone()[0]

            for claim in claims_data:  #Loop due to possible multiple entries in ‘claims_data’

                #Review
                conn.execute("INSERT OR IGNORE INTO claim_reviews (portal_id, headline, body, article_author, published_at, article_url ,language) "
                             "VALUES (?, ?, ?, ?, ?, ?, ?)",
                             (portal_id, claim["headline"], claim["body"], claim["author_factcheck"],
                                        claim["published_at"],factcheck_url, claim["language"]))
                review_id = conn.execute("SELECT id FROM claim_reviews WHERE  article_url = ?", (factcheck_url,)).fetchone()[0]

                #Claim
                conn.execute(
                    "INSERT OR IGNORE INTO claims (claim, claim_author, stated_at) VALUES (?, ?, ?)",
                    (claim["claim"], claim["author_claim"], claim["stated_at"]))
                claim_id = conn.execute("SELECT id FROM claims WHERE claim IS ? AND claim_author IS ?",
                                        (claim["claim"], claim["author_claim"])).fetchone()[0]

                #claim_ratings
                conn.execute("""INSERT OR IGNORE INTO  claim_ratings (claim_review_id, claim_id, rating_original)
                                    VALUES (?, ?, ?)""",
                                 (review_id, claim_id, claim["original_rating"]))
                conn.commit()
    def get_as_pd(self):
        """

        :return:
        """
        with self._get_connection() as conn:
            return pd.read_sql_query("""SELECT *
                                      FROM portals
                                               JOIN claim_reviews ON portals.id = claim_reviews.portal_id
                                               JOIN
                                           claim_ratings ON claim_ratings.claim_review_id = claim_reviews.id
                                               JOIN
                                           claims ON claims.id = claim_ratings.claim_id """, conn)

    def export_as_csv(self,path):
        """
        Exports the joined tables from the database as a CSV file

        :param path: path where the CSV file will be saved
        """
        with self._get_connection() as conn:
            df = pd.read_sql_query("""SELECT * FROM portals JOIN claim_reviews ON portals.id = claim_reviews.portal_id JOIN
                                    claim_ratings ON claim_ratings.claim_review_id = claim_reviews.id  JOIN
                                    claims ON claims.id = claim_ratings.claim_id """, conn)
            df.to_csv(path, index=False)