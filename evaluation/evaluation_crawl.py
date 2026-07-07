from src.crawler.sitemap_crawler import search_sitemap_by_url
from src.crawler.url_filter import filter_url, load_rules
from evaluation.claimskg_client import get_urls_from_claimskg
from src.storage.html_cache_manager import HTMLCacheManager
def test_ClaimsKG_comparision():
    """
    Manual test to check whether URLs from Claims KG match those from the scraper. The output consists of two files,
    links that are only in Claims KG but not in the scraper results, and vice versa (tests/test_data/raw).
    """
    portal = "Politifact"
    url = "https://www.politifact.com/"
    test_db_path = "tests/test_data/raw"

    #Crawl
    manager_raw = HTMLCacheManager(version="test_ClaimsKg", mode="create", base_path=test_db_path)
    search_sitemap_by_url(portal, url, manager_raw)

    #Get Data
    db_urls = set(manager_raw.get_urls_by_portal(portal))
    raw_claimskg_urls = get_urls_from_claimskg(portal, year_end=2013)
    raw_claimskg_urls.update(get_urls_from_claimskg(portal, year_start=2016, year_end=2020))
    raw_claimskg_urls.update(get_urls_from_claimskg(portal, year_start=2021))
    claimskg_urls = {url.rstrip("/") for url in raw_claimskg_urls}

    #Compare
    only_in_claimskg = claimskg_urls - db_urls
    only_in_db = db_urls - claimskg_urls

    #Write
    with open("tests/test_data/raw/only_in_claimskg.txt", "w", encoding="utf-8") as f:
        for url in sorted(only_in_claimskg):
            f.write(f"{url}\n")

    with open("tests/test_data/raw/only_in_database.txt", "w", encoding="utf-8") as f:
        for url in sorted(only_in_db):
            f.write(f"{url}\n")

    del manager_raw


def test_clean_db():
    """
    To re-filter the test database that had already been crawled,
    if the filter had to be adjusted
    """
    portal = "Politifact"
    test_db_path = "tests/test_data/raw"
    test_source_path = "tests/test_data/raw/factencheck_test_ClaimsKg.db"

    manager = HTMLCacheManager(version="test_ClaimsKg", mode="load", base_path=test_db_path, source_path = test_source_path)
    urls = manager.get_urls_by_portal(portal)

    include, exclude = load_rules(portal)
    urls_to_delete = [url for url in urls if not filter_url(url, include, exclude)]

    if urls_to_delete:
        manager.delete_urls_bulk(urls_to_delete)
    del manager