from src.crawler.sitemap_crawler import (
    search_sitemap_by_url,
    find_sitemap_automatically,
    crawl_sitemap_manually)
from unittest.mock import patch, MagicMock

@patch("src.crawler.sitemap_crawler.find_sitemap_automatically")
@patch("src.crawler.sitemap_crawler.crawl_sitemap_manually")
def test_search_sitemap_by_url_automatic_success(mock_manual, mock_auto):
    mock_auto.return_value = True
    mock_db = MagicMock()

    search_sitemap_by_url("test_portal", "https://example.com", mock_db)

    mock_auto.assert_called_once_with("https://example.com", "test_portal", mock_db)
    mock_manual.assert_not_called()

@patch("src.crawler.sitemap_crawler.find_sitemap_automatically")
@patch("src.crawler.sitemap_crawler.crawl_sitemap_manually")
def test_search_sitemap_by_url_fallback_to_manual(mock_manual, mock_auto):
    mock_auto.return_value = False
    mock_db = MagicMock()

    search_sitemap_by_url("test_portal", "https://example.com", mock_db)

    mock_auto.assert_called_once()
    mock_manual.assert_called_once_with("https://example.com", "test_portal", mock_db)

@patch("src.crawler.sitemap_crawler.sitemap_tree_for_homepage")
@patch("src.crawler.requester.fetch_page")
def test_find_sitemap_automatically_success(mock_fetch, mock_sitemap_tree):
    mock_tree = MagicMock()
    mock_page = MagicMock()
    mock_page.url = "https://example.com/page1"
    mock_tree.all_pages.return_value = ["https://example.com/page1"]
    mock_sitemap_tree.return_value = mock_tree

    mock_fetch.return_value = "<html>Inhalt</html>"
    mock_db = MagicMock()

    result = find_sitemap_automatically("https://example.com", "test_portal", mock_db)

    assert result is True
    mock_fetch.assert_called_once_with("https://example.com/page1")
    mock_db.save_html.assert_called_once_with("https://example.com/page1", "test_portal", "<html>Inhalt</html>")


@patch("src.crawler.sitemap_crawler.sitemap_tree_for_homepage")
def test_find_sitemap_automatically_empty_or_error(mock_sitemap_tree):

    mock_sitemap_tree.side_effect = Exception("USP Discovery Failed")
    mock_db = MagicMock()

    result = find_sitemap_automatically("https://example.com", "test_portal", mock_db)

    assert result is False
    mock_db.save_html.assert_not_called()