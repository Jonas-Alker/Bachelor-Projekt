from bs4 import BeautifulSoup

def preprocess_factcheck(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')

    # Remove navigation menus
    nav = soup.find('nav', id='new_navbar_wrapper')
    if nav:
        nav.decompose()

    # Remove footer
    footer = soup.find('footer', class_='container')
    if footer:
        footer.decompose()

    # Remove sidebars and ads
    sidebar = soup.find('div', class_='right-column')
    if sidebar:
        sidebar.decompose()

    # Remove sticky ads
    sticky_ad = soup.find('div', class_='sticky-cont')
    if sticky_ad:
        sticky_ad.decompose()

    # Remove "Recommendations" section
    recommendations = soup.find('div', id='read_more')
    if recommendations:
        recommendations.decompose()

    # Remove "Article Tags" section
    tags_section = soup.find('div', id='tag_section')
    if tags_section:
        tags_section.decompose()

    # Remove social media sharing buttons
    social_buttons = soup.find('div', class_='social_comments_app_wrapper')
    if social_buttons:
        social_buttons.decompose()

    # Remove "Sources" section
    sources = soup.find('div', class_='sources_wrapper')
    if sources:
        sources.decompose()

    # Remove "Updates" section
    updates = soup.find('div', class_='updates_wrapper')
    if updates:
        updates.decompose()

    # Remove "Article Tags" section
    article_tags = soup.find('div', id='tag_section')
    if article_tags:
        article_tags.decompose()

    # Remove "Related Articles" section
    related_articles = soup.find('div', class_='outer-ad-unit-wrapper')
    if related_articles:
        related_articles.decompose()

    # Remove cookie banners
    cookie_banner = soup.find('div', class_='newsletter-login-banner')
    if cookie_banner:
        cookie_banner.decompose()

    # Remove promotional banners
    promo_banners = soup.find_all(['div', 'aside'], class_=lambda x: x and ('promo-' in x or 'sponsor-1440' in x))
    for banner in promo_banners:
        banner.decompose()

    # Remove script tags
    scripts = soup.find_all('script')
    for script in scripts:
        script.decompose()

    # Remove style tags
    styles = soup.find_all('style')
    for style in styles:
        style.decompose()

    # Return the cleaned HTML as a string
    return str(soup)