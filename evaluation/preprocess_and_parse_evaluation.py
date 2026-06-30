import json
import re
import string
from difflib import SequenceMatcher
from pathlib import Path
import pandas as pd
from evaluation.claimskg_client import get_claim_details_by_url
import timeit

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
            manager_by_llm.add_fact_check(portal_name, portal_url, link, extraction_llm(portal_name, html))
            manager_by_llm_directly.add_fact_check(portal_name, portal_url, link, extraction_llm_directly(portal_name, html))
            manager_by_parser.add_fact_check(portal_name, portal_url, link, extraction_parser(portal_name, html))

    #Export to csv
    manager_by_parser.export_as_csv(Path(__file__).resolve().parent / "evaluation_data" / "output" / "by_parser.csv")
    manager_by_llm.export_as_csv(Path(__file__).resolve().parent / "evaluation_data" / "output" /"by_llm.csv")
    manager_by_llm_directly.export_as_csv(Path(__file__).resolve().parent / "evaluation_data" / "output" /"by_llm_directly.csv")

def _is_empty_value(val):
    """
    Returns whether the parameter passed is an empty parameter or a value that represents one

    :param val: value to be checked
    :return: outcome of the review
    """
    if pd.isna(val) or val == "N/A" or str(val).strip() == "" or str(val).lower() == "nan" or val is None:
        return True
    return False

def _clean_string(text):
    """
    Removes punctuation and white space from the passed string and converts all letters to lower case.
    Is used to check whether two strings are the same.

    :param text:  string to be processed
    :return: processed string
    """
    text = str(text)
    if _is_empty_value(text):
        return ""

    text = re.sub(r"\W+", "", text)
    return text.lower()

def _similarity(a, b):
    """
    Checks whether two strings are equal and returns a value between 0 and 1 that reflects the degree of similarity.

    :param a:  string a
    :param b:  string b
    :return:   match score between 0 and 1
    """

    return SequenceMatcher(None, _clean_string(a), _clean_string(b)).ratio()

def _compare_dates(date_kg, date_llm):
    """
    Compare two dates (source: ClaimsKG, LLM) with different formatting (YYYY-MM-DD; DD.MM.YYYY) for matching

    :param date_kg: date from ClaimsKg
    :param date_llm: date extracted from LLM
    :return: boolean (match)
    """
    if _is_empty_value(date_kg) and _is_empty_value(date_llm):
        return True
    if _is_empty_value(date_kg) or _is_empty_value(date_llm):
        return False

    try:
        d_kg = pd.to_datetime(date_kg).date()
        d_llm = pd.to_datetime(date_llm, dayfirst=True).date()
        return d_kg == d_llm
    except Exception:
        return False

def _compare_urls(url_a, url_b):
    """
    Compare two URLs (strings) to check if they are the same. Ignore ‘http://’, ‘https://’ and ‘www.’, as well as a ‘/’ at the end.

    :param url_a: first url
    :param url_b: second url
    :return: boolean (match)
    """
    if _is_empty_value(url_a) and _is_empty_value(url_b):
        return True
    if _is_empty_value(url_a) or _is_empty_value(url_b):
        return False

    clean_a = re.sub(r"^https?://(www\.)?", "", str(url_a)).strip("/")
    clean_b = re.sub(r"^https?://(www\.)?", "", str(url_b)).strip("/")

    return clean_a == clean_b

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

