import json
import os
from src.crawler.sitemap_crawler import search_sitemap_by_url
from src.crawler.url_filter import filter_urls

def run_pipline():
    portals_config = "config/portals.json"

    if not os.path.exists(portals_config):
        print(f"Error: {portals_config} does not exist")
        return

    with open(portals_config, "r", encoding="utf-8") as f:
        portals = json.load(f)

    for portal in portals:
        name = portal["name"]
        url = portal["url"]

        search_sitemap_by_url(name, url)
        filter_urls(name)

if __name__ == "__main__":
    run_pipline()
