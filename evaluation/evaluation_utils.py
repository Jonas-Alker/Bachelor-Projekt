import re
import requests
import string
import pandas as pd

from difflib import SequenceMatcher

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

def _extract_set_values(val):
    """
    Prüft ob ein Wert in {...} steht und gibt die einzelnen Elemente als Liste zurück.
    Trennt bei Komma oder Semikolon. Andernfalls wird der Wert als 1-Element-Liste zurückgegeben.
    """
    if _is_empty_value(val):
        return []

    val_str = str(val).strip()
    if val_str.startswith("{") and val_str.endswith("}"):
        inner = val_str[1:-1]
        parts = re.split(r'[,;]', inner)
        return [p.strip() for p in parts if p.strip()]

    return [val_str]

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
        for b in vals_b:
            try:
                d_a = pd.to_datetime(a, dayfirst=True).date()
                d_b = pd.to_datetime(b, dayfirst=True).date()
                if d_a == d_b:
                    return True
            except Exception:
                continue
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

def _compare_strings(val_a, val_b):
    """
    Vergleicht zwei Strings. Unterstützt {...} Notation.
    Prüft ob ein Element exakt passt oder ob ALLE Elemente des Sets im anderen String enthalten sind.
    """
    if _is_empty_value(val_a) and _is_empty_value(val_b):
        return True
    if _is_empty_value(val_a) or _is_empty_value(val_b):
        return False

    vals_a = _extract_set_values(val_a)
    vals_b = _extract_set_values(val_b)

    # 1. Direkter Match von mindestens einem Element
    for a in vals_a:
        for b in vals_b:
            if _clean_string(a) == _clean_string(b):
                return True

    # 2. Prüfen, ob *alle* Elemente aus dem {...}-Block im anderen String vorkommen
    # (z.B. Goldstandard: "{Autor A, Autor B}", LLM: "Autor A - Autor B")
    str_a_clean = _clean_string(str(val_a))
    str_b_clean = _clean_string(str(val_b))

    if len(vals_a) > 1:
        all_in_b = all(_clean_string(a) in str_b_clean for a in vals_a)
        if all_in_b: return True

    if len(vals_b) > 1:
        all_in_a = all(_clean_string(b) in str_a_clean for b in vals_b)
        if all_in_a: return True

    return False

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
    aligned_pairs = _align_pairs(df_first_source, df_second_source)

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

                elif _compare_strings(val_s1, val_s2):
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

def _align_pairs(df_first_source, df_second_source):
    """

    :param df_first_source:
    :param df_second_source:
    :return:
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
