import json
import os


def load_rules(portal_name, config_path="config/filter_rules.json"):
    """Loads inclusion and exclusion rules for a specific portal from a JSON config file.
    If the specified portal configuration does not exist, it falls back to a 'default' rule set.
    If the entire configuration file is missing, hardcoded fallback lists
    are returned.

    :param portal_name: The name of the specific web portal.
    :param config_path: The file path to the JSON configuration file.
    :return: A tuple containing two lists of strings: (include_rules, exclude_rules).

    """

    if not(os.path.exists(config_path)):
        return ["artikel"],["impressum"]

    with open(config_path, "r", encoding="utf-8") as f:
        rules = json.load(f)

    portal_rules = rules.get(portal_name, rules.get("default"))
    return portal_rules["include"], portal_rules["exclude"]

def filter_urls(portal_name, input_base="data/raw", output_base="data/filtered"):
    include, exclude = load_rules(portal_name)

    input_file = (f"{input_base}/{portal_name}_urls.txt")
    if not os.path.exists(input_file):
        print(f"Input file {input_file} does not exist")
        return

    output_dir = output_base
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    output_file = (f"{output_dir}/{portal_name}_filtered_urls.txt")

    relevant_urls = []
    with open(input_file, "r", encoding="utf-8") as f:
        for line in f:
            url = line.strip().lower()

            if any(word in url for word in exclude):
                continue

            if any(word in url for word in include):
                relevant_urls.append(url)

    with open(output_file, "w", encoding="utf-8") as f:
        for url in relevant_urls:
            f.write(f"{url}\n")