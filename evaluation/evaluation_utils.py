import re
import requests
import pandas as pd
import src.crawler.sitemap_crawler as sitemap_crawler

from datetime import datetime
from typing import Any, Literal
from difflib import SequenceMatcher
from pandas import DataFrame, Series


# =====================================================================
# 1. Common support methods & validation
# =====================================================================

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
    :return: the processed string
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

def _extract_set_values(val):
    """
    Checks whether a value is contained within {...} and returns the individual elements, separated by commas or semicolons, as a list.

    :param val: value to be checked
    :return: individual elements as a list
    """
    if _is_empty_value(val):
        return []

    val_str = str(val).strip()
    if val_str.startswith("{") and val_str.endswith("}"):
        inner = val_str[1:-1]
        parts = re.split(r'[,;]', inner)
        return [p.strip() for p in parts if p.strip()]

    return [val_str]

def load_html(url):
    """
    Downloads the HTML from the URL provided.

    :param url: url to download
    :return: HTML content
    """
    return sitemap_crawler.fetch_page(url)


def _parse_date_safe(d_str):
    """
    Convert a supplied string into date where possible. The formats YYYY-MM-DD and DD.MM.YYYY are accepted.

    :param d_str: date string
    :return: corresponding datetime or None
    """
    # 1. Try: ISO-Norm (z.B. YYYY-MM-DD)
    try:
        return datetime.strptime(d_str, "%Y-%m-%d").date()
    except ValueError:
        pass

    # 2. Try: European (z.B. DD.MM.YYYY)
    try:
        return datetime.strptime(d_str, "%d.%m.%Y").date()
    except ValueError:
        return None


# =====================================================================
# 2. Precise comparison logic (dates, URLs, strings)
# =====================================================================

def _compare_dates(date_a, date_b):
    """
    Compare two dates (source: ClaimsKG, LLM) with different formatting (YYYY-MM-DD; DD.MM.YYYY) for matching

    :param date_a: first date to compare
    :param date_b: second date to compare
    :return: boolean (match)
    """
    if _is_empty_value(date_a) and _is_empty_value(date_b):
        return True
    if _is_empty_value(date_a) or _is_empty_value(date_b):
        return False

    vals_a = _extract_set_values(date_a)
    vals_b = _extract_set_values(date_b)

    for a in vals_a:
        d_a = _parse_date_safe(a)
        if d_a is None:
            continue  #Skip if 'a' is definitely not a date

        for b in vals_b:
            d_b = _parse_date_safe(b)
            if d_b is None:
                continue
            if d_a == d_b:
                return True

    return False

def _compare_strings(val_a, val_b):
    """
    Compares two strings. Supports list notation {...,...}.
    Checks whether an element matches exactly or whether ALL elements of the set are contained in the other string.

    :param val_a: first string to compare
    :param val_b: second string to compare
    :return: boolean (match)
    """
    if _is_empty_value(val_a) and _is_empty_value(val_b):
        return True
    if _is_empty_value(val_a) or _is_empty_value(val_b):
        return False

    vals_a = _extract_set_values(val_a)
    vals_b = _extract_set_values(val_b)

    # 1. Exact match of at least one element
    for a in vals_a:
        for b in vals_b:
            if _clean_string(a) == _clean_string(b):
                return True

    # 2. Check whether *all* elements from the {...} block appear in the other string
    # (e.g. ground_truth: "{Author A, Author B}", LLM: "Author A - Author B")
    str_a_clean = _clean_string(str(val_a))
    str_b_clean = _clean_string(str(val_b))

    if len(vals_a) > 1:
        all_in_b = all(_clean_string(a) in str_b_clean for a in vals_a)
        if all_in_b: return True

    if len(vals_b) > 1:
        all_in_a = all(_clean_string(b) in str_a_clean for b in vals_b)
        if all_in_a: return True

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


# =====================================================================
# 3. Alignment and Match Matrix Generation
# =====================================================================

def _align_pairs(df_first_source, df_second_source):
    """
    Pairs the claims from both DataFrames based on URL and claim similarity.

    :param df_first_source: dataframe containing claims from the first source
    :param df_second_source: dataframe containing claims from the second source
    :return: list of aligned_pairs
    """
    aligned_pairs = []
    unique_urls = sorted(
        list(set(df_first_source["article_url"].unique()) | set(df_second_source["article_url"].unique())))

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

    return aligned_pairs

def _get_match_matrix(aligned_pairs, shared_columns):
    """
    Checks the pairs for matches for each split column.
    Returns a DataFrame containing:
      1 : Match
      0 : No match (values differ)
     -1 : No match found (only one claim exists)

    :param aligned_pairs: list of tuples aligned claims
    :param shared_columns: list of shared columns

    :return: DataFrame containing matches for each split column
    """
    match_data = []

    for s1_row, s2_row in aligned_pairs:
        match_row = {}
        for col in shared_columns:
            # By default, -1 if a partner is missing
            if not s1_row or not s2_row:
                match_row[col] = -1
            else:
                val_s1 = s1_row.get(col)
                val_s2 = s2_row.get(col)

                is_match = False
                if col in ["published_at", "stated_at"]:
                    is_match = _compare_dates(val_s1, val_s2)
                elif col == "portal_url":
                    is_match = _compare_urls(val_s1, val_s2)
                else:
                    is_match = _compare_strings(val_s1, val_s2)

                # 1 for a match, 0 for a mismatch
                match_row[col] = 1 if is_match else 0

        match_data.append(match_row)

    return pd.DataFrame(match_data)