def _evaluate_to_csv(df_first_source, df_second_source, name_first, name_second, website_count, total_processing_time, output_path):
    """
    Compare data from given first source with the extracted data of a second source.
    A CSV file is created in `evaluation_data/output`, which compares the individual claims and shows the percentage match for each column.

    :param: df_claimsKG: dataframe of claims out of claimsKG
    :param: df_second_source: dataframe of second source (e.g. llm, parser )
    :param: website_count: number of websites tested
    :param: total_processing_time: total processing time of data obtaining
    :param: output_path: path to output file
    :return: CSV file in folder `evaluation_data/output`
    """

    shared_columns = [col for col in df_first_source.columns if col in df_second_source.columns and col != "article_url"]

    ## Matching Claims
    aligned_pairs = []
    unique_urls = sorted(list(set(df_first_source["article_url"].unique()) | set(df_second_source["article_url"].unique())))

    for url in unique_urls:
        s1_subset = df_first_source[df_first_source["article_url"] == url].to_dict('records')
        s2_subset = df_second_source[df_second_source["article_url"] == url].to_dict('records')

        all_pairs = []
        for s1_index, s1_row in enumerate(s1_subset):
            for s2_index, s2_row in enumerate(s2_subset):
                score = _similarity(s1_row.get("claim", ""), s2_row.get("claim", ""))
                all_pairs.append((s1_index, s2_index, score))

        all_pairs.sort(key=lambda x: x[2], reverse=True)

        used_s1_index = set()
        used_s2_index = set()

        # Add best matching claims
        for s1_idx, s2_idx, score in all_pairs:
            if s1_idx not in used_s1_index and s2_idx not in used_s2_index and score > 0.3:
                aligned_pairs.append((s1_subset[s1_idx], s2_subset[s2_idx]))

                used_s1_index.add(s1_idx)
                used_s2_index.add(s2_idx)

        # Treatment of the leftover claims
        for i, s1_row in enumerate(s1_subset):
            if i not in used_s1_index:
                aligned_pairs.append((s1_row, None))

        for j, s2_row in enumerate(s2_subset):
            if j not in used_s2_index:
                aligned_pairs.append((None, s2_row))

    ## Analysis and prepare CSV export

    alternating_data = []
    matches = {col: {"correct": 0, "total": 0} for col in shared_columns}

    for s1_row, s2_row in aligned_pairs:

        # Insert ClaimsKG line
        if s1_row:
            row_c = s1_row.copy()
            row_c["Source"] = name_first
            alternating_data.append(row_c)
        else:
            row_c = {col: None for col in shared_columns}
            row_c["Source"] = name_first
            row_c["article_url"] = s2_row.get("article_url", "")
            alternating_data.append(row_c)

        # Insert LLM line
        if s2_row:
            row_l = s2_row.copy()
            row_l["Source"] = name_second
            alternating_data.append(row_l)
        else:
            row_l = {col: None for col in shared_columns}
            row_l["Source"] = name_second
            row_l["article_url"] = s1_row.get("article_url", "")
            alternating_data.append(row_l)

        empty_row = {col: "" for col in shared_columns}
        empty_row["Source"] = ""
        empty_row["article_url"] = ""
        alternating_data.append(empty_row)

        # Check for matching
        if s1_row and s2_row:
            for col in shared_columns:
                val_s1 = s1_row.get(col)
                val_s2 = s2_row.get(col)

                if col in ["published_at", "stated_at"]:
                    if _compare_dates(val_s1, val_s2):
                        matches[col]["correct"] += 1

                elif col == "portal_url":
                    if _compare_urls(val_s1, val_s2):
                        matches[col]["correct"] += 1

                elif _clean_string(val_s1) == _clean_string(val_s2):
                    matches[col]["correct"] += 1

                matches[col]["total"] += 1

    for i in range(2):
        alternating_data.append({col: "" for col in shared_columns} | {"Source": "", "article_url": ""})

    # Add percentages
    title_row = {"Source": "column:", "article_url": ""}
    for col in shared_columns:
        title_row[col] = col
    alternating_data.append(title_row)

    evaluation_row = {"Source": "EQUIVALENCE:", "article_url": ""}
    for col in shared_columns:
        if matches[col]["total"] > 0:
            percent = (matches[col]["correct"] / matches[col]["total"]) * 100
            evaluation_row[col] = f"{percent:.2f}%"
        else:
            evaluation_row[col] = "N/A"

    alternating_data.append(evaluation_row)

    alternating_data.append({col: "" for col in shared_columns} | {"Source": "", "article_url": ""})

    # Add Metrics
    alternating_data.append({"Source": "Metrics:", "article_url": ""})
    alternating_data.append(({"Source": "Processing Time: ", "portal_name": f"{total_processing_time:.2f} sec"}))
    alternating_data.append({"Source": "Websites processed:", "portal_name": str(website_count)})

    alternating_data.append({col: "" for col in shared_columns} | {"Source": "", "article_url": ""})

    aligned_claims_s1 = set()
    aligned_claims_s2 = set()
    aligned_count = 0

    for s1_row, s2_row in aligned_pairs:
        if s1_row and s2_row:
            aligned_claims_s1.add((s1_row["article_url"], s1_row["claim"]))
            aligned_claims_s2.add((s2_row["article_url"], s2_row["claim"]))
            aligned_count += 1

    not_aligned_claims_s1 = 0
    not_aligned_claims_s2 = 0

    for s1_row, s2_row in aligned_pairs:
        if not s1_row:
            if (s2_row["article_url"], s2_row["claim"]) not in aligned_claims_s2:
                not_aligned_claims_s2 += 1
        if not s2_row:
            if (s1_row["article_url"], s1_row["claim"]) not in aligned_claims_s1:
                not_aligned_claims_s1 += 1

    total_claims_s1 = aligned_count + not_aligned_claims_s1
    total_claims_s2 = aligned_count + not_aligned_claims_s2

    perc_kg = (aligned_count / total_claims_s1 * 100) if total_claims_s1 > 0 else 0
    perc_llm = (aligned_count / total_claims_s2 * 100) if total_claims_s2 > 0 else 0

    alternating_data.append({"Source": "Alignment stats", "portal_name": ""})
    alternating_data.append(
        {"Source": f"{name_first} Aligned", "portal_name": f"{aligned_count} / {total_claims_s1} ({perc_kg:.2f}%)"})
    alternating_data.append(
        {"Source": f"{name_second} Aligned", "portal_name": f"{aligned_count} / {total_claims_s2} ({perc_llm:.2f}%)"})

    ## Make CSV
    df_export = pd.DataFrame(alternating_data)
    cols = ["article_url", "Source"] + [col for col in shared_columns]
    df_export = df_export[[c for c in cols if c in df_export.columns]]

    df_export.to_csv(output_path, index=False, sep=";", encoding="utf-8-sig")