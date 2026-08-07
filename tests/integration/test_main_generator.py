import json
import pytest
from unittest.mock import patch, mock_open
from main_generator import generate_missing_codes

DUMMY_CONFIG = [
    {"name": "Correctiv", "factcheck_example": "https://correctiv.org/beispiel1"},
    {"name": "Mimikama", "factcheck_example": "https://mimikama.org/beispiel2"}
]


@patch("main_generator.gen_preprocessor.generate_preprocessor")
@patch("main_generator.gen_parser.generate_parser")
@patch("main_generator.preprocessor_c.get_existing_preprocessors")
@patch("main_generator.parser_c.get_existing_parsers")
def test_generate_missing_codes_all_exist(mock_get_parsers, mock_get_preprocessors,
                                          mock_gen_parser, mock_gen_preproc):
    """Check that nothing is generated if all the codes are already present."""
    mock_get_parsers.return_value = ["correctiv", "mimikama"]
    mock_get_preprocessors.return_value = ["correctiv", "mimikama"]
    m_open = mock_open(read_data=json.dumps(DUMMY_CONFIG))
    with patch("builtins.open", m_open):
        generate_missing_codes()

    mock_gen_parser.assert_not_called()
    mock_gen_preproc.assert_not_called()


@patch("main_generator.gen_preprocessor.generate_preprocessor")
@patch("main_generator.gen_parser.generate_parser")
@patch("main_generator.preprocessor_c.get_existing_preprocessors")
@patch("main_generator.parser_c.get_existing_parsers")
def test_generate_missing_codes_some_missing(mock_get_parsers, mock_get_preprocessors,
                                             mock_gen_parser, mock_gen_preproc):
    """Checks that missing parsers and pre-processors are correctly identified and generated."""

    # correctiv has a parser but no pre-processor ,mimikama” is completely both
    mock_get_parsers.return_value = ["correctiv"]
    mock_get_preprocessors.return_value = []

    m_open = mock_open(read_data=json.dumps(DUMMY_CONFIG))
    with patch("builtins.open", m_open):
        generate_missing_codes()

    mock_gen_parser.assert_called_once_with("https://mimikama.org/beispiel2", "mimikama")
    assert mock_gen_preproc.call_count == 2