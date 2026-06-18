from bs4 import BeautifulSoup

def preprocess_factcheck(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')

    # Remove donation prompts
    for element in soup.find_all(['div', 'section', 'aside'], class_=['become_member_wrapper', 'account_info', 'account_info_text', 'paid_member_perks', 'login_options_section']):
        element.decompose()

    # Remove cookie banners
    for element in soup.find_all(['div'], id=['newsletter-login-banner', 'promo-1440-banner', 'outer-promo-banner']):
        element.decompose()

    # Remove donation buttons
    for element in soup.find_all(['a'], class_=['member_link']):
        element.decompose()

    # Remove sidebars
    for element in soup.find_all(['div'], class_=['right-column', 'sticky-cont', 'sidebar_ad']):
        element.decompose()

    # Remove ads
    for element in soup.find_all(['div'], class_=['banner_ad_between_sections', 'outer-ad-unit-wrapper', 'snopesad', 'snopes_dt_incontent', 'snopes_m_incontent', 'snopes_dt_incontent_sponsorship', 'snopes_m_incontent_sponsorship']):
        element.decompose()

    # Remove related articles
    for element in soup.find_all(['div'], id=['read_more', 'read_more_articles_wrapper', 'tag_section']):
        element.decompose()

    # Remove latest news
    for element in soup.find_all(['div'], class_=['most_searched_wrapper']):
        element.decompose()

    # Remove trending
    for element in soup.find_all(['div'], class_=['trending_wrapper']):
        element.decompose()

    # Remove social media widgets
    for element in soup.find_all(['div'], class_=['social_total', 'social_comments_app_wrapper']):
        element.decompose()

    # Remove navigation elements
    for element in soup.find_all(['nav', 'footer', 'header']):
        element.decompose()

    # Remove scripts and styles
    for element in soup.find_all(['script', 'style']):
        element.decompose()

    return str(soup)