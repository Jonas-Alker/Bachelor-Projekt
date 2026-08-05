import pytest
import requests
import json
import os
from unittest.mock import patch, mock_open, MagicMock
from tools.generate_parser import load_html, load_few_shots, generate_parser


# Tests for load_html

@patch("tools.generate_parser.logger.debug")
@patch("tools.generate_parser.fetch_page")
def test_load_html_success(mock_fetch_page, mock_debug):
    """
    Tests if HTML is successfully fetched via the sitemap crawler and debug statements are logged.
    """
    mock_fetch_page.return_value = "<html>Test Content</html>"

    result = load_html("https://test.com")

    assert result == "<html>Test Content</html>"
    mock_fetch_page.assert_called_once_with("https://test.com")
    mock_debug.assert_called_once()
    assert "Attempting to download HTML from: https://test.com" in mock_debug.call_args[0][0]


# Tests for load_few_shots

@patch("tools.generate_parser.logger.debug")
def test_load_few_shots_success(mock_debug):
    """
    Tests if the few-shot examples are correctly loaded from a JSON file and formatted into the required message structure.
    """
    mock_json_content = """
    [
        {
            "input_html": "<p>Fact</p>",
            "expected_output": [{"headline": "Test"}]
        }
    ]
    """
    with patch("tools.generate_parser.open", mock_open(read_data=mock_json_content)):
        result = load_few_shots()

    assert len(result) == 2
    assert result[0]["role"] == "user"
    assert "<p>Fact</p>" in result[0]["content"]
    assert result[1]["role"] == "assistant"
    assert "Test" in result[1]["content"]

    mock_debug.assert_called_once()
    assert "Loaded 1 few-shot examples for LLM prompt" in mock_debug.call_args[0][0]


@patch("tools.generate_parser.logger.error")
@patch("tools.generate_parser.open")
def test_load_few_shots_file_not_found(mock_file_open, mock_error):
    """
    Tests if a FileNotFoundError is correctly raised and logged when the few-shot JSON file is missing.
    """
    mock_file_open.side_effect = FileNotFoundError("No such file or directory")

    with pytest.raises(FileNotFoundError):
        load_few_shots()

    mock_error.assert_called_once()
    assert "Few-shot examples file not found" in mock_error.call_args[0][0]


@patch("tools.generate_parser.logger.error")
@patch("tools.generate_parser.open")
def test_load_few_shots_json_decode_error(mock_file_open, mock_error):
    """
    Tests if a JSONDecodeError is correctly raised and logged when the few-shot JSON file is corrupted.
    """
    mock_file_open.return_value.__enter__.return_value.read.return_value = "{broken_json:"

    with pytest.raises(json.JSONDecodeError):
        load_few_shots()

    mock_error.assert_called_once()
    assert "Error decoding JSON from few-shot examples" in mock_error.call_args[0][0]

# Tests for generate_parser

@patch("tools.generate_parser.os.makedirs")
@patch("tools.generate_parser.open", new_callable=mock_open)
@patch("tools.generate_parser.logger.info")
@patch("tools.generate_parser.logger.debug")
@patch("tools.generate_parser.requests.post")
@patch("tools.generate_parser.load_few_shots")
@patch("tools.generate_parser.load_html")
def test_generate_parser_success(mock_load_html, mock_load_few_shots, mock_post, mock_debug, mock_info, mock_file_open,
                                 mock_makedirs):
    """
    Tests the full success path: fetching HTML, calling the API, stripping markdown, and writing the parser script.
    """
    mock_load_html.return_value = "<html>Dummy</html>"
    mock_load_few_shots.return_value = []
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "choices": [
            {
                "message": {
                    "content": "```python\ndef parse_factcheck(html_content):\n    pass\n```"
                }
            }
        ]
    }
    mock_post.return_value = mock_response

    generate_parser("https://test.com", "TestPortal")


    mock_load_html.assert_called_once_with("https://test.com")
    mock_post.assert_called_once()
    call_args = mock_post.call_args[1]["json"]
    assert "<html>Dummy</html>" in call_args["messages"][-1]["content"]
    mock_file_open.assert_called_once()
    handle = mock_file_open()
    handle.write.assert_called_once_with("def parse_factcheck(html_content):\n    pass")
    mock_debug.assert_called_once()
    assert "Sending extraction request to KIConnect API" in mock_debug.call_args[0][0]
    mock_info.assert_called_once()
    assert "Successfully generated parser for testportal" in mock_info.call_args[0][0]


@patch("tools.generate_parser.logger.error")
@patch("tools.generate_parser.load_html")
def test_generate_parser_html_fail(mock_load_html, mock_error):
    """
    Tests if the generation safely aborts and logs an error if the HTML fails to load.
    """
    mock_load_html.return_value = None

    generate_parser("https://test.com", "TestPortal")

    mock_error.assert_called_once()
    assert "Skipping parser generation for testportal" in mock_error.call_args[0][0]
    assert "HTML could not be loaded" in mock_error.call_args[0][0]


@patch("tools.generate_parser.logger.error")
@patch("tools.generate_parser.requests.post")
@patch("tools.generate_parser.load_few_shots")
@patch("tools.generate_parser.load_html")
def test_generate_parser_api_fail(mock_load_html, mock_load_few_shots, mock_post, mock_error):
    """
    Tests if a failure during the API request (e.g., network error or 500 status) is caught and logged.
    """
    mock_load_html.return_value = "<html>Dummy</html>"
    mock_load_few_shots.return_value = []
    mock_post.side_effect = requests.exceptions.HTTPError("500 Server Error")

    generate_parser("https://test.com", "TestPortal")

    mock_error.assert_called_once()
    assert "Failed to generate parser for testportal" in mock_error.call_args[0][0]