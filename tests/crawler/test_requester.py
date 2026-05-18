from src.crawler.requester import fetch_page
from unittest.mock import MagicMock, patch
import requests


@patch("src.crawler.requester.time.sleep")
@patch("src.crawler.requester.requests.get")
def test_fetch_page_success(mock_get,mock_sleep):
    """Tests if the function returns the HTML text upon a successful HTTP 200 response."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.text = "<html>Valid HTML</html>"
    mock_get.return_value = mock_response

    result = fetch_page("http://example.com")

    assert result == "<html>Valid HTML</html>"

    mock_sleep.assert_called_once()
    mock_get.assert_called_once_with("http://example.com", timeout=10)

@patch("src.crawler.requester.time.sleep")
@patch("src.crawler.requester.requests.get")
def test_fetch_page_http_error(mock_get, mock_sleep):
    """Tests if None is returned in the event of an HTTP error (e.g. 404)."""
    mock_response = MagicMock()
    mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError("404 Not Found")
    mock_get.return_value = mock_response

    result = fetch_page("https://example.com/broken-link")

    assert result is None
    mock_get.assert_called_once()

@patch("src.crawler.requester.time.sleep")
@patch("src.crawler.requester.requests.get")
def test_fetch_page_timeout(mock_get, mock_sleep):
    """Tests the behaviour in the event of a connection timeout."""
    mock_get.side_effect = requests.exceptions.Timeout("Connection timed out")

    result = fetch_page("https://example.com/slow-page", timeout=5)

    assert result is None
    mock_get.assert_called_once_with("https://example.com/slow-page", timeout=5)