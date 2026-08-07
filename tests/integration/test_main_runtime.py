import os
import json
import pytest
import sys
from unittest.mock import patch
from main_runtime import main

CLAIM_EXAMPLE = {
    "headline": "Elefant leitet ZOO? ",
    "body": "Integration Test Body",
    "author_factcheck": "Karla Kolumna",
    "published_at": "01.01.2026",
    "language": "de",
    "claim": "Benjamin Blümchen leitet einen ZOO.",
    "author_claim": "Otto",
    "stated_at": "01.12.2025",
    "original_rating": "Falsch"
}


def dummy_load_bulk(portal_data, hcm):
    """Simulates the crawler using the list of URLs."""
    hcm.save_html("https://Neustaedter-Zeitung/fc1", "Neustaedter Zeitung", "https://Neustaedter-Zeitung.com", "<html>Dummy</html>")


def dummy_search_sitemap(portal, url, hcm):
    """Simulates the crawler using the sitemap."""
    hcm.save_html("https://Neustaedter-Zeitung.com/fc2", "Neustaedter Zeitung", "https://Neustaedter-Zeitung.com", "<html>Dummy 2</html>")


def dummy_preprocess(portal, html_content):
    """Simulates the pre-processor."""
    return "<html>Shortened</html>"


def dummy_parse(portal, html_content, use_llm=False):
    """Simulates the parser (LLM or generated)."""
    return [CLAIM_EXAMPLE]


@pytest.mark.parametrize("use_url_list, use_preprocessor, use_generated_parser", [
    (True, False, False),
    (False, True, True),
    (True, True, False),
    (False, False, True),
])
@patch("main_runtime.load_bulk", side_effect=dummy_load_bulk)
@patch("main_runtime.search_sitemap_by_url", side_effect=dummy_search_sitemap)
@patch("main_runtime.preprocessor_controller.preprocess", side_effect=dummy_preprocess)
@patch("main_runtime.parse", side_effect=dummy_parse)
def test_main_pipeline_combinations(mock_parse, mock_preprocess, mock_search_sitemap, mock_load_bulk,
                                    use_url_list, use_preprocessor, use_generated_parser, tmp_path):
    """Tests various execution paths of main_runtime.py."""
    test_portal_data = tmp_path / "url_list.json"
    test_config_data = tmp_path / "portals.json"
    test_out_csv = tmp_path / "factchecks_export.csv"
    test_out_ttl = tmp_path / "faktchecks_export.ttl"

    with open(test_portal_data, "w", encoding="utf-8") as f:
        json.dump(
            [{"portal_name": "Neustaedter Zeitung", "portal_url": "https://Neustaedter-Zeitung.com", "factchecks": ["https://Neustaedter-Zeitung.com/fc1"]}],
            f)

    with open(test_config_data, "w", encoding="utf-8") as f:
        json.dump({"portals": [{"portal": "Neustaedter Zeitung", "url": "https://Neustaedter-Zeitung.com"}]}, f)

    test_args = ["main_runtime.py", "--html-db-version", "test_html", "--factcheck_db_version", "test_fc"]
    if use_url_list:
        test_args.append("--use-url-list")
    if use_preprocessor:
        test_args.append("--use-preprocessor")
    if use_generated_parser:
        test_args.append("--use-generated-parser")

    with patch("main_runtime.PORTAL_DATA", str(test_portal_data)), \
            patch("main_runtime.CONFIG_PORTALS", str(test_config_data)), \
            patch("main_runtime.OUTPUT_CSV", str(test_out_csv)), \
            patch("main_runtime.OUTPUT_TTL", str(test_out_ttl)), \
            patch.object(sys, 'argv', test_args):

        old_cwd = os.getcwd()
        os.chdir(tmp_path)
        try:
            main()
        finally:
            os.chdir(old_cwd)


    if use_url_list:
        assert mock_load_bulk.called
        assert not mock_search_sitemap.called
    else:
        assert mock_search_sitemap.called
        assert not mock_load_bulk.called

    if use_preprocessor:
        assert mock_preprocess.called
    else:
        assert not mock_preprocess.called

    assert mock_parse.called


    assert os.path.exists(test_out_csv)
    assert os.path.exists(test_out_ttl)