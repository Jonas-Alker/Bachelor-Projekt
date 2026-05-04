import json
import os


def load_rules(portal_name):
    """
    :param portal_name:
    :return:
    """
    config_path = "config/filter_rules.json"

    if  not(os.path.exists(config_path)):
        return ["artikel"],["impressum"]

    with open(config_path, "r", encoding="utf-8") as f:
        rules = json.load(f)

    portal_rules = rules.get(portal_name, rules.get("default"))
    return portal_rules["include"], portal_rules["exclude"]

def filter_urls(portal_name):
    include, exclude = load_rules(portal_name)

    input_file = (f"data/raw/{portal_name}_urls.txt")
    if not os.path.exists(input_file):
        print(f"Input file {input_file} does not exist")
        return

    output_dir = "data/filtered"
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