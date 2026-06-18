from bs4 import BeautifulSoup

def preprocess_factcheck(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')

    # Remove global layout tags
    for tag in soup(['nav', 'header', 'footer', 'aside', 'script', 'style']):
        tag.decompose()

    # Remove navigation menus and related sections
    for element in soup.find_all(['div', 'section', 'ul'], class_=['navbar', 'navbar-nav', 'dropdown-menu', 'page-header', 'breadcrumbs', 'social-media', 'topics', 'related-factchecks', 'footer-links', 'brand-legal']):
        element.decompose()

    # Remove ads, sidebars, and recommendation widgets
    for element in soup.find_all(['div', 'section'], class_=['inline-donate', 'jumbotron', 'donate', 'signup', 'ga-inline-donate', 'ga-newsletter-signup']):
        element.decompose()

    # Remove cookie banners and tracking elements
    for element in soup.find_all(['div', 'iframe'], class_=['gtm-start', 'gtm-js', 'gtm-start']):
        element.decompose()

    # Remove specific layout classes
    for element in soup.find_all(['div', 'section'], class_=['container', 'row', 'col-12', 'col-md-6', 'col-lg-8', 'py-3', 'py-md-8', 'justify-content-md-center', 'mx-n2', 'mx-sm-0']):
        element.decompose()

    return str(soup)