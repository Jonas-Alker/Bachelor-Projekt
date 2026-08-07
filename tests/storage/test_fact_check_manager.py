import os
import json
import sqlite3
import pytest
import pandas as pd
from unittest.mock import patch, MagicMock
from src.storage.fact_check_manager import FactCheckManager


DUMMY_CLAIM = {
    "headline": "Test Headline",
    "body": "Test Body",
    "author_factcheck": "FactChecker",
    "published_at": "01.01.2026",
    "language": "en",
    "claim": "Test Claim",
    "author_claim": "ClaimAuthor",
    "stated_at": "01.12.2025",
    "original_rating": "False"
}


@pytest.fixture(autouse=True)
def mock_debug_logger():
    """Globally mocks the debug logger for all tests to keep the console output clean."""
    with patch('src.storage.fact_check_manager.logger.debug') as mock_debug:
        yield mock_debug

@pytest.fixture(autouse=True)
def mock_info_logger():
    """Globally mocks the debug logger for all tests to keep the console output clean."""
    with patch('src.storage.fact_check_manager.logger.info') as mock_info:
        yield mock_info


@pytest.fixture
def db(tmp_path):
    """Provides a fresh, temporary database instance for testing."""
    manager = FactCheckManager(version="test_v1", mode="create", base_path=str(tmp_path))
    yield manager
    del manager


# Initialization & File Mode Tests


def test_load_existing_db(db):
    """Tests if the manager can successfully load an existing database file."""
    db_path = db.db_path
    base_path = os.path.dirname(db_path)

    # Insert a dummy entry so the DB is not completely empty
    db.add_fact_check("Portal", "https://portal.com", "https://portal.com/fc", [DUMMY_CLAIM])

    try:
        loader = FactCheckManager(version="test_v1", mode="load", base_path=base_path)
        assert loader.db_path == db_path
        # Verify data is still accessible
        df = loader.get_as_pd()
        assert not df.empty
    except FileNotFoundError:
        pytest.fail("FactCheckManager did not load properly!")


@patch('src.storage.fact_check_manager.logger.error')
def test_load_non_existing_db(mock_error):
    """Tests if attempting to load a missing database raises a FileNotFoundError and logs an error."""
    with pytest.raises(FileNotFoundError) as excinfo:
        FactCheckManager(version="not-here", mode="load", base_path="tests/test_data/factchecks")

    assert "of db file not found:" in str(excinfo.value)
    mock_error.assert_called_once()
    assert "db file not found" in mock_error.call_args[0][0]


@patch('src.storage.fact_check_manager.logger.error')
def test_copy_missing_source_path(mock_error):
    """Tests if initializing in 'copy' mode without a source_path raises a ValueError and logs it."""
    with pytest.raises(ValueError, match="source_path must be provided when mode is 'copy'"):
        FactCheckManager(version="test_v1", mode="copy", base_path="tests/test_data/factchecks")

    mock_error.assert_called_once()
    assert "source_path must be provided" in mock_error.call_args[0][0]


@patch('src.storage.fact_check_manager.logger.error')
def test_copy_source_file_not_found(mock_error):
    """Tests if providing an invalid source file in 'copy' mode raises a FileNotFoundError and logs it."""
    with pytest.raises(FileNotFoundError, match="Source database file not found"):
        FactCheckManager(version="test_v1", mode="copy", base_path="tests/test_data/factchecks",
                         source_path="does_not_exist.db")

    mock_error.assert_called_once()
    assert "Source database file not found" in mock_error.call_args[0][0]


# Add Fact Check (Data Normalization) Tests


def test_add_valid_fact_check_list(db, mock_debug_logger):
    """Tests if a valid list of claim dictionaries is successfully saved."""
    mock_debug_logger.reset_mock()
    db.add_fact_check("Portal", "https://portal.com", "https://portal.com/fc", [DUMMY_CLAIM])

    df = db.get_as_pd()
    assert len(df) == 1
    assert df.iloc[0]["headline"] == "Test Headline"

    mock_debug_logger.assert_called_once()
    assert "Successfully saved 1 claim(s)" in mock_debug_logger.call_args[0][0]


