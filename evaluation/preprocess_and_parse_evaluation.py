import json
from pathlib import Path

import requests
import src.preprocessor.preprocessor_controller as preprocessor_controller
import src.parser.parser_controller as parser_controller
from src.storage.fact_check_manager import FactCheckManager

def load_html(url):
    """
    Downloads the HTML from the URL provided.

    :param url: url to download
    :return: HTML content
    """
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.text

    except Exception as e:
        print(f"Error loading URL: {e}")
        return None


def extraction_llm(portal, html):
    """
    Forwards the method call for extraction. The HTML is pre-processed and then parsed using an LLM.

    :param portal: name of portal
    :param html: HTML from which data is to be extracted

    :return: extraction data
    """
    html_shortend = preprocessor_controller.preprocess(portal, html)
    return parser_controller.parse(portal, html_shortend, True)


def extraction_llm_directly(portal, html):
    """
    Forwards the method call for extraction. The HTML is NOT pre-processed but parsed directly using an LLM.

    :param portal: name of portal
    :param html: HTML from which data is to be extracted

    :return: extraction data
    """
    return parser_controller.parse(portal, html, True)

def extraction_normal(portal, html):
    """
    Forwards the method call for extraction. The HTML is parsed using the generated parser scripts.

    :param portal: name of portal
    :param html: HTML from which data is to be extracted

    :return: extraction data
    """
    return parser_controller.parse(portal, html, False)

def test_extraktion():
    """
    Test the extraction using sample fact-checks stored in `evaluation_data/evaluation_portals.json`.
    Three different approaches are tested:
    1. Direct LLM extraction (without pre-processing)
    2. LLM extraction with prior pre-processing
    3. Extraction via pre-generated parser scripts with pre-processing

    The results are stored in a database and also exported as CSV files in the ‘evaluation_data’ folder.
    """
    #Load evaluation_data
    data_path = Path(__file__).resolve().parent / "evaluation_data" / "evaluation_portals.json"
    with open(data_path, "r") as f:
        file = json.load(f)

    #Create Databases
    manager_by_llm = FactCheckManager(version="test_llm", mode="create", base_path="evaluation/evaluation_data")
    manager_by_llm_directly = FactCheckManager(version="test_llm_directly", mode="create", base_path="evaluation/evaluation_data")
    manager_by_parser = FactCheckManager(version="test_parser", mode="create", base_path="evaluation/evaluation_data")

    #Fill Database
    for portal in file:
        portal_name = portal["portal_name"]
        portal_url = portal["portal_url"]
        factchecks = portal["factchecks"]
        for link in factchecks:
            html = load_html(link)
            manager_by_llm.add_fact_check(portal_name, portal_url, link, extraction_llm(portal_name, html))
            manager_by_llm_directly.add_fact_check(portal_name, portal_url, link, extraction_llm_directly(portal_name, html))
            manager_by_parser.add_fact_check(portal_name, portal_url, link, extraction_normal(portal_name, html))

    #Export to csv
    manager_by_parser.export_as_csv(Path(__file__).resolve().parent / "evaluation_data" / "by_parser.csv")
    manager_by_llm.export_as_csv(Path(__file__).resolve().parent / "evaluation_data" / "by_llm.csv")
    manager_by_llm_directly.export_as_csv(Path(__file__).resolve().parent / "evaluation_data" / "by_llm_directly.csv")