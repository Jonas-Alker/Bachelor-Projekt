import json
import string
import timeit
import pandas as pd
import src.preprocessor.preprocessor_controller as preprocessor_controller
import src.parser.parser_controller as parser_controller

from pathlib import Path
from evaluation.claimskg_client import get_claim_details_by_url
from src.storage.fact_check_manager import FactCheckManager
from evaluation.evaluation_utils import load_html, _evaluate_to_csv


def extraction_llm_preprocessed(portal, html):
    """
    Forwards the method call for extraction. The HTML is pre-processed and then parsed using an LLM.

    :param portal: name of portal
    :param html: HTML from which data is to be extracted

    :return: extraction data
    """
    html_shortened = preprocessor_controller.preprocess(portal, html)
    return parser_controller.parse(portal, html_shortened, True)

def extraction_llm_directly(portal, html):
    """
    Forwards the method call for extraction. The HTML is NOT pre-processed but parsed directly using an LLM.

    :param portal: name of portal
    :param html: HTML from which data is to be extracted

    :return: extraction data
    """
    return parser_controller.parse(portal, html, True)

def extraction_parser(portal, html):
    """
    Forwards the method call for extraction. The HTML is parsed using the generated parser scripts.

    :param portal: name of portal
    :param html: HTML from which data is to be extracted

    :return: extraction data
    """
    return parser_controller.parse(portal, html, False)

def test_extraction():
    """
    Test the extraction using sample fact-checks stored in `evaluation_data/evaluation_portals.json`.
    Three different approaches are tested:
    1. Direct LLM extraction (without pre-processing)
    2. LLM extraction with prior pre-processing
    3. Extraction via pre-generated parser scripts with pre-processing

    The results are stored in a database and also exported as CSV files in the ‘evaluation_data’ folder.
    """
    #Load evaluation_data
    data_path = Path(__file__).resolve().parent / "evaluation_data" / "input" / "evaluation_portals.json"
    with open(data_path, "r") as f:
        file = json.load(f)

    #Create Databases
    manager_by_llm = FactCheckManager(version="test_llm", mode="create", base_path="evaluation/evaluation_data/db")
    manager_by_llm_directly = FactCheckManager(version="test_llm_directly", mode="create", base_path="evaluation/evaluation_data/db")
    manager_by_parser = FactCheckManager(version="test_parser", mode="create", base_path="evaluation/evaluation_data/db")

    #Fill Database
    for portal in file:
        portal_name = portal["portal_name"]
        portal_url = portal["portal_url"]
        for link in portal["factchecks"]:
            html = load_html(link)
            manager_by_llm.add_fact_check(portal_name, portal_url, link, extraction_llm_preprocessed(portal_name, html))
            manager_by_llm_directly.add_fact_check(portal_name, portal_url, link, extraction_llm_directly(portal_name, html))
            manager_by_parser.add_fact_check(portal_name, portal_url, link, extraction_parser(portal_name, html))

    #Export to csv
    manager_by_parser.export_as_csv(Path(__file__).resolve().parent / "evaluation_data" / "output" / "by_parser.csv")
    manager_by_llm.export_as_csv(Path(__file__).resolve().parent / "evaluation_data" / "output" /"by_llm.csv")
    manager_by_llm_directly.export_as_csv(Path(__file__).resolve().parent / "evaluation_data" / "output" /"by_llm_directly.csv")

def test_llm_extraction_quality_against_claims_kg():
    ## Load evaluation_data
    data_path = Path(__file__).resolve().parent / "evaluation_data" / "input" / "claim_comparison_claimsKG.json"
    with open(data_path, "r") as f:
        file = json.load(f)

    ## Create Databases
    manager_by_llm = FactCheckManager(version="test_llm", mode="create", base_path="evaluation/evaluation_data/db")
    claimsKG_results = []

    ##Metrics
    timer = timeit.default_timer
    total_processing_time = 0
    website_count = 0

    ## Fill Database
    for portal in file:
        portal_name = portal["portal_name"]
        portal_url = portal["portal_url"]
        for link in portal["factchecks"]:
            website_count += 1
            html = load_html(link)

            start_time = timer()
            manager_by_llm.add_fact_check(portal_name, portal_url, link, extraction_llm_directly(portal_name, html))
            total_processing_time += timer() - start_time

            kg_details = get_claim_details_by_url(link)
            for claim_dict in kg_details:
                claimsKG_results.append(claim_dict)

    ## Preparing Data
    df_claimsKG = pd.DataFrame(claimsKG_results)
    df_llm = manager_by_llm.get_as_pd()

    ##Comparison
    output_path = Path(__file__).resolve().parent / "evaluation_data" / "output" /"evaluation_claims_vs_llm.csv"
    _evaluate_to_csv(df_claimsKG, df_llm,"ClaimsKG","LLM",website_count,total_processing_time, output_path)

