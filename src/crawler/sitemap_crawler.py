import src.crawler.requester as requester
import src.crawler.link_parser as link_parser
import src.crawler.url_filter as url_filter
from urllib.parse import urlparse
from usp.tree import sitemap_tree_for_homepage
import logging

#Getting Logger
logger = logging.getLogger(__name__)

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
        logger.info(f"Automatic sitemap discovery failed for '{portal_name}'. Falling back to manual crawl.")
        crawl_sitemap_manually(portal_url, portal_name, db)
    else:
        logger.info(f"Successfully finished automatic sitemap crawl for '{portal_name}'.")

def find_sitemap_automatically(start_url, portal, db):
    """Attempts to automatically discover, parse, and crawl a website's sitemap.

    :param start_url: The homepage URL where the sitemap discovery starts.
    :param portal: The name of the web portal.
    :param db: The database manager instance for saving HTML content.
    :return: True if pages were successfully found and processed via the sitemap;
        False otherwise (or if an error occurred).
    """
    all_pages = []
    try:
        tree = sitemap_tree_for_homepage(start_url)
        all_pages = list(tree.all_pages())
        if all_pages:
            logger.info(f"Found {len(all_pages)} pages in sitemap for {start_url}")
            include, exclude = url_filter.load_rules(portal)
            for page in all_pages:
                url = page.url
                if url_filter.filter_url(url, include, exclude):
                    r = requester.fetch_page(page)
                    if r:
                        db.save_html(url, portal, r)

    except Exception as e:
        logger.error(f"Sitemap Automatic Crawl Error ({start_url}): {e}")
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
    include, exclude = url_filter.load_rules(portal)

    logger.info(f"Starting manual crawl for '{portal}'.")
    while to_visit:
        current_url = next(iter(to_visit))

        if current_url in visited_urls:
            del to_visit[current_url]
            continue
        try:
            r = requester.fetch_page(current_url)
            visited_urls.add(current_url)

            if not r:
                del to_visit[current_url]
                continue

            if url_filter.filter_url(current_url, include, exclude):
                db.save_html(current_url, portal, r)
            found_links = link_parser.extract_sublinks(r, current_url, domain)

            for link in found_links:
                if link not in visited_urls:
                    to_visit[link] = None
                    
            del to_visit[current_url]
        except Exception as e:
            logger.error(f"Sitemap Manual Crawl Error: {e}")
            if current_url in to_visit:
                del to_visit[current_url]
            continue

def load_bulk(portal_data, db):
    """Loads bulk data from a dictionary and saves it in db.

    :param portal_data: dictionary containing multiple datasets of portals (html, portal url, portal name, url )
    :param db: The database manager instance for saving HTML content.
    """
    for portal in portal_data:
        portal_name = portal.get("portal_name", "unknown_portal")
        logger.info(f"Starting bulk load for '{portal_name}'")
        for page in portal["factchecks"]:
            try:
                r = requester.fetch_page(page)
                if r:
                    db.save_html(page, portal_name, portal["portal_url"], r)
            except Exception as e:
                logger.error(f"Error during bulk load for {page}: {e}")

def fetch_page(url):
    """
    Fetches the web page content for the specified URL by delegating to the requester.

    :param url: The web address of the page to fetch.
    :return: The raw HTML content of the page as a string if successful;
        None if an HTTP error or connection issue occurs.
    """
    return requester.fetch_page(url)