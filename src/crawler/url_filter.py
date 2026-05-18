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

def filter_url(url, include, exclude):
    """Determines whether a given URL should be kept based on include and exclude rules

    :param url: The URL string to evaluate.
    :param include: A list of keywords that a URL must contain to be considered valid.
    :param exclude: A list of keywords that will cause a URL to be rejected immediately.
    :return: True if the URL passes the filtering criteria; False otherwise
    """
    if any(word in url for word in exclude):
        return False
    elif any(word in url for word in include):
        return True
    else:
        return False