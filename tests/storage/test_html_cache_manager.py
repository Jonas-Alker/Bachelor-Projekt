import os
import sqlite3
from unittest.mock import patch, MagicMock
from src.storage.html_cache_manager import HTMLCacheManager
import pytest

@pytest.fixture(autouse=True)
def mock_debug_logger():
    """Globally mocks the debug logger for all tests to keep the console output clean."""
    with patch('src.storage.html_cache_manager.logger.debug') as mock_debug:
        yield mock_debug

@pytest.fixture
def db():
    """Provides a fresh, temporary database instance for testing."""
    test_db_path = "tests/test_data/raw"
    manager = HTMLCacheManager(version="test_v1", mode= "create",base_path=test_db_path)
    db_file_path = manager.db_path

    yield manager
    del manager
    if os.path.exists(db_file_path):
        try:
            os.remove(db_file_path)
        except PermissionError as e:
            print(f"Error: {e}")

def test_save_and_get_html(db):
    """Tests if an HTML entry can be successfully saved and subsequently retrieved."""
    url = "https://www.test.com/test"
    portal_name = "TestPortal"
    portal_url = "https://www.test.com"
    content = "<html> Test </html>"

    db.save_html(url,portal_name,portal_url,content)
    result = db.get_full_entry(url)

    assert result is not None
    assert result["portal"] == portal_name
    assert result["html_content"] == content
    assert result["portal_url"] == portal_url

def test_get_non_existing_entry(db):
    """Tests if querying a non-existent URL correctly returns None."""
    result = db.get_full_entry("https://www.not-here.com")
    assert result is None

def test_get_urls_by_portal(db):
    """Tests if URLs can be correctly filtered and retrieved by their portal name."""
    test_data = [
        ("https://www.test1.com/test", "TestPortal_A","https://www.test1.com/", "conntent 1"),
        ("https://www.test2.com/test", "TestPortal_A", "https://www.test2.com/", "conntent 2"),
        ("https://www.test3.com/test", "TestPortal_B", "https://www.test3.com/", "conntent 3"),
    ]

    for url, portal, portal_url, content in test_data:
        db.save_html(url, portal, portal_url, content)

    urls_a = db.get_urls_by_portal("TestPortal_A")
    assert len(urls_a) == 2
    assert "https://www.test1.com/test" in urls_a
    assert "https://www.test2.com/test" in urls_a
    assert "https://www.test3.com/test" not in urls_a

# Initialization & File Mode Tests

def test_load_existing_db(db):
    """Tests if the manager can successfully load an existing database file."""
    db_path = db.db_path
    base_path = os.path.dirname(db_path)

    url = "https://www.test.com/test"
    db.save_html(url, "TestPortal", "https://www.test.com", "<html> Test </html>")

    try:
        loader = HTMLCacheManager(version="test_v1", mode="load", base_path=base_path)
        assert loader.db_path == db_path
        assert loader.get_full_entry(url) is not None
    except FileNotFoundError:
        pytest.fail("DBManager did not load properly!")


@patch('src.storage.html_cache_manager.logger.error')
def test_load_non_existing_db(mock_error):
    """Tests if attempting to load a missing database raises a FileNotFoundError and logs an error."""
    with pytest.raises(FileNotFoundError) as excinfo:
        HTMLCacheManager(version="not-here", mode="load", base_path="tests/test_data/raw")

    assert "of db file not found:" in str(excinfo.value)
    mock_error.assert_called_once()
    assert "db file not found" in mock_error.call_args[0][0]


@patch('src.storage.html_cache_manager.logger.error')
def test_copy_missing_source_path(mock_error):
    """Tests if initializing in 'copy' mode without a source_path raises a ValueError and logs it."""
    with pytest.raises(ValueError, match="source_path must be provided when mode is 'copy'"):
        HTMLCacheManager(version="test_v1", mode="copy", base_path="tests/test_data/raw")

    mock_error.assert_called_once()
    assert "source_path must be provided" in mock_error.call_args[0][0]


@patch('src.storage.html_cache_manager.logger.error')
def test_copy_source_file_not_found(mock_error):
    """Tests if providing an invalid source file in 'copy' mode raises a FileNotFoundError and logs it."""
    with pytest.raises(FileNotFoundError, match="Source database file not found"):
        HTMLCacheManager(version="test_v1", mode="copy", base_path="tests/test_data/raw",
                         source_path="does_not_exist.db")

    mock_error.assert_called_once()
    assert "Source database file not found" in mock_error.call_args[0][0]

