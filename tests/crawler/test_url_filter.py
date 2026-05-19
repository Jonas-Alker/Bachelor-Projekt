from src.crawler.url_filter import (
    load_rules,
    filter_url)
from unittest.mock import mock_open, patch

@patch('src.crawler.url_filter.os.path.exists')
def test_load_rules_file_not_exist(mock_exists):
    mock_exists.return_value = False
    include, exclude = load_rules("example_portal")

    assert include == ["artikel"]
    assert exclude == ["impressum"]

@patch('src.crawler.url_filter.os.path.exists')
def test_load_rules_fallback(mock_exists):
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

def test_filter_url_allowed():
    url = "https://www.politifact.com/artikel/2026/factcheck-something"
    include = ["artikel", "faktencheck"]
    exclude = ["impressum", "kontakt"]

    assert filter_url(url, include, exclude) is True

def test_filter_url_excluded():
    url = "https://www.politifact.com/legal/impressum"
    include = ["artikel"]
    exclude = ["impressum", "kontakt"]

    assert filter_url(url, include, exclude) is False

def test_filter_url_no_match():
    url = "https://www.politifact.com/main-page"
    include = ["artikel"]
    exclude = ["impressum"]

    assert filter_url(url, include, exclude) is False


def test_filter_url_conflict_exclude_wins():
    url = "https://www.politifact.com/artikel/how-to-kontakt"
    include = ["artikel"]
    exclude = ["kontakt", "impressum"]

    assert filter_url(url, include, exclude) is False