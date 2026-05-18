import src.crawler.requester as requester
import src.crawler.link_parser as link_parser
from urllib.parse import urlparse
from usp.tree import sitemap_tree_for_homepage

def search_sitemap_by_url(portal_name, portal_url, db):
    """
    :param portal_name:
    :param portal_url:
    :return:
    """
    #Use usp to get sitemap automatically
    confirm = find_sitemap_automatically(portal_url, portal_name, db)

    #Fallback if usp does not work
    if not confirm:
        crawl_sitemap_manually(portal_url, portal_name, db)

def find_sitemap_automatically(start_url, portal, db):
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