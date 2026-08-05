import pytest
from unittest.mock import patch, MagicMock
from src.parser.parser_controller import get_existing_parsers, parse


# Tests for get_existing_parsers()

@patch('src.parser.parser_controller.logger.debug')
@patch('os.path.exists')
def test_get_existing_parsers_no_dir(mock_exists, mock_debug):
    """Tests what happens if the GENERATED_DIR folder does not exist."""
    mock_exists.return_value = False

    result = get_existing_parsers()

    assert result == []
    mock_debug.assert_called_once()
    assert "Generated directory not found" in mock_debug.call_args[0][0]


@patch('os.path.exists')
@patch('os.listdir')
def test_get_existing_parsers_with_files(mock_listdir, mock_exists):
    """Tests whether only valid _parser.py files are recognized."""
    mock_exists.return_value = True
    mock_listdir.return_value = [
        "fullfact_parser.py",
        "politifact_parser.py",
        "readme.md"
    ]

    result = get_existing_parsers()

    assert result == ["fullfact", "politifact"]


# Tests for parse(portal_name,html, llm_based)

@patch('src.parser.parser_controller.logger.debug')
@patch('src.parser.parser_controller.llm_parser')
def test_parse_llm_based(mock_llm_parser, mock_debug):
    """Test the LLM path (llm_based=True)."""
    mock_llm_parser.parse_factcheck.return_value = {"return_values"}

    result = parse("example_portal", "<html>...</html>", llm_based=True)

    assert result == {"return_values"}
    mock_llm_parser.parse_factcheck.assert_called_once_with("<html>...</html>")
    mock_debug.assert_called_once()
    assert "Routing parsing for example_portal to LLM" in mock_debug.call_args[0][0]

@patch('src.parser.parser_controller.logger.error')
@patch('pathlib.Path.exists')
def test_parse_file_not_found(mock_path_exists,mock_error):
    """
    Tests whether an error is thrown if the parser does not exist.
    """
    mock_path_exists.return_value = False

    with pytest.raises(FileNotFoundError, match="Parser for unknown does not exist"):
        parse("unknown", "<html>...</html>", llm_based=False)

    mock_error.assert_called_once()
    assert "does not exist" in mock_error.call_args[0][0]

@patch('src.parser.parser_controller.logger.error')
@patch('pathlib.Path.exists')
@patch('importlib.util.spec_from_file_location')
@patch('importlib.util.module_from_spec')
def test_parse_missing_function(mock_module_from_spec, mock_spec_from_file_location, mock_path_exists, mock_error):
    """
    Tests the behaviour if the file exists but the parse_factcheck function is missing.
    """
    mock_path_exists.return_value = True

    mock_module = MagicMock()
    del mock_module.parse_factcheck
    mock_module_from_spec.return_value = mock_module

    with pytest.raises(AttributeError, match="Parser for example_portal has no function parse_factcheck."):
        parse("example_portal", "<html>...</html>", llm_based=False)

    mock_error.assert_called_once()
    assert "has no function parse_factcheck" in mock_error.call_args[0][0]


@patch('src.parser.parser_controller.logger.warning')
def test_parse_empty_html(mock_warning):
    """
    Tests if the function returns None and logs a warning when the HTML is empty.
    """
    result = parse("example_portal", "", llm_based=False)

    assert result is None
    mock_warning.assert_called_once()
    assert "Parsing interrupted" in mock_warning.call_args[0][0]

@patch('src.parser.parser_controller.logger.debug')
@patch('pathlib.Path.exists')
@patch('importlib.util.spec_from_file_location')
@patch('importlib.util.module_from_spec')
def test_parse_script_success(mock_module_from_spec, mock_spec_from_file_location, mock_path_exists, mock_debug):
    """
    Tests the successful dynamic loading and execution of a script-based parser.
    """
    mock_path_exists.return_value = True

    mock_module = MagicMock()
    mock_module.parse_factcheck.return_value = {"claim": "true"}
    mock_module_from_spec.return_value = mock_module

    result = parse("example_portal", "<html>...</html>", llm_based=False)

    assert result == {"claim": "true"}
    mock_module.parse_factcheck.assert_called_once_with("<html>...</html>")
    mock_debug.assert_called_once()
    assert "Successfully loaded and executing script parser" in mock_debug.call_args[0][0]

@patch('src.parser.parser_controller.logger.debug')
@patch('src.parser.parser_controller.logger.warning')
@patch('pathlib.Path.exists')
@patch('importlib.util.spec_from_file_location')
@patch('importlib.util.module_from_spec')
def test_parse_script_exception(mock_module_from_spec, mock_spec_from_file_location, mock_path_exists, mock_warning,mock_debug):
    """
    Tests if an exception inside the dynamically loaded parser is caught, logged, and an empty list is returned.
    """
    mock_path_exists.return_value = True

    mock_module = MagicMock()
    mock_module.parse_factcheck.side_effect = Exception("BeautifulSoup crashed")
    mock_module_from_spec.return_value = mock_module

    result = parse("example_portal", "<html>...</html>", llm_based=False)

    assert result == []
    mock_debug.assert_called_once()
    mock_warning.assert_called_once()
    assert "Successfully loaded and executing script parser" in mock_debug.call_args[0][0]
    assert "Error parsing via parser example_portal" in mock_warning.call_args[0][0]