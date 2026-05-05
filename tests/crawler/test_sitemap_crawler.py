import os
from src.crawler.sitemap_crawler import (
    search_sitemap_by_url,
    find_sitemap_automatically,
    crawl_sitemap_manually)


def test_crawler_output_file_creation():
    test_dir = "tests/test_data/raw"
    if not os.path.exists(test_dir):
        os.makedirs(test_dir)

    portal = "unit_test_portal"
    url = "https://www.mimikama.org/"#
    expected_file = f"{test_dir}/{portal}_urls.txt"

    if os.path.exists(expected_file):
        os.remove(expected_file)

    search_sitemap_by_url(portal, url, base_dir=test_dir)

    print(f"Expected file {expected_file}")
    assert os.path.exists(expected_file)

def test_find_sitemap_automatically():
    url = "https://www.mimikama.org/"

    urls = find_sitemap_automatically(url)

    assert isinstance(urls, set)
    assert len(urls) > 1
    for found_url in urls:
        assert "mimikama" in found_url

def test_crawl_sitemap_manually():
    url = "https://www.mimikama.org/"

    urls = crawl_sitemap_manually(url)

    assert len(urls) > 1
    for found_url in urls:
        assert "mimikama" in found_url