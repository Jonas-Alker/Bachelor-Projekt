import os

from src.storage.html_cache_manager import HTMLCacheManager
import pytest

@pytest.fixture
def db():
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
    url = "https://www.test.com"
    portal_name = "TestPortal"
    content = "<html> Test </html>"

    db.save_html(url,portal_name,content)
    result = db.get_full_entry(url)

    assert result is not None
    assert result["portal"] == portal_name
    assert result["html_content"] == content

def test_get_non_existing_entry(db):
    result = db.get_full_entry("https://www.not-here.com")
    assert result is None

def test_get_urls_by_portal(db):
    test_data = [
        ("https://www.test1.com", "TestPortal_A", "conntent 1"),
        ("https://www.test2.com", "TestPortal_A", "conntent 2"),
        ("https://www.test3.com", "TestPortal_B", "conntent 3"),
    ]

    for url, portal, content in test_data:
        db.save_html(url, portal, content)

    urls_a = db.get_urls_by_portal("TestPortal_A")
    assert len(urls_a) == 2
    assert "https://www.test1.com" in urls_a
    assert "https://www.test2.com" in urls_a
    assert "https://www.test3.com" not in urls_a

def test_load_existing_db(db):
    db_path = db.db_path
    base_path = os.path.dirname(db_path)

    url = "https://www.test.com"
    portal_name = "TestPortal"
    content = "<html> Test </html>"
    db.save_html(url, portal_name, content)

    try:
        loader = HTMLCacheManager(version="test_v1", mode= "load",base_path= base_path)
        assert loader.db_path == db_path
        result = loader.get_full_entry(url)
        assert result is not None
        assert result["portal"] == portal_name
        assert result["html_content"] == content
    except FileNotFoundError:
        pytest.fail("DBManager did not load properly!")
    del loader

def test_load_non_existing_db():
    with pytest.raises(FileNotFoundError) as excinfo:
        HTMLCacheManager(version="not-here", mode= "load", base_path="tests/test_data/raw")
    assert "of db file not found:" in str(excinfo)

def test_delete_url(db):
    url_to_delete = "https://www.test1.com"
    url_to_keep = "https://www.test2.com"
    portal = "TestPortal"
    content = "<html>Test</html>"

    db.save_html(url_to_delete, portal, content)
    db.save_html(url_to_keep, portal, content)
    db.delete_url(url_to_delete)

    assert db.get_full_entry(url_to_delete) is None
    assert db.get_full_entry(url_to_keep) is not None

def test_delete_urls_bulk(db: HTMLCacheManager):
    portal = "TestPortal"
    test_data = [
        ("https://www.test1.com", portal, "content 1"),
        ("https://www.test2.com", portal, "content 2"),
        ("https://www.test3.com", portal, "content 3"),
    ]

    for url, portal_name, content in test_data:
        db.save_html(url, portal_name, content)
    urls_to_delete = ["https://www.test1.com", "https://www.test2.com"]

    db.delete_urls_bulk(urls_to_delete)

    assert db.get_full_entry("https://www.test1.com") is None
    assert db.get_full_entry("https://www.test2.com") is None
    assert db.get_full_entry("https://www.test3.com") is not None
    remaining_urls = db.get_urls_by_portal(portal)
    assert len(remaining_urls) == 1
    assert "https://www.test3.com" in remaining_urls