# Deletion Tests

def test_delete_url(db):
    """Tests if a single URL entry is successfully deleted from the database."""
    url_to_delete = "https://www.test1.com/test"
    url_to_keep = "https://www.test2.com/test"
    portal = "TestPortal"
    portal_url = "https://www.test.com"
    content = "<html>Test</html>"

    db.save_html(url_to_delete, portal, portal_url, content)
    db.save_html(url_to_keep, portal, portal_url, content)
    db.delete_url(url_to_delete)

    assert db.get_full_entry(url_to_delete) is None
    assert db.get_full_entry(url_to_keep) is not None

def test_delete_urls_bulk(db):
    """Tests if multiple URLs can be efficiently deleted in a single bulk transaction."""
    portal = "TestPortal"
    test_data = [
        ("https://www.test1.com/test", portal, "https://www.test1.com/", "content 1"),
        ("https://www.test2.com/test", portal, "https://www.test2.com/", "content 2"),
        ("https://www.test3.com/test", portal, "https://www.test3.com/", "content 3"),
    ]

    for url, portal_name, portal_url, content in test_data:
        db.save_html(url, portal_name, portal_url, content)

    db.delete_urls_bulk(["https://www.test1.com/test", "https://www.test2.com/test"])

    assert db.get_full_entry("https://www.test1.com/test") is None
    assert db.get_full_entry("https://www.test2.com/test") is None
    assert db.get_full_entry("https://www.test3.com/test") is not None

def test_delete_urls_bulk_empty(db):
    """Tests if providing an empty list to bulk deletion safely returns without executing a query."""
    # Should not raise any errors
    db.delete_urls_bulk([])
    assert True

# Queue Functionality Tests

def test_pop_next_page(db):
    """Tests if pop_next_page successfully retrieves and removes the oldest entry based on crawled_at."""
    db.save_html("https://url1.com", "Portal1", "https://url1.com", "Content 1")
    db.save_html("https://url2.com", "Portal2", "https://url2.com", "Content 2")

    popped = db.pop_next_page()
    assert popped is not None
    assert popped["url"] == "https://url1.com"
    assert db.get_full_entry("https://url1.com") is None
    assert db.get_full_entry("https://url2.com") is not None


def test_pop_next_page_empty(db):
    """Tests if pop_next_page safely returns None when the database is empty."""
    assert db.pop_next_page() is None

# Exception Handling Tests (SQLite Errors)

@patch('src.storage.html_cache_manager.logger.error')
@patch('src.storage.html_cache_manager.sqlite3.connect')
def test_save_html_sqlite_error(mock_connect, mock_error, db):
    """Tests if an SQLite error during save_html is caught and logged as an error."""
    # Wir erstellen eine gefälschte Verbindung, die beim Aufruf von execute() crasht
    mock_conn = MagicMock()
    mock_conn.__enter__.return_value = mock_conn
    mock_conn.execute.side_effect = sqlite3.Error("Database locked")
    mock_connect.return_value = mock_conn

    db.save_html("https://test.com", "Portal", "https://test.com", "Content")

    mock_error.assert_called_once()
    assert "SQLite error saving URL" in mock_error.call_args[0][0]


@patch('src.storage.html_cache_manager.logger.error')
@patch('src.storage.html_cache_manager.sqlite3.connect')
def test_delete_url_sqlite_error(mock_connect, mock_error, db):
    """Tests if an SQLite error during delete_url is caught and logged as an error."""
    mock_conn = MagicMock()
    mock_conn.__enter__.return_value = mock_conn
    mock_conn.execute.side_effect = sqlite3.Error("Database locked")
    mock_connect.return_value = mock_conn

    db.delete_url("https://test.com")

    mock_error.assert_called_once()
    assert "SQLite error deleting URL" in mock_error.call_args[0][0]


@patch('src.storage.html_cache_manager.logger.error')
@patch('src.storage.html_cache_manager.sqlite3.connect')
def test_delete_urls_bulk_sqlite_error(mock_connect, mock_error, db):
    """Tests if an SQLite error during bulk deletion is caught and logged as an error."""
    mock_conn = MagicMock()
    mock_conn.__enter__.return_value = mock_conn
    mock_conn.executemany.side_effect = sqlite3.Error("Database locked")
    mock_connect.return_value = mock_conn

    db.delete_urls_bulk(["https://test1.com", "https://test2.com"])

    mock_error.assert_called_once()
    assert "SQLite error in bulk deletion" in mock_error.call_args[0][0]