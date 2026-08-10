import json
import string
import timeit
import pandas as pd
import src.preprocessor.preprocessor_controller as preprocessor_controller
import src.parser.parser_controller as parser_controller

from pathlib import Path
from evaluation.claimskg_client import get_claim_details_by_url
from src.storage.fact_check_manager import FactCheckManager
from evaluation.evaluation_utils import load_html, _evaluate_to_exel

# =====================================================================
# 1. Configuration & Setup
# =====================================================================

def _load_json_data(file_path):
    """
    Loads the JSON file containing the portals and links to be evaluated.

    :param file_path: path of the JSON file to be loaded

    :return: list of dictionaries containing the parsed portal data and fact-check links
    """
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)

def _get_input_path(language):
    """
    Returns the corresponding ground truth path (folder) for the language passed.

    :param language: language for which the path is being searched

    :return: corresponding ground truth path (folder) for the language passed
    """
    if language == "english":
        return Path(__file__).resolve().parent / "evaluation_data" / "input" / "ground_truth" / "english"
    elif language == "german":
        return Path(__file__).resolve().parent / "evaluation_data" / "input" / "ground_truth" / "german"
    else:
        print("The error message still needs to be handled here")


# =====================================================================
# 2. Data Processing & Extraction
# =====================================================================

def _get_claimsKG_df(portals_data):
    """
    Extracts the claim data from ClaimsKg (if available)

    :param portals_data: all portal names, portal URLs and article URLs that need to be extracted, in schema from JSON

    :return:
            pd.DataFrame(claimsKG_results): DataFrame containing extracted data
            website_count: number of articles extracted
    """
    claimsKG_results = []
    website_count = 0

    ## Fill Database
    for portal in portals_data:
        for link in portal["factchecks"]:
            website_count += 1
            kg_details = get_claim_details_by_url(link)
            for claim_dict in kg_details:
                claimsKG_results.append(claim_dict)

    return pd.DataFrame(claimsKG_results), website_count

def _get_pipeline_df(portals_data, llm_based = True, preprocessed = False):
    """
    Extracts the claim data using the pipeline located in the src folder

    :param portals_data: all portal names, portal URLs and article URLs that need to be extracted, in schema from JSON
    :param llm_based: boolean that specifies whether extraction should be carried out directly via the LLM (True)
                    or via a generated parser (False)
    :param preprocessed: boolean that specifies whether the HTML should be pre-processed (True) or not (False)

    :return:
            pipeline_df: DataFrame containing extracted data
            website_count: number of articles extracted
            total_processing_time: duration of the extraction
    """
    pipline_db_manager = FactCheckManager(version="pipeline", mode="create", base_path="evaluation/evaluation_data/db")
    ##Metrics
    timer = timeit.default_timer
    total_processing_time = 0
    website_count = 0

    for portal in portals_data:
        portal_name = portal["portal_name"]
        portal_url = portal["portal_url"]
        for link in portal["factchecks"]:
            website_count += 1
            html = load_html(link)

            start_time = timer()
            if llm_based == True and preprocessed == False:
                data = parser_controller.parse(portal_name, html, True)

            elif llm_based == True and preprocessed == True:
                html_shortened = preprocessor_controller.preprocess(portal_name, html)
                data = parser_controller.parse(portal_name, html_shortened, True)

            elif llm_based == False and preprocessed == False:
                data = parser_controller.parse(portal_name, html, False)

            else:
                html_shortened = preprocessor_controller.preprocess(portal_name, html)
                data = parser_controller.parse(portal_name, html_shortened, False)
            total_processing_time += timer() - start_time

            pipline_db_manager.add_fact_check(portal_name, portal_url, link, data)

        pipeline_df = pipline_db_manager.get_as_pd()
    return pipeline_df , website_count, total_processing_time

def _get_ground_truth_df(path):
    """
    Provides a dataframe containing the specified ground truth folder and the associated
    portal_data (portal names, portal URLs, article URLs) for further evaluation.

    :param path: path to the folder from which the ground truth data is to be taken

    :return:
            ground_truth_df: DataFrame containing ground truth data
            portals_data: all portal names, portal URLs and article URLs that need to be extracted,in same schema as JSON
    """
    ground_truth_results = []

    ## Fill Database
    csv_files = list(path.glob("*.csv"))
    for file_path in csv_files:
        df = pd.read_csv(file_path, dtype=str)
        ground_truth_results.append(df)
    ground_truth_df = pd.concat(ground_truth_results, ignore_index=True)

    ## Build Portal_data for further use
    portals_data = []

    # 2. Group the DataFrame by portal to replicate the JSON structure
    grouped = ground_truth_df.groupby(["portal_name", "portal_url"])

    for (portal_name, portal_url), group in grouped:
        unique_links = group["article_url"].dropna().unique().tolist()

        portals_data.append({
            "portal_name": str(portal_name),
            "portal_url": str(portal_url),
            "factchecks": unique_links
        })

    return ground_truth_df, portals_data


# =====================================================================
# 3. Evaluation calls
# =====================================================================

def test_llm_directly_extraction_quality_against_ground_truth(language = "english"):
    """
    Evaluates direct LLM extraction against ground_truth data (evaluation_data/input/ground_truth) for the language given
    and outputs the data in an xlsx file (evaluation_data/output/llm_directly_against_ground_truth_{language}.xlsx)

    :param language: language of ground_truth data that will be used in test
    """
    ground_truth_df, portals_data = _get_ground_truth_df(_get_input_path(language))
    pipeline_df , website_count, total_processing_time =_get_pipeline_df(portals_data, llm_based= True, preprocessed= False)
    output_path = Path(__file__).resolve().parent / "evaluation_data" / "output" / f"llm_directly_against_ground_truth_{language}.xlsx"
    _evaluate_to_exel(ground_truth_df,pipeline_df, "ground_truth", "LLM_direct", website_count, total_processing_time, output_path)

