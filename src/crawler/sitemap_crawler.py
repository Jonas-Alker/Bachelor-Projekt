import src.crawler.requester as requester
import src.crawler.link_parser as link_parser
from urllib.parse import urlparse
from usp.tree import sitemap_tree_for_homepage

def search_sitemap_by_url(portal_name, portal_url, db):
    """Orchestrates the crawling process for a specific portal using sitemaps.
    It first attempts to discover and parse the sitemap automatically. If the
    automatic discovery fails, it falls back to a manual breadth-first crawl
    of the portal's links.

    :param portal_name: The name of the web portal.
    :param portal_url: The root/homepage URL of the portal to crawl.
    :param db: The database manager instance used to persist crawled pages.
    """
    #Use usp to get sitemap automatically
    confirm = find_sitemap_automatically(portal_url, portal_name, db)

    #Fallback if usp does not work
    if not confirm:
        crawl_sitemap_manually(portal_url, portal_name, db)

def find_sitemap_automatically(start_url, portal, db):
    """Attempts to automatically discover, parse, and crawl a website's sitemap.

    :param start_url: The homepage URL where the sitemap discovery starts.
    :param portal: The name of the web portal.
    :param db: The database manager instance for saving HTML content.
    :return: True if pages were successfully found and processed via the sitemap;
        False otherwise (or if an error occurred).
    """
    try:
        tree = sitemap_tree_for_homepage(start_url)
        all_pages = list(tree.all_pages())
        if all_pages:
            for page in all_pages:
                r = requester.fetch_page(page)
                db.save_html(page, portal, r)

    except Exception as e:
        print(f"Sitemap Error: {e}")
    if all_pages:
        return True
    return False

def crawl_sitemap_manually(start_url, portal, db):
    """Performs a manual breadth-first crawl of a portal starting from its homepage.
    This acts as a fallback crawler. It keeps track of visited URLs using existing
    database entries, extracts internal sublinks from newly crawled pages, and
    recursively explores them until no more unvisited internal links remain.

    :param start_url: The homepage URL where the manual crawl begins.
    :param portal: The name of the portal being crawled.
    :param db: The database manager instance for saving HTML content.
    """
    visited_urls = set(db.get_urls_by_portal(portal))
    to_visit = {start_url: None}
    domain = urlparse(start_url).netloc

    while to_visit:
        current_url = next(iter(to_visit))

        if current_url in visited_urls:
            del to_visit[current_url]
            continue
        try:
            r = requester.fetch_page(current_url)
            visited_urls.add(current_url)

            db.save_html(current_url, portal, r)
            found_links = link_parser.extract_sublinks(r, current_url, domain)

            for link in found_links:
                if link not in visited_urls:
                    to_visit[link] = None
            del to_visit[current_url]
        except Exception as e:
            print(f"Sitemap Manual Crawl Error: {e}")
            continue