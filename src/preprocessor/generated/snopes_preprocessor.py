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

    # Remove right column (sidebar)
    right_column = soup.find('div', class_='right-column')
    if right_column:
        right_column.decompose()

    # Remove sticky ad container
    sticky_ad = soup.find('div', class_='sticky-cont')
    if sticky_ad:
        sticky_ad.decompose()

    # Remove promotional banners
    promo_banners = soup.find_all(['div', 'aside'], class_=lambda x: x and ('promo-' in x or 'sponsor-1440' in x))
    for banner in promo_banners:
        banner.decompose()

    # Remove newsletter login banner
    newsletter_banner = soup.find('div', id='newsletter-login-banner')
    if newsletter_banner:
        newsletter_banner.decompose()

    # Remove outer promo banner
    outer_promo = soup.find('div', class_='outer-promo-banner')
    if outer_promo:
        outer_promo.decompose()

    # Remove app promo banner
    app_promo = soup.find('div', class_='newsletter-login-banner')
    if app_promo:
        app_promo.decompose()

    # Remove presidential debate banner
    debate_banner = soup.find('div', class_='presidential_debate_banner')
    if debate_banner:
        debate_banner.decompose()

    # Remove factbot promo
    factbot_promo = soup.find('div', id='factbot_promo_wrap')
    if factbot_promo:
        factbot_promo.decompose()

    # Remove search user wrapper
    search_user = soup.find('div', class_='search_user_wrapper')
    if search_user:
        search_user.decompose()

    # Remove become member wrapper
    become_member = soup.find('div', class_='become_member_wrapper')
    if become_member:
        become_member.decompose()

    # Remove social comments app wrapper
    social_comments = soup.find('div', class_='social_comments_app_wrapper')
    if social_comments:
        social_comments.decompose()

    # Remove article tags section
    article_tags = soup.find('div', id='tag_section')
    if article_tags:
        article_tags.decompose()

    # Remove read more recommendations
    read_more = soup.find('div', id='read_more')
    if read_more:
        read_more.decompose()

    # Remove updates section
    updates = soup.find('div', class_='updates_wrapper')
    if updates:
        updates.decompose()

    # Remove sources section
    sources = soup.find('div', class_='sources_wrapper')
    if sources:
        sources.decompose()

    # Remove admin banner if present
    admin_banner = soup.find('div', class_='railrode-admin-banner')
    if admin_banner:
        admin_banner.decompose()

    # Remove soft paywall container if present
    soft_paywall = soup.find('div', class_='soft-paywall-container')
    if soft_paywall:
        soft_paywall.decompose()

    # Remove hard paywall container if present
    hard_paywall = soup.find('div', class_='hard-paywall-container')
    if hard_paywall:
        hard_paywall.decompose()

    # Remove subscription container if present
    subscribe_container = soup.find('div', class_='subscribe-container')
    if subscribe_container:
        subscribe_container.decompose()

    # Remove hidden content
    hidden_content = soup.find_all(class_='hidden-content')
    for content in hidden_content:
        content.decompose()

    # Remove hidden to subscribe
    hidden_to_subscribe = soup.find_all(class_='hidden-to-subscribe')
    for content in hidden_to_subscribe:
        content.decompose()

    # Remove outer ad unit wrappers
    ad_wrappers = soup.find_all('div', class_='outer-ad-unit-wrapper')
    for wrapper in ad_wrappers:
        wrapper.decompose()

    # Remove banner ad sections
    banner_ads = soup.find_all('div', class_='banner_ad_between_sections')
    for banner in banner_ads:
        banner.decompose()

    # Remove article rail wrapper
    article_rail = soup.find('div', class_='article_rail_wrapper')
    if article_rail:
        article_rail.decompose()

    # Return the cleaned HTML as a string
    return str(soup)