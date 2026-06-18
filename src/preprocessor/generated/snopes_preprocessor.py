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
    right_column = soup.find('div', class_='right-column')
    if right_column:
        right_column.decompose()

    # Remove cookie banners
    newsletter_banner = soup.find('div', id='newsletter-login-banner')
    if newsletter_banner:
        newsletter_banner.decompose()

    promo_banner = soup.find('div', class_='newsletter-login-banner')
    if promo_banner:
        promo_banner.decompose()

    promo_1440_banner = soup.find('div', id='promo-1440-banner')
    if promo_1440_banner:
        promo_1440_banner.decompose()

    footer_promo_banner = soup.find('div', id='footer-outer-promo-banner')
    if footer_promo_banner:
        footer_promo_banner.decompose()

    # Remove "Related Articles" sections
    read_more = soup.find('div', id='read_more')
    if read_more:
        read_more.decompose()

    # Remove "Read More" sections
    read_more_articles = soup.find('div', id='read_more_articles_wrapper')
    if read_more_articles:
        read_more_articles.decompose()

    # Remove "Latest News" sections
    latest_news = soup.find('div', class_='latest_news_wrapper')
    if latest_news:
        latest_news.decompose()

    # Remove "Trending" sections
    trending = soup.find('div', class_='trending_wrapper')
    if trending:
        trending.decompose()

    # Remove "Other Fact Checks" sections
    other_fact_checks = soup.find('div', class_='other_fact_checks_wrapper')
    if other_fact_checks:
        other_fact_checks.decompose()

    # Remove recommendation widgets
    recommendations = soup.find('div', class_='recommendations_wrapper')
    if recommendations:
        recommendations.decompose()

    # Remove navigation filler
    nav_filler = soup.find('div', id='nav_filler')
    if nav_filler:
        nav_filler.decompose()

    # Remove sticky ads
    sticky_ad = soup.find('div', class_='sticky-cont')
    if sticky_ad:
        sticky_ad.decompose()

    # Remove script tags
    for script in soup.find_all('script'):
        script.decompose()

    # Remove style tags
    for style in soup.find_all('style'):
        style.decompose()

    # Remove input tags
    for input_tag in soup.find_all('input'):
        input_tag.decompose()

    # Remove meta tags
    for meta in soup.find_all('meta'):
        meta.decompose()

    # Remove link tags
    for link in soup.find_all('link'):
        link.decompose()

    # Remove hr tags
    for hr in soup.find_all('hr'):
        hr.decompose()

    # Remove br tags
    for br in soup.find_all('br'):
        br.decompose()

    return str(soup)