def test_llm_preprocessed_extraction_quality_against_ground_truth(language = "english"):
    """
    Evaluates preprocessed LLM extraction against ground_truth data (evaluation_data/input/ground_truth) for the language given
    and outputs the data in an xlsx file (evaluation_data/output/llm_preprocessed_against_ground_truth_{language}.xlsx)

    :param language: language of ground_truth data that will be used in test
    """
    ground_truth_df, portals_data = _get_ground_truth_df(_get_input_path(language))
    pipeline_df , website_count, total_processing_time =_get_pipeline_df(portals_data, llm_based= True, preprocessed= True)
    output_path = Path(__file__).resolve().parent / "evaluation_data" / "output" / f"llm_preprocessed_against_ground_truth_{language}.xlsx"
    _evaluate_to_exel(ground_truth_df,pipeline_df, "ground_truth", "LLM_preprocessed", website_count, total_processing_time, output_path)

def test_claims_kg_quality_against_ground_truth():
    """
    Evaluates claims_kg data against ground_truth data (evaluation_data/input/ground_truth) for english portals
    and outputs the data in an xlsx file (evaluation_data/output/claims_kg_against_ground_truth.xlsx)
    """
    ground_truth_df, portals_data = _get_ground_truth_df(_get_input_path("english"))
    portal_data = _load_json_data(Path(__file__).resolve().parent / "evaluation_data" / "input" / "claim_comparison_claimsKG.json")
    claimsKG_df, _ = _get_claimsKG_df(portal_data)
    output_path = Path(__file__).resolve().parent / "evaluation_data" / "output" / "claims_kg_against_ground_truth.xlsx"
    _evaluate_to_exel(ground_truth_df,claimsKG_df, "ground_truth", "ClaimsKG", -1, 0, output_path)

def test_parser_against_ground_truth(language = "english"):
    """
    Evaluates generated parser extraction against ground_truth data (evaluation_data/input/ground_truth) for the language given
    and outputs the data in an xlsx file (evaluation_data/output/parser_against_ground_truth_{language}.xlsx)

    :param language: language of ground_truth data that will be used in test
    """
    ground_truth_df, portals_data = _get_ground_truth_df(_get_input_path(language))
    pipeline_df, website_count, total_processing_time = _get_pipeline_df(portals_data, llm_based=False,  preprocessed=False)
    output_path = Path(__file__).resolve().parent / "evaluation_data" / "output" / f"parser_against_ground_truth_{language}.xlsx"
    _evaluate_to_exel(ground_truth_df, pipeline_df, "ground_truth", "generated_parser", website_count, total_processing_time, output_path)


# =====================================================================
# 4. Outdated evaluation methods
# =====================================================================

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

def test_parser_against_claims_kg():
    """
    Evaluates generated parser extraction against Claims KG and
    outputs the data in an xlsx file (evaluation_data/output/parser_against_claims_kg.xlsx)
    """
    portal_data = _load_json_data(Path(__file__).resolve().parent / "evaluation_data" / "input" / "claim_comparison_claimsKG.json")
    claimsKG_df, _ = _get_claimsKG_df(portal_data)
    pipeline_df, website_count, total_processing_time = _get_pipeline_df(portal_data, llm_based=False, preprocessed=False)
    output_path = Path(__file__).resolve().parent / "evaluation_data" / "output" / "parser_against_claims_kg.xlsx"
    _evaluate_to_exel(claimsKG_df, pipeline_df, "ClaimsKG", "generated_parser", website_count, total_processing_time, output_path)

def test_llm_preprocessed_extraction_quality_against_claims_kg():
    """
    Evaluates preprocessed LLM extraction against Claims KG and
    outputs the data in an xlsx file (evaluation_data/output/llm_preprocessed_against_claims_kg.xlsx)
    """
    portal_data = _load_json_data(Path(__file__).resolve().parent / "evaluation_data" / "input" / "claim_comparison_claimsKG.json")
    claimsKG_df, _ = _get_claimsKG_df(portal_data)
    pipeline_df, website_count, total_processing_time = _get_pipeline_df(portal_data, llm_based=True, preprocessed=True)
    output_path = Path(__file__).resolve().parent / "evaluation_data" / "output" / "llm_preprocessed_against_claims_kg.xlsx"
    _evaluate_to_exel(claimsKG_df, pipeline_df, "ClaimsKG", "LLM_direct", website_count, total_processing_time, output_path)

def test_llm_directly_extraction_quality_against_claims_kg():
    """
    Evaluates direct LLM extraction against Claims KG and
    outputs the data in an xlsx file (evaluation_data/output/llm_directly_against_claims_kg.xlsx)
    """
    portal_data = _load_json_data(Path(__file__).resolve().parent / "evaluation_data" / "input" / "claim_comparison_claimsKG.json")
    claimsKG_df, _ = _get_claimsKG_df(portal_data)
    pipeline_df , website_count, total_processing_time = _get_pipeline_df(portal_data, llm_based= True, preprocessed= False)
    output_path = Path(__file__).resolve().parent / "evaluation_data" / "output" / "llm_directly_against_claims_kg.xlsx"
    _evaluate_to_exel(claimsKG_df, pipeline_df ,"ClaimsKG", "LLM_direct", website_count, total_processing_time, output_path)
