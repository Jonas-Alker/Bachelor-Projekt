import pytest
from unittest.mock import patch, MagicMock
from src.parser.parser_controller import get_existing_parsers, parse


# Tests for get_existing_parsers()

@patch('os.path.exists')
def test_get_existing_parsers_no_dir(mock_exists):
    """
    Tests what happens if the GENERATED_DIR folder does not exist.
    """
    mock_exists.return_value = False

    result = get_existing_parsers()
    assert result == []


@patch('os.path.exists')
@patch('os.listdir')
def test_get_existing_parsers_with_files(mock_listdir, mock_exists):
    """
    Tests whether only valid _parser.py files are recognised.
    """
    mock_exists.return_value = True
    mock_listdir.return_value = [
        "fullfact_parser.py",
        "politifact_parser.py",
        "readme.md"
    ]

    result = get_existing_parsers()

    assert result == ["fullfact", "politifact"]


# Tests for parse(portal_name,html, llm_based)

@patch('src.parser.parser_controller.llm_parser')
def test_parse_llm_based(mock_llm_parser):
    """
    Test the LLM path (llm_based=True).
    """
    mock_llm_parser.parse_factcheck.return_value = {"return_values"}

    result = parse("example_portal", "<html>...</html>", llm_based=True)

    assert result == {"return_values"}
    mock_llm_parser.parse_factcheck.assert_called_once_with("<html>...</html>")


@patch('pathlib.Path.exists')
def test_parse_file_not_found(mock_path_exists):
    """
    Tests whether an error is thrown if the parser does not exist.
    """
    mock_path_exists.return_value = False

    with pytest.raises(FileNotFoundError, match="Parser for unknown does not exist"):
        parse("unknown", "<html>...</html>", llm_based=False)


@patch('pathlib.Path.exists')
@patch('importlib.util.spec_from_file_location')
@patch('importlib.util.module_from_spec')
def test_parse_missing_function(mock_module_from_spec, mock_spec_from_file_location, mock_path_exists):
    """
    Tests the behaviour if the file exists but the parse_factcheck function is missing.
    """
    mock_path_exists.return_value = True

    mock_module = MagicMock()
    del mock_module.parse_factcheck
    mock_module_from_spec.return_value = mock_module

    with pytest.raises(AttributeError, match="Parser for example_portal has no function parse_factcheck."):
        parse("example_portal", "<html>...</html>", llm_based=False)