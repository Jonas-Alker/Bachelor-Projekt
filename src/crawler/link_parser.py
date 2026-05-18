from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup

def extract_sublinks(html, base_url, domain):
    """Extracts all valid, internal sublinks from an HTML content string.

    :param html: The raw HTML content string to parse.
    :param base_url: The base URL used to resolve relative hyperlinks.
    :param domain: The specific domain name (e.g., "example.com") to filter internal links.
    :return:
    """
    soup = BeautifulSoup(html, "html.parser")
    found_links = set()

    for link in soup.find_all("a", href = True):
        full_url = urljoin(base_url, link["href"]).split('#')[0].rstrip('/')

        if urlparse(full_url).netloc == domain:
            if not any(ext in full_url for ext in [".jpg", ".pdf", ".png"]):
                found_links.add(full_url)
    return found_links