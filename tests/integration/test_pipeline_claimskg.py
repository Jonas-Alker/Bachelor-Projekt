import os
from src.crawler.sitemap_crawler import search_sitemap_by_url
from src.crawler.url_filter import filter_urls
from src.analysis.claimskg_client import get_urls_from_claimskg
from src.storage.db_manager import DBManager


def test_get_urls_of_Test_Portal():
    portal = "Politifact"
    url = "https://www.politifact.com/"
    test_db_path = "tests/test_data/raw"
    manager = DBManager(version="test_ClaimsKg", mode="create", base_path=test_db_path)
    search_sitemap_by_url(portal, url, manager)
    del manager


def test_url_extrakion():
    portal = "Politifact"
    raw_dir = "tests/test_data/raw"
    filtered_dir = "tests/test_data/filtered"
    analyse_dir = "tests/test_data/analysis"

    test_db_path = "tests/test_data/raw"
    manager = DBManager(version="test_ClaimsKg", mode="load", base_path=test_db_path)

    if not os.path.exists(analyse_dir):
        os.makedirs(analyse_dir)

    claimskg_urls = get_urls_from_claimskg(portal, year_end= 2013)
    claimskg_urls.update(get_urls_from_claimskg(portal, year_start=2016, year_end=2020))
    claimskg_urls.update(get_urls_from_claimskg(portal, year_start=2021))

   ##assert len(claimskg_urls) > 0


    filter_urls(portal, input_base = raw_dir, output_base=filtered_dir)
