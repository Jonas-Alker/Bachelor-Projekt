import json
import os
from src.crawler.sitemap_crawler import search_sitemap_by_url
import src.storage.html_cache_manager as html_cache_manager
from src.storage.fact_check_manager import FactCheckManager

CONFIG_PORTALS = "config/portals.json"
LLM_BASED = False

def read_portals_config():
    if not os.path.exists(CONFIG_PORTALS):
        raise(f"Error: {CONFIG_PORTALS} does not exist")

    with open(CONFIG_PORTALS, "r", encoding="utf-8") as f:
        return json.load(f)

def crawl_all_portals(portals):
    html_db = html_cache_manager.HTMLCacheManager(version="v1", mode="create")
    for portal in portals:
        search_sitemap_by_url(portal["name"].lover(), portal["url"].lover(),html_db)
    return html_db

def preprocess(portal_name , html):
    return
def parse(portal_name , html, type):
    return
def save():
    return


def run_pipline():
    portals = read_portals_config()
    html_db = crawl_all_portals(portals)
    factcheck_db  = FactCheckManager(version="v1", mode="create")

    while factcheck := html_db.pop_next_page():
        portal_url = "" #This must be retrieved from the configuration or implemented in html_cache_manager.
        preprocessed = preprocess(factcheck['portal'], factcheck['html_content'])
        parsed = parse(factcheck.portal, preprocessed, LLM_BASED)
        factcheck_db.add_fact_check(factcheck['portal'], portal_url, factcheck["url"], parsed)










if __name__ == "__main__":
    run_pipline()
