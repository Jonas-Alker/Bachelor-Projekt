from bs4 import BeautifulSoup

def preprocess_factcheck(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')

    # Remove donation prompts
    donation_prompts = soup.find_all(['div', 'section', 'aside'], class_=['mkg-topbar', 'mk-spende-overlay', 'mk-spende-modal', 'mkg-donate-overlay', 'mkg-donate-card', 'mkg-inline2', 'mk-cta-stack', 'mk-wa', 'mk-club-banner', 'mimikama-sources', 'mimikama-footer-2026'])
    for element in donation_prompts:
        element.decompose()

    # Remove cookie banners
    cookie_banners = soup.find_all(['div'], class_=['brlbs-cmpnt-container', 'brlbs-cmpnt-widget'])
    for element in cookie_banners:
        element.decompose()

    # Remove ads and sidebars
    ads_sidebars = soup.find_all(['div', 'section', 'aside'], class_=['mk-cta-stack', 'mk-wa', 'mk-club-banner', 'mimikama-sources', 'mimikama-footer-2026', 'mk-pillar-hint'])
    for element in ads_sidebars:
        element.decompose()

    # Remove related articles sections
    related_articles = soup.find_all(['div', 'section', 'aside'], class_=['mk-cluster-footer', 'mimikama-footer-2026'])
    for element in related_articles:
        element.decompose()

    # Remove read more links
    read_more_links = soup.find_all(['a'], class_=['mk-inline2-cta', 'mk-wa-cta', 'mk-cta', 'mk-cta-paypal', 'mk-donate-hero', 'mk-donate-once', 'mk-bridge-btn', 'mkg-inline2-cta', 'mkg-sbanner-btn', 'mkg-donate-hero-btn'])
    for element in read_more_links:
        element.decompose()

    # Remove latest news sections
    latest_news = soup.find_all(['div', 'section'], class_=['mimikama-footer__projekte', 'mimikama-footer__seo'])
    for element in latest_news:
        element.decompose()

    # Remove trending terms
    trending_terms = soup.find_all(['div', 'section'], class_=['mimikama-footer__seo', 'mimikama-footer__seo-grid'])
    for element in trending_terms:
        element.decompose()

    # Remove global layout tags (safe to remove)
    global_layout = soup.find_all(['nav', 'footer', 'aside', 'script', 'style'])
    for element in global_layout:
        element.decompose()

    return str(soup)