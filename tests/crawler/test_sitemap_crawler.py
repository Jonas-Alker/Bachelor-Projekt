from src.crawler.sitemap_crawler import (
    search_sitemap_by_url,
    find_sitemap_automatically,
    crawl_sitemap_manually, load_bulk, fetch_page)
from unittest.mock import patch, MagicMock

@patch("src.crawler.sitemap_crawler.logger.info")
@patch("src.crawler.sitemap_crawler.find_sitemap_automatically")
@patch("src.crawler.sitemap_crawler.crawl_sitemap_manually")
def test_search_sitemap_by_url_automatic_success(mock_manual, mock_auto, mock_logger):
    """Tests if the manual fallback is avoided when automatic discovery succeeds."""
    mock_auto.return_value = True
    mock_db = MagicMock()

    search_sitemap_by_url("test_portal", "https://example.com", mock_db)

    mock_auto.assert_called_once_with("https://example.com", "test_portal", mock_db)
    mock_manual.assert_not_called()
    assert mock_logger.call_count == 2

@patch("src.crawler.sitemap_crawler.logger.info")
@patch("src.crawler.sitemap_crawler.find_sitemap_automatically")
@patch("src.crawler.sitemap_crawler.crawl_sitemap_manually")
def test_search_sitemap_by_url_fallback_to_manual(mock_manual, mock_auto, mock_logger):
    """Tests if the crawler correctly falls back to manual crawl when sitemap discovery fails."""
    mock_auto.return_value = False
    mock_db = MagicMock()

    search_sitemap_by_url("test_portal", "https://example.com", mock_db)

    mock_auto.assert_called_once()
    mock_manual.assert_called_once_with("https://example.com", "test_portal", mock_db)
    assert mock_logger.call_count == 2

@patch("src.crawler.sitemap_crawler.url_filter")
@patch("src.crawler.sitemap_crawler.sitemap_tree_for_homepage")
@patch("src.crawler.requester.fetch_page")
def test_find_sitemap_automatically_success(mock_fetch, mock_sitemap_tree,mock_filter):
    """Tests successful automatic sitemap discovery and HTML extraction."""
    mock_tree = MagicMock()
    mock_page = MagicMock()
    mock_page.url = "https://example.com/page1"
    mock_tree.all_pages.return_value = [mock_page]
    mock_sitemap_tree.return_value = mock_tree

    mock_filter.load_rules.return_value = (["artikel"], ["impressum"])
    mock_filter.filter_url.return_value = True

    mock_fetch.return_value = "<html>Content</html>"
    mock_db = MagicMock()

    result = find_sitemap_automatically("https://example.com", "test_portal", mock_db)

    assert result is True
    mock_fetch.assert_called_once_with("https://example.com/page1")
    mock_db.save_html.assert_called_once_with("https://example.com/page1", "test_portal", "<html>Content</html>")

@patch("src.crawler.sitemap_crawler.logger.error")
@patch("src.crawler.sitemap_crawler.sitemap_tree_for_homepage")
def test_find_sitemap_automatically_empty_or_error(mock_sitemap_tree, mock_logger):
    """Tests error handling and logging during a failed sitemap discovery."""
    mock_sitemap_tree.side_effect = Exception("USP Discovery Failed")
    mock_db = MagicMock()

    result = find_sitemap_automatically("https://example.com", "test_portal", mock_db)

    assert result is False
    mock_db.save_html.assert_not_called()
    mock_logger.assert_called_once()
    assert "Sitemap Automatic Crawl Error" in mock_logger.call_args[0][0]

@patch("src.crawler.sitemap_crawler.find_sitemap_automatically")
@patch("src.crawler.sitemap_crawler.crawl_sitemap_manually")
def test_search_sitemap_by_url_orchestration(mock_manual, mock_auto):
    mock_db = MagicMock()

    mock_auto.return_value = True
    search_sitemap_by_url("test_portal", "https://example.com", mock_db)
    mock_auto.assert_called_once()
    mock_manual.assert_not_called()

    mock_auto.reset_mock()
    mock_auto.return_value = False
    search_sitemap_by_url("test_portal", "https://example.com", mock_db)
    mock_manual.assert_called_once()

@patch("src.crawler.sitemap_crawler.logger.info")
@patch("src.crawler.sitemap_crawler.requester")
@patch("src.crawler.sitemap_crawler.link_parser")
@patch("src.crawler.sitemap_crawler.url_filter")
def test_crawl_sitemap_manually_logic(mock_filter, mock_parser, mock_req, mock_logger):
    """Tests the breadth-first logic, ensuring correct URL filtering and sublink extraction."""
    mock_db = MagicMock()
    mock_db.get_urls_by_portal.return_value = []

    mock_filter.load_rules.return_value = ([], [])
    mock_filter.filter_url.return_value = True
    mock_req.fetch_page.return_value = "<html></html>"
    mock_parser.extract_sublinks.return_value = []

    crawl_sitemap_manually("https://example.com", "test_portal", mock_db)

    assert mock_req.fetch_page.called
    assert mock_db.save_html.called

@patch("src.crawler.sitemap_crawler.logger.info")
@patch("src.crawler.sitemap_crawler.requester.fetch_page")
def test_load_bulk_success(mock_fetch, mock_logger):
    """Tests if bulk data is correctly iterated, fetched, and saved to the database."""
    mock_db = MagicMock()
    mock_fetch.return_value = "<html>Content</html>"

    portal_data = [{
        "portal_name": "test_portal",
        "portal_url": "https://example.com",
        "factchecks": ["https://example.com/page1", "https://example.com/page2"]
    }]

    load_bulk(portal_data, mock_db)

    assert mock_fetch.call_count == 2
    assert mock_db.save_html.call_count == 2

    mock_db.save_html.assert_any_call(
        "https://example.com/page1",
        "test_portal",
        "https://example.com",
        "<html>Content</html>"
    )

    mock_db.save_html.assert_any_call(
        "https://example.com/page2",
        "test_portal",
        "https://example.com",
        "<html>Content</html>"
    )


@patch("src.crawler.sitemap_crawler.logger.error")
@patch("src.crawler.sitemap_crawler.logger.info")
@patch("src.crawler.sitemap_crawler.requester.fetch_page")
def test_load_bulk_error_handling(mock_fetch, mock_info, mock_error):
    """Tests if exceptions during bulk loading are caught and logged without crashing the process."""
    mock_db = MagicMock()
    mock_fetch.side_effect = Exception("Bulk Fetch Error")

    portal_data = [{
        "portal_name": "test_portal",
        "portal_url": "https://example.com",
        "factchecks": ["https://example.com/error"]
    }]

    load_bulk(portal_data, mock_db)

    assert mock_db.save_html.call_count == 0
    mock_error.assert_called_once()
    assert "Error during bulk load" in mock_error.call_args[0][0]


@patch("src.crawler.sitemap_crawler.requester")
def test_fetch_page_wrapper(mock_requester):
    """Tests if the fetch_page wrapper correctly delegates the call to the requester module."""
    mock_requester.fetch_page.return_value = "<html>Wrapper Content</html>"

    result = fetch_page("https://example.com/wrapper")

    assert result == "<html>Wrapper Content</html>"
    mock_requester.fetch_page.assert_called_once_with("https://example.com/wrapper")