def test_add_valid_fact_check_json_string(db):
    """Tests if a valid JSON string is correctly parsed and saved."""
    json_str = json.dumps([DUMMY_CLAIM])
    db.add_fact_check("Portal", "https://portal.com", "https://portal.com/fc", json_str)

    df = db.get_as_pd()
    assert len(df) == 1
    assert df.iloc[0]["claim"] == "Test Claim"


def test_add_fact_check_nested_list(db):
    """Tests if deeply nested lists (hallucinated by LLMs) are gracefully flattened."""
    nested_data = [[DUMMY_CLAIM]]
    db.add_fact_check("Portal", "https://portal.com", "https://portal.com/fc", nested_data)

    df = db.get_as_pd()
    assert len(df) == 1


def test_add_fact_check_single_dict(db):
    """Tests if a single dictionary (instead of a list) is gracefully wrapped into a list."""
    db.add_fact_check("Portal", "https://portal.com", "https://portal.com/fc", DUMMY_CLAIM)

    df = db.get_as_pd()
    assert len(df) == 1


@patch('src.storage.fact_check_manager.logger.error')
def test_add_invalid_json_string(mock_error, db):
    """Tests if an invalid JSON string is caught and logged."""
    db.add_fact_check("Portal", "https://portal.com", "https://portal.com/fc", "{broken_json: true")

    mock_error.assert_called_once()
    assert "Invalid JSON string" in mock_error.call_args[0][0]


@patch('src.storage.fact_check_manager.logger.error')
def test_add_invalid_data_format(mock_error, db):
    """Tests if completely unsupported data types (like None or integers) are rejected and logged."""
    db.add_fact_check("Portal", "https://portal.com", "https://portal.com/fc", None)

    mock_error.assert_called_once()
    assert "Invalid data format" in mock_error.call_args[0][0]


# Export and Data Retrieval Tests


def test_get_as_pd(db):
    """Tests if the database content is correctly joined and returned as a pandas DataFrame."""
    db.add_fact_check("Portal1", "https://portal1.com", "https://portal1.com/fc1", DUMMY_CLAIM)
    db.add_fact_check("Portal2", "https://portal2.com", "https://portal2.com/fc2", DUMMY_CLAIM)

    df = db.get_as_pd()
    assert isinstance(df, pd.DataFrame)
    assert len(df) == 2
    assert "portal_name" in df.columns
    assert "headline" in df.columns
    assert "rating_original" in df.columns


def test_export_as_csv(db, tmp_path, mock_info_logger):
    """Tests if the database content is correctly exported to a CSV file."""
    db.add_fact_check("Portal", "https://portal.com", "https://portal.com/fc", DUMMY_CLAIM)

    csv_path = tmp_path / "export.csv"
    mock_info_logger.reset_mock()

    db.export_as_csv(str(csv_path))

    assert os.path.exists(csv_path)
    exported_df = pd.read_csv(csv_path)
    assert len(exported_df) == 1
    assert exported_df.iloc[0]["portal_name"] == "Portal"

    mock_info_logger.assert_called_once()
    assert "Successfully exported data to CSV" in mock_info_logger.call_args[0][0]


# Exception Handling Tests (SQLite & Pandas)


@patch('src.storage.fact_check_manager.logger.error')
@patch('src.storage.fact_check_manager.sqlite3.connect')
def test_add_fact_check_sqlite_error(mock_connect, mock_error, db):
    """Tests if an SQLite error during data insertion is caught and logged as an error."""
    mock_conn = MagicMock()
    mock_conn.__enter__.return_value = mock_conn
    mock_conn.execute.side_effect = sqlite3.Error("Database locked")
    mock_connect.return_value = mock_conn

    db.add_fact_check("Portal", "https://portal.com", "https://portal.com/fc", DUMMY_CLAIM)

    mock_error.assert_called_once()
    assert "SQLite error saving fact check" in mock_error.call_args[0][0]


@patch('src.storage.fact_check_manager.logger.error')
@patch('src.storage.fact_check_manager.pd.read_sql_query')
def test_get_as_pd_error(mock_read_sql, mock_error, db):
    """Tests if a failure during pandas SQL reading is caught and returns an empty DataFrame."""
    mock_read_sql.side_effect = Exception("Pandas conversion failed")

    df = db.get_as_pd()

    assert isinstance(df, pd.DataFrame)
    assert df.empty
    mock_error.assert_called_once()
    assert "Error fetching data to pandas DataFrame" in mock_error.call_args[0][0]


