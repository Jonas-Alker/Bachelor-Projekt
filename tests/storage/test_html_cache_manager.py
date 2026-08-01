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
    result = db.get_full_entry("https://www.not-here.com")
    assert result is None

def test_get_urls_by_portal(db):
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

def test_load_existing_db(db):
    db_path = db.db_path
    base_path = os.path.dirname(db_path)

    url = "https://www.test.com/test"
    portal_name = "TestPortal"
    portal_url = "https://www.test.com"
    content = "<html> Test </html>"
    db.save_html(url, portal_name, portal_url, content)

    try:
        loader = HTMLCacheManager(version="test_v1", mode= "load",base_path= base_path)
        assert loader.db_path == db_path
        result = loader.get_full_entry(url)
        assert result is not None
        assert result["portal"] == portal_name
        assert result["html_content"] == content
        assert result["portal_url"] == portal_url
    except FileNotFoundError:
        pytest.fail("DBManager did not load properly!")
    del loader

def test_load_non_existing_db():
    with pytest.raises(FileNotFoundError) as excinfo:
        HTMLCacheManager(version="not-here", mode= "load", base_path="tests/test_data/raw")
    assert "of db file not found:" in str(excinfo)

def test_delete_url(db):
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

def test_delete_urls_bulk(db: HTMLCacheManager):
    portal = "TestPortal"
    test_data = [
        ("https://www.test1.com/test", portal, "https://www.test1.com/", "content 1"),
        ("https://www.test2.com/test", portal, "https://www.test2.com/", "content 2"),
        ("https://www.test3.com/test", portal, "https://www.test3.com/", "content 3"),
    ]

    for url, portal_name, portal_url, content in test_data:
        db.save_html(url, portal_name, portal_url, content)
    urls_to_delete = ["https://www.test1.com/test", "https://www.test2.com/test"]

    db.delete_urls_bulk(urls_to_delete)

    assert db.get_full_entry("https://www.test1.com/test") is None
    assert db.get_full_entry("https://www.test2.com/test") is None
    assert db.get_full_entry("https://www.test3.com/test") is not None
    remaining_urls = db.get_urls_by_portal(portal)
    assert len(remaining_urls) == 1
    assert "https://www.test3.com/test" in remaining_urls