import pytest
import requests
from unittest.mock import patch, mock_open, MagicMock
from src.parser.llm_parser import load_few_shot, parse_factcheck



# Tests for load_few_shot

@patch("src.parser.llm_parser.logger.debug")
def test_load_few_shot_success(mock_debug):
    """
    Tests if the few-shot examples are correctly loaded from a JSON file and formatted into the required message structure.
    """
    mock_json_content = """
    [
        {
            "input_html": "<p>Claim here</p>",
            "expected_output": [{"headline": "Test Headline"}]
        }
    ]
    """

    with patch("src.parser.llm_parser.open", mock_open(read_data=mock_json_content)):
        result = load_few_shot()

    assert len(result) == 2
    assert result[0]["role"] == "user"
    assert "<p>Claim here</p>" in result[0]["content"]
    assert result[1]["role"] == "assistant"
    assert "Test Headline" in result[1]["content"]
    mock_debug.assert_called_once()
    assert "Loaded 1 few-shot examples" in mock_debug.call_args[0][0]


@patch("src.parser.llm_parser.open")
def test_load_few_shot_file_not_found(mock_file_open):
    """
    Tests if a FileNotFoundError is correctly raised when the few-shot JSON file is missing.
    """
    mock_file_open.side_effect = FileNotFoundError("No such file or directory")

    with pytest.raises(FileNotFoundError):
        load_few_shot()



# Tests for parse_factcheck(html_content)

@patch("src.parser.llm_parser.logger.debug")
@patch("src.parser.llm_parser.load_few_shot")
@patch("src.parser.llm_parser.requests.post")
def test_parse_factcheck_success(mock_post, mock_load_few_shot, mock_debug):
    """
    Tests if a valid API response is correctly parsed, stripped of markdown formatting, and returned as a Python list of dicts.
    """
    mock_load_few_shot.return_value = []
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "choices": [
            {
                "message": {
                    "content": "```json\n[{\"headline\": \"Valid LLM Extraction\"}]\n```"
                }
            }
        ]
    }
    mock_post.return_value = mock_response

    result = parse_factcheck("<html>Test Factcheck</html>")

    assert isinstance(result, list)
    assert result[0]["headline"] == "Valid LLM Extraction"
    mock_post.assert_called_once()
    call_args = mock_post.call_args[1]["json"]
    assert "<html>Test Factcheck</html>" in call_args["messages"][-1]["content"]
    assert mock_debug.call_count == 2
    assert "Sending extraction request" in mock_debug.call_args_list[0][0][0]
    assert "Parsed 1 claim(s)" in mock_debug.call_args_list[1][0][0]


@patch("src.parser.llm_parser.logger.error")
@patch("src.parser.llm_parser.logger.debug")
@patch("src.parser.llm_parser.load_few_shot")
@patch("src.parser.llm_parser.requests.post")
def test_parse_factcheck_api_error(mock_post,mock_load_few_shot, mock_debug, mock_logger):
    """
    Tests if an API or network error (like a 500 status code) is properly caught, logged, and returns None.
    """
    mock_load_few_shot.return_value = []
    mock_post.side_effect = requests.exceptions.HTTPError("500 Server Error")

    result = parse_factcheck("<html>Broken Factcheck</html>")

    assert result is None
    mock_logger.assert_called_once()
    assert "Error with the AI request" in mock_logger.call_args[0][0]
    mock_debug.assert_called_once()
    assert "Sending extraction request" in mock_debug.call_args[0][0]


@patch("src.parser.llm_parser.logger.error")
@patch("src.parser.llm_parser.logger.debug")
@patch("src.parser.llm_parser.load_few_shot")
@patch("src.parser.llm_parser.requests.post")
def test_parse_factcheck_json_repair_error(mock_post, mock_load_few_shot, mock_debug, mock_logger):
    """
    Tests if completely malformed output that even json_repair cannot fix is caught in the broad exception block.
    """
    mock_load_few_shot.return_value = []
    mock_response = MagicMock()
    mock_response.json.side_effect = KeyError("choices")
    mock_post.return_value = mock_response

    result = parse_factcheck("<html>Broken JSON format</html>")

    assert result is None
    mock_logger.assert_called_once()
    assert "Error with the AI request" in mock_logger.call_args[0][0]