@patch('src.storage.fact_check_manager.logger.error')
@patch('src.storage.fact_check_manager.pd.read_sql_query')
def test_export_as_csv_error(mock_read_sql, mock_error, db):
    """Tests if a failure during CSV export is safely caught and logged."""
    mock_read_sql.side_effect = Exception("Disk full")

    db.export_as_csv("dummy/path.csv")

    mock_error.assert_called_once()
    assert "Error exporting data to CSV" in mock_error.call_args[0][0]


def test_get_rdf_export_data_success(db):
    """Tests if get_rdf_export_data correctly returns the joined data with aliased IDs."""
    db.add_fact_check("Portal", "https://portal.com", "https://portal.com/fc", DUMMY_CLAIM)

    df = db.get_rdf_export_data()

    assert isinstance(df, pd.DataFrame)
    assert len(df) == 1

    expected_columns = [
        'review_id', 'headline', 'body', 'article_author', 'published_at',
        'article_url', 'language', 'claim_id', 'claim', 'claim_author',
        'stated_at', 'portal_id', 'portal_name', 'portal_url', 'rating_original'
    ]
    for col in expected_columns:
        assert col in df.columns, f"Spalte '{col}' fehlt im DataFrame für den RDF-Export."

    assert df.iloc[0]["portal_name"] == "Portal"
    assert df.iloc[0]["claim"] == "Test Claim"
    assert df.iloc[0]["rating_original"] == "False"


@patch('src.storage.fact_check_manager.logger.error')
@patch('src.storage.fact_check_manager.pd.read_sql_query')
def test_get_rdf_export_data_error(mock_read_sql, mock_error, db):
    """Tests if a failure during fetching RDF export data is safely caught, logged, and returns an empty DataFrame."""
    mock_read_sql.side_effect = Exception("Database read error")

    df = db.get_rdf_export_data()

    assert isinstance(df, pd.DataFrame)
    assert df.empty
    mock_error.assert_called_once()
    assert "Error fetching data for RDF export" in mock_error.call_args[0][0]


def test_claim_deduplication_logic(db):
    """Tests if identical claims from different articles are deduplicated correctly in the database."""

    db.add_fact_check("Portal1", "https://portal1.com", "https://portal1.com/fc1", [DUMMY_CLAIM])

    db.add_fact_check("Portal2", "https://portal2.com", "https://portal2.com/fc2", [DUMMY_CLAIM])

    with db._get_connection() as conn:
        claims_count = conn.execute("SELECT COUNT(*) FROM claims").fetchone()[0]
        reviews_count = conn.execute("SELECT COUNT(*) FROM claim_reviews").fetchone()[0]
        ratings_count = conn.execute("SELECT COUNT(*) FROM claim_ratings").fetchone()[0]

        assert claims_count == 1
        assert reviews_count == 2
        assert ratings_count == 2
        claim_ids = conn.execute("SELECT claim_id FROM claim_ratings").fetchall()
        assert claim_ids[0]['claim_id'] == claim_ids[1]['claim_id']

    df = db.get_as_pd()
    assert len(df) == 2


def test_get_existing_article_urls_success(db):
    """Tests if the method correctly retrieves all unique article URLs from the database."""
    urls_empty = db.get_existing_article_urls()
    assert isinstance(urls_empty, list)
    assert len(urls_empty) == 0

    db.add_fact_check("Portal1", "https://portal1.com", "https://portal1.com/fc1", [DUMMY_CLAIM])
    db.add_fact_check("Portal2", "https://portal2.com", "https://portal2.com/fc2", [DUMMY_CLAIM])

    urls = db.get_existing_article_urls()

    assert len(urls) == 2
    assert "https://portal1.com/fc1" in urls
    assert "https://portal2.com/fc2" in urls


@patch('src.storage.fact_check_manager.logger.error')
def test_get_existing_article_urls_error(mock_error, db):
    """Tests if database errors during URL retrieval are caught and return an empty list."""
    with patch.object(db, '_get_connection', side_effect=Exception("Database connection failed")):
        urls = db.get_existing_article_urls()

        assert isinstance(urls, list)
        assert len(urls) == 0
        mock_error.assert_called_once()
        assert "Error fetching existing URLs" in mock_error.call_args[0][0]