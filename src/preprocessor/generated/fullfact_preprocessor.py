from bs4 import BeautifulSoup

def preprocess_factcheck(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')

    # Remove global layout tags
    for tag in soup(['nav', 'footer', 'aside', 'script', 'style']):
        tag.decompose()

    # Remove donation prompts and CTAs
    for element in soup.find_all(['section', 'div'], class_=['inline-donate', 'jumbotron', 'donate', 'ga-inline-donate']):
        element.decompose()

    # Remove related articles sections
    for element in soup.find_all(['section', 'div'], class_=['related-factchecks', 'related-articles']):
        element.decompose()

    # Remove sidebars and menus
    for element in soup.find_all(['div', 'ul'], class_=['navbar-nav', 'navbar-collapse', 'dropdown-menu', 'footer-links']):
        element.decompose()

    # Remove cookie banners and newsletter signups
    for element in soup.find_all(['section', 'div'], class_=['signup', 'newsletter-signup-form', 'ga-newsletter-signup']):
        element.decompose()

    # Remove ads and promotional content
    for element in soup.find_all(['div', 'section'], class_=['ad', 'advertisement', 'promo', 'ga-navbar-donate']):
        element.decompose()

    # Remove trending/latest news sections
    for element in soup.find_all(['section', 'div'], class_=['trending', 'latest-news', 'topics']):
        element.decompose()

    # Remove read more links and similar
    for element in soup.find_all(['a', 'div'], class_=['read-more', 'load-more', 'show-more']):
        element.decompose()

    return str(soup)