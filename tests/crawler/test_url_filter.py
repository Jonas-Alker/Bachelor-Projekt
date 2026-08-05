from src.crawler.url_filter import (
    load_rules,
    filter_url)
from unittest.mock import mock_open, patch

@patch('src.crawler.url_filter.logger.warning')
@patch('src.crawler.url_filter.os.path.exists')
def test_load_rules_file_not_exist(mock_exists, mock_logger):
    """Tests if hardcoded defaults are returned and a warning is logged when config is missing."""
    mock_exists.return_value = False
    include, exclude = load_rules("example_portal")

    assert include == ["artikel"]
    assert exclude == ["impressum"]
    mock_logger.assert_called_once()
    assert "not found" in mock_logger.call_args[0][0]

@patch('src.crawler.url_filter.logger.info')
@patch('src.crawler.url_filter.os.path.exists')
def test_load_rules_fallback(mock_exists, mock_logger):
    """Tests if the 'default' rules are applied and an info is logged when the portal is unknown."""
    mock_exists.return_value = True
    json_content = """
        {
            "default": {
                "include": ["faktencheck", "artikel"],
                "exclude": ["impressum", "kontakt", "ueber-uns"]
            }
        }
        """
    with patch('src.crawler.url_filter.open', mock_open(read_data=json_content)):
        include, exclude = load_rules("does_not_exist")
        include_default, exclude_default = load_rules("default")

    assert include == ["faktencheck", "artikel"]
    assert exclude == ["impressum", "kontakt", "ueber-uns"]
    assert include == include_default
    assert exclude == exclude_default
    mock_logger.assert_called_once()
    assert "Falling back to 'default'" in mock_logger.call_args[0][0]

@patch('src.crawler.url_filter.logger.error')
@patch('src.crawler.url_filter.os.path.exists')
def test_load_rules_invalid_json(mock_exists, mock_logger):
    """Tests if hardcoded defaults are returned and an error is logged when JSON is malformed."""
    mock_exists.return_value = True
    invalid_json_content = "{ invalid json data... }"

    with patch('src.crawler.url_filter.open', mock_open(read_data=invalid_json_content)):
        include, exclude = load_rules("example_portal")

    assert include == ["artikel"]
    assert exclude == ["impressum"]
    mock_logger.assert_called_once()
    assert "Error parsing JSON" in mock_logger.call_args[0][0]

def test_filter_url_allowed():
    """Tests if a URL containing an included keyword and no excluded keywords is correctly allowed."""
    url = "https://www.politifact.com/artikel/2026/factcheck-something"
    include = ["artikel", "faktencheck"]
    exclude = ["impressum", "kontakt"]

    assert filter_url(url, include, exclude) is True

def test_filter_url_excluded():
    """Tests if a URL containing an excluded keyword is correctly rejected."""
    url = "https://www.politifact.com/legal/impressum"
    include = ["artikel"]
    exclude = ["impressum", "kontakt"]

    assert filter_url(url, include, exclude) is False

def test_filter_url_no_match():
    """Tests if a URL is rejected by default when it matches neither include nor exclude keywords."""
    url = "https://www.politifact.com/main-page"
    include = ["artikel"]
    exclude = ["impressum"]

    assert filter_url(url, include, exclude) is False


def test_filter_url_conflict_exclude_wins():
    """Tests if a URL containing both included and excluded keywords is rejected, ensuring exclude rules take priority."""
    url = "https://www.politifact.com/artikel/how-to-kontakt"
    include = ["artikel"]
    exclude = ["kontakt", "impressum"]

    assert filter_url(url, include, exclude) is False