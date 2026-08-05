from src.crawler.requester import fetch_page
from unittest.mock import MagicMock, patch
import requests


@patch("src.crawler.requester.time.sleep")
@patch("src.crawler.requester.session.get")
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

@patch("src.crawler.requester.logger.error")
@patch("src.crawler.requester.time.sleep")
@patch("src.crawler.requester.session.get")
def test_fetch_page_http_error(mock_get, mock_sleep, mock_logger):
    """Tests if None is returned in the event of an HTTP error (e.g. 404)."""
    mock_response = MagicMock()
    mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError("404 Not Found")
    mock_get.return_value = mock_response

    result = fetch_page("https://example.com/broken-link")

    assert result is None
    mock_get.assert_called_once()
    mock_logger.assert_called_once()
    assert "HTTP Error" in mock_logger.call_args[0][0]

@patch("src.crawler.requester.logger.error")
@patch("src.crawler.requester.time.sleep")
@patch("src.crawler.requester.session.get")
def test_fetch_page_timeout(mock_get, mock_sleep, mock_logger):
    """Tests the behaviour in the event of a connection timeout."""
    mock_get.side_effect = requests.exceptions.Timeout("Connection timed out")

    result = fetch_page("https://example.com/slow-page", timeout=5)

    assert result is None
    mock_get.assert_called_once_with("https://example.com/slow-page", timeout=5)
    mock_logger.assert_called_once()
    assert "Fetch Connection Error" in mock_logger.call_args[0][0]

@patch("src.crawler.requester.logger.error")
@patch("src.crawler.requester.time.sleep")
@patch("src.crawler.requester.session.get")
def test_fetch_page_connection_error(mock_get, mock_sleep, mock_logger):
    """Tests if None is returned and logged when a general RequestException occurs."""
    mock_get.side_effect = requests.exceptions.ConnectionError("Network unreachable")

    result = fetch_page("https://example.com/network-error")

    assert result is None
    mock_get.assert_called_once_with("https://example.com/network-error", timeout=10)
    mock_logger.assert_called_once()
    assert "Fetch Connection Error" in mock_logger.call_args[0][0]

@patch("src.crawler.requester.logger.error")
@patch("src.crawler.requester.time.sleep")
@patch("src.crawler.requester.session.get")
def test_fetch_page_unexpected_exception(mock_get, mock_sleep, mock_logger):
    """Tests if None is returned and logged for completely unexpected exceptions."""
    mock_get.side_effect = ValueError("Something completely unexpected happened")

    result = fetch_page("https://example.com/unexpected")

    assert result is None
    mock_logger.assert_called_once()
    assert "Unexpected Error fetching" in mock_logger.call_args[0][0]