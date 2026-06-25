import pytest
from unittest.mock import patch, MagicMock
from src.preprocessor.preprocessor_controller import get_existing_preprocessors, preprocess


# Tests for get_existing_preprocessor()

@patch('os.path.exists')
def test_get_existing_preprocessor_no_dir(mock_exists):
    """
    Tests what happens if the GENERATED_DIR folder does not exist.
    """
    mock_exists.return_value = False

    result = get_existing_preprocessors()
    assert result == []


@patch('os.path.exists')
@patch('os.listdir')
def test_get_existing_preprocessor_with_files(mock_listdir, mock_exists):
    """
    Tests whether only valid _preprocessor.py files are recognised.
    """
    mock_exists.return_value = True
    mock_listdir.return_value = [
        "fullfact_preprocessor.py",
        "politifact_preprocessor.py",
        "readme.md"
    ]

    result = get_existing_preprocessors()

    assert result == ["fullfact", "politifact"]


# Tests for preprocess(portal_name,html)

@patch('pathlib.Path.exists')
def test_preprocessor_file_not_found(mock_path_exists):
    """
    Tests whether an error is thrown if the preprocessor does not exist.
    """
    mock_path_exists.return_value = False

    with pytest.raises(FileNotFoundError, match="Preprocessor for unknown does not exist"):
        preprocess("unknown", "<html>...</html>")


@patch('pathlib.Path.exists')
@patch('importlib.util.spec_from_file_location')
@patch('importlib.util.module_from_spec')
def test_parse_missing_function(mock_module_from_spec, mock_spec_from_file_location, mock_path_exists):
    """
    Tests the behaviour if the file exists but the preprocessor_factcheck function is missing.
    """
    mock_path_exists.return_value = True

    mock_module = MagicMock()
    del mock_module.preprocess_factcheck
    mock_module_from_spec.return_value = mock_module

    with pytest.raises(AttributeError, match="Preprocessor for example_portal has no function preprocess_factcheck."):
        preprocess("example_portal", "<html>...</html>")