import pytest
from unittest.mock import patch, MagicMock
from src.preprocessor.preprocessor_controller import get_existing_preprocessors, preprocess


# Tests for get_existing_preprocessor()

@patch('src.preprocessor.preprocessor_controller.logger.debug')
@patch('os.path.exists')
def test_get_existing_preprocessor_no_dir(mock_exists, mock_debug):
    """
    Tests what happens if the GENERATED_DIR folder does not exist.
    """
    mock_exists.return_value = False

    result = get_existing_preprocessors()

    assert result == []
    mock_debug.assert_called_once()
    assert "Generated preprocessor directory not found" in mock_debug.call_args[0][0]


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

@patch('src.preprocessor.preprocessor_controller.logger.error')
@patch('pathlib.Path.exists')
def test_preprocessor_file_not_found(mock_path_exists, mock_error):
    """
    Tests whether an error is thrown if the preprocessor does not exist.
    """
    mock_path_exists.return_value = False

    with pytest.raises(FileNotFoundError, match="Preprocessor for unknown does not exist"):
        preprocess("unknown", "<html>...</html>")

    mock_error.assert_called_once()
    assert "does not exist" in mock_error.call_args[0][0]


@patch('src.preprocessor.preprocessor_controller.logger.error')
@patch('pathlib.Path.exists')
@patch('importlib.util.spec_from_file_location')
@patch('importlib.util.module_from_spec')
def test_parse_missing_function(mock_module_from_spec, mock_spec_from_file_location, mock_path_exists, mock_error):
    """
    Tests the behavior if the file exists but the preprocess_factcheck function is missing.
    """
    mock_path_exists.return_value = True
    mock_module = MagicMock(spec=[])
    mock_module_from_spec.return_value = mock_module

    with pytest.raises(AttributeError, match="Preprocessor for example_portal has no function preprocess_factcheck."):
        preprocess("example_portal", "<html>...</html>")

    mock_error.assert_called_once()
    assert "has no function preprocess_factcheck" in mock_error.call_args[0][0]

@patch('src.preprocessor.preprocessor_controller.logger.debug')
@patch('pathlib.Path.exists')
@patch('importlib.util.spec_from_file_location')
@patch('importlib.util.module_from_spec')
def test_preprocess_script_success(mock_module_from_spec, mock_spec_from_file_location, mock_path_exists, mock_debug):
    """
    Tests the successful dynamic loading and execution of a preprocessor script.
    """
    mock_path_exists.return_value = True
    mock_module = MagicMock()
    mock_module.preprocess_factcheck.return_value = "<html>Cleaned HTML</html>"
    mock_module_from_spec.return_value = mock_module

    result = preprocess("example_portal", "<html>Raw HTML</html>")

    assert result == "<html>Cleaned HTML</html>"
    mock_module.preprocess_factcheck.assert_called_once_with("<html>Raw HTML</html>")
    mock_debug.assert_called_once()
    assert "Successfully loaded and executing preprocessor script" in mock_debug.call_args[0][0]


@patch('src.preprocessor.preprocessor_controller.logger.error')
@patch('src.preprocessor.preprocessor_controller.logger.debug')
@patch('pathlib.Path.exists')
@patch('importlib.util.spec_from_file_location')
@patch('importlib.util.module_from_spec')
def test_preprocess_script_exception(mock_module_from_spec, mock_spec_from_file_location, mock_path_exists, mock_debug, mock_error):
    """
    Tests if an exception inside the dynamically loaded preprocessor is caught, logged, and None is returned.
    """
    mock_path_exists.return_value = True
    mock_module = MagicMock()
    mock_module.preprocess_factcheck.side_effect = Exception("Parsing logic crashed")
    mock_module_from_spec.return_value = mock_module

    result = preprocess("example_portal", "<html>Raw HTML</html>")

    assert result is None
    mock_debug.assert_called_once()
    mock_error.assert_called_once()
    assert "Error during preprocessing" in mock_error.call_args[0][0]