def test_llm_extraction_against_parser():
    ## Load evaluation_data
    data_path = Path(__file__).resolve().parent / "evaluation_data" / "input" / "claim_comparison_claimsKG.json"
    with open(data_path, "r") as f:
        file = json.load(f)

    ## Create Databases
    manager_by_llm = FactCheckManager(version="test_llm", mode="create", base_path="evaluation/evaluation_data/db")
    manager_by_parser = FactCheckManager(version="test_parser", mode="create", base_path="evaluation/evaluation_data/db")

    ##Metrics
    website_count = 0

    ## Fill Database
    for portal in file:
        portal_name = portal["portal_name"]
        portal_url = portal["portal_url"]
        for link in portal["factchecks"]:
            website_count += 1
            html = load_html(link)

            manager_by_parser.add_fact_check(portal_name, portal_url, link, extraction_parser(portal_name, html))
            manager_by_llm.add_fact_check(portal_name, portal_url, link, extraction_llm_directly(portal_name, html))


    ## Preparing Data
    df_parser = manager_by_parser.get_as_pd()
    df_llm = manager_by_llm.get_as_pd()

    ##Comparison
    output_path = Path(__file__).resolve().parent / "evaluation_data" / "output" /"evaluation_parser_vs_llm.csv"
    _evaluate_to_csv(df_parser, df_llm,"Parser", "LLM",website_count,-1, output_path, )

def test_parser_extraction_against_claims_kg():
    ## Load evaluation_data
    data_path = Path(__file__).resolve().parent / "evaluation_data" / "input" / "claim_comparison_claimsKG.json"
    with open(data_path, "r") as f:
        file = json.load(f)

    ## Create Databases
    manager_by_parser = FactCheckManager(version="test_parser", mode="create", base_path="evaluation/evaluation_data/db")
    claimsKG_results = []

    ##Metrics
    timer = timeit.default_timer
    total_processing_time = 0
    website_count = 0

    ## Fill Database
    for portal in file:
        portal_name = portal["portal_name"]
        portal_url = portal["portal_url"]
        for link in portal["factchecks"]:
            website_count += 1
            html = load_html(link)

            start_time = timer()
            manager_by_parser.add_fact_check(portal_name, portal_url, link, extraction_parser(portal_name, html))
            total_processing_time += timer() - start_time

            kg_details = get_claim_details_by_url(link)
            for claim_dict in kg_details:
                claimsKG_results.append(claim_dict)

    ## Preparing Data
    df_claimsKG = pd.DataFrame(claimsKG_results)
    df_parser = manager_by_parser.get_as_pd()

    ##Comparison
    output_path = Path(__file__).resolve().parent / "evaluation_data" / "output" / "evaluation_claims_vs_parser.csv"
    _evaluate_to_csv(df_claimsKG, df_parser,"ClaimsKG","Parser", website_count, total_processing_time, output_path)

def test_llm_extraction_against_ground_truth():
    ## Create Databases
    folder_path = Path(__file__).resolve().parent / "evaluation_data" / "input" / "ground_truth" / "english"
    csv_files = list(folder_path.glob("*.csv"))
    df_list = []
    for file_path in csv_files:
        df = pd.read_csv(file_path, dtype=str)
        df_list.append(df)
    df_ground_truth = pd.concat(df_list, ignore_index=True)
    manager_by_llm = FactCheckManager(version="test_llm_ground_truth", mode="create", base_path="evaluation/evaluation_data/db")


    ##Metrics
    timer = timeit.default_timer
    total_processing_time = 0
    website_count = 0

    unique_portal = []

    ## Fill Database
    for index, row in df_ground_truth.iterrows():
        link = row["article_url"]
        portal_name = row.get("portal_name", "Unknown")
        portal_url = row.get("portal_url", "")

        website_count += 1
        html = load_html(link)

        if html:
            start_time = timer()
            manager_by_llm.add_fact_check(portal_name, portal_url, link,  extraction_llm_directly(portal_name, html))
            total_processing_time += timer() - start_time


    df_llm = manager_by_llm.get_as_pd()

    output_path = Path(
        __file__).resolve().parent / "evaluation_data" / "output" / f"evaluation_ground_truth_vs_llm.csv"
    _evaluate_to_csv(df_ground_truth, df_llm, "ground_truth", "LLM", website_count, total_processing_time, output_path)