# =====================================================================
# 4. Evaluation & Excel Export
# =====================================================================

def _evaluate_to_exel(df_first_source, df_second_source, name_first, name_second, website_count, total_processing_time, output_path):
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

    ## Align and calculate matches
    aligned_pairs = _align_pairs(df_first_source, df_second_source)
    df_matches = _get_match_matrix(aligned_pairs, shared_columns)

    ## Analysis and prepare CSV export
    alternating_data = []
    matches_stats = {col: {"correct": 0, "total": 0} for col in shared_columns}

    for idx, (s1_row, s2_row) in enumerate(aligned_pairs):
        match_row = df_matches.iloc[idx]  # Retrieve the matching values (-1, 0, 1) for this pair

        # Insert Source 1 line
        if s1_row:
            row_c = s1_row.copy()
        else:
            row_c = {col: None for col in shared_columns}
            row_c["article_url"] = s2_row.get("article_url", "")
        row_c["Source"] = name_first
        alternating_data.append(row_c)

        # Insert Source 2 line
        if s2_row:
            row_l = s2_row.copy()
        else:
            row_l = {col: None for col in shared_columns}
            row_l["article_url"] = s1_row.get("article_url", "")
        row_l["Source"] = name_second
        alternating_data.append(row_l)

        # Insert Empty line
        empty_row = {col: "" for col in shared_columns}
        empty_row["Source"] = ""
        empty_row["article_url"] = ""
        alternating_data.append(empty_row)

        # Check for matching (via Match-Matrix)
        for col in shared_columns:
            val = match_row[col]
            if val != -1:  #If both are present
                matches_stats[col]["total"] += 1
                if val == 1:
                    matches_stats[col]["correct"] += 1

    for i in range(2):
        alternating_data.append({col: "" for col in shared_columns} | {"Source": "", "article_url": ""})

    # Add percentages
    title_row = {"Source": "column:", "article_url": ""}
    for col in shared_columns:
        title_row[col] = col
    alternating_data.append(title_row)

    evaluation_row = {"Source": "EQUIVALENCE:", "article_url": ""}
    for col in shared_columns:
        if matches_stats[col]["total"] > 0:
            percent = (matches_stats[col]["correct"] / matches_stats[col]["total"]) * 100
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

    _append_alignment_stats(aligned_pairs, alternating_data, name_first, name_second)

    ## Make Excel
    df_export = pd.DataFrame(alternating_data)
    cols = ["article_url", "Source"] + [col for col in shared_columns]
    df_export = df_export[[c for c in cols if c in df_export.columns]]
    df_export = df_export.fillna("")

    _write_excel(df_export, df_matches, output_path, shared_columns)


def _write_excel(df_export: Series | DataFrame | Any, df_matches: DataFrame, output_path,
                 shared_columns: list[Literal["article_url"] | Any]):
    """
    Write the DataFrame to Excel and format the cells with colors based on the match matrix.

    :param df_export: DataFrame with claims
    :param df_matches: DataFrame with data od cell based matches
    :param output_path: output path for the Excel file
    :param shared_columns: columns that appear in both data sources contained in df_export
    """
    writer = pd.ExcelWriter(output_path, engine='xlsxwriter')
    df_export.to_excel(writer, index=False, sheet_name='Evaluation')

    workbook = writer.book
    worksheet = writer.sheets['Evaluation']

    # Define colors formats
    format_match = workbook.add_format({'bg_color': '#C6EFCE', 'font_color': '#006100'})  # Green (+1)
    format_mismatch = workbook.add_format({'bg_color': '#FFC7CE', 'font_color': '#9C0006'})  # Red (0)
    format_missing = workbook.add_format({'bg_color': '#F2F2F2', 'font_color': '#7A7A7A'})  # Grey(-1)

    # Mapping column names to an Excel index
    col_idx_map = {col_name: idx for idx, col_name in enumerate(df_export.columns)}

    # Applying colors
    for idx, match_row in df_matches.iterrows():
        # As we are inserting 3 lines per pair (S1, S2, blank) and line 0 is the header:
        excel_row_s1 = idx * 3 + 1
        excel_row_s2 = idx * 3 + 2

        for col in shared_columns:
            if col in col_idx_map:
                excel_col = col_idx_map[col]
                match_val = match_row[col]

                # We’ll retrieve the text that actually belongs in the cell
                val_s1 = df_export.iloc[excel_row_s1 - 1, excel_col]
                val_s2 = df_export.iloc[excel_row_s2 - 1, excel_col]

                # Assign a format based on the match matrix
                if match_val == 1:
                    worksheet.write(excel_row_s1, excel_col, val_s1, format_match)
                    worksheet.write(excel_row_s2, excel_col, val_s2, format_match)
                elif match_val == 0:
                    worksheet.write(excel_row_s1, excel_col, val_s1, format_mismatch)
                    worksheet.write(excel_row_s2, excel_col, val_s2, format_mismatch)
                elif match_val == -1:
                    worksheet.write(excel_row_s1, excel_col, val_s1, format_missing)
                    worksheet.write(excel_row_s2, excel_col, val_s2, format_missing)

    writer.close()


def _append_alignment_stats(aligned_pairs: list[Any], alternating_data: list[Any], name_first, name_second):
    """
    Calculates the alignment statistics and appends them to the export data.

    :param aligned_pairs: dataframe with aligned claims
    :param alternating_data: dataframe with alternating claims (append statistics here)
    :param name_first: name of first data source
    :param name_second: name of second data source
    """
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