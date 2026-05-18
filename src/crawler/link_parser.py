from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup

def extract_sublinks(html, base_url, domain):
    soup = BeautifulSoup(html, "html.parser")
    found_links = set()

    for link in soup.find_all("a", href = True):
        full_url = urljoin(base_url, link["href"]).split('#')[0].rstrip('/')

        if urlparse(full_url).netloc == domain:
            if not any(ext in full_url for ext in [".jpg", ".pdf", ".png"]):
                found_links.add(full_url)
    return found_links