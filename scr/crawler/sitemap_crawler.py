import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlpasrser, urlparse
from usp.tree import sitemap_tree_for_homepage

def search_sitemap_by_url(portal_name, portal_url):
    """
    :param portal_name: 
    :param (portal_url: 
    :return: 
    """
    urls = set()

    output_file = f"data/raw/{portal_name}_urls.txt"
    print(f"Searching sitemap for {portal_name}")

    try:
        tree = sitemap_tree_for_homepage(portal_url)
        all_pages = list(tree.all_pages())
        if all_pages:
            for page in all_pages:
                urls.add(page.url)
    except Exception as e:
        print(f"Sitemap Error: {e}")

    #Fallback if usp does not work
    if not urls:
        urls = manual_crawl(portal_url)

    if urls:
        with open(output_file, "w", encoding= "utf-8") as f:
            for url in urls:
                f.write(f"{url}\n")


def manual_crawl(url):
    urls = set()
    to_visit = [url]
    domain = urlpasrser(url).netloc

    while to_visit:
        current_url = to_visit.pop(0)
        if current_url in urls:
            continue
        try:
            urls.add(current_url)
            r= requests.get(current_url)
            soup = BeautifulSoup(r.text, "html.parser")
            for link in soup.find_all("a", href=True):
                full_url = urljoin(current_url, link["href"]).split('#')[0].rstrip('/')
                if urlparse(full_urls).netloc == domain and full_url not in urls:
                    to_visit.append(full_url)
        except Exception as e:
            print(f"Sitemap Manual Crawl Error: {e}")
            continue
    return urls