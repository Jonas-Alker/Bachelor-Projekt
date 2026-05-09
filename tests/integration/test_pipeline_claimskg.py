import os
from src.crawler.sitemap_crawler import search_sitemap_by_url
from src.crawler.url_filter import filter_urls
from src.analysis.claimskg_client import get_urls_from_claimskg

def test_url_extrakion():
    portal = "Politifact"
    url = "https://www.politifact.com/"
    raw_dir = "tests/test_data/raw"
    filtered_dir = "tests/test_data/filtered"
    analyse_dir = "tests/test_data/analysis"

    if not os.path.exists(raw_dir):
        os.makedirs(raw_dir)

    if not os.path.exists(filtered_dir):
        os.makedirs(filtered_dir)

    if not os.path.exists(analyse_dir):
        os.makedirs(analyse_dir)



    claimskg_urls = get_urls_from_claimskg(portal, year_end= 2013)
    claimskg_urls.update(get_urls_from_claimskg(portal, year_start=2016, year_end=2020))
    claimskg_urls.update(get_urls_from_claimskg(portal, year_start=2021))
    assert len(claimskg_urls) > 0

    search_sitemap_by_url(portal, url, base_dir= raw_dir)
    filter_urls(portal, input_base = raw_dir, output_base=filtered_dir)

    print("Test")
    file_new_data = f"{analyse_dir}/{portal}_new_urls.txt"
    file_missing_data = f"{analyse_dir}/{portal}_missing_from_crawler_urls.txt"

    filtered_path =f"{filtered_dir}/{portal}_filtered_urls.txt"
    with open(filtered_path, "r", encoding="utf-8") as f:
        crawled_urls = set(line.strip() for line in f)

    only_in_crawl = sorted(crawled_urls - claimskg_urls)
    only_in_claimskg_urls = sorted(claimskg_urls - crawled_urls)

    with open(file_missing_data, "w", encoding="utf-8") as f:
        f.write("\n".join(only_in_claimskg_urls))

    with open(file_new_data, "w", encoding="utf-8") as f:
        f.write("\n".join(only_in_crawl))