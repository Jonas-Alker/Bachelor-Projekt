from bs4 import BeautifulSoup

def preprocess_factcheck(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')

    # Remove global layout tags
    for tag in soup(['nav', 'header', 'footer', 'aside', 'script', 'style']):
        tag.decompose()

    # Remove specific layout containers
    for tag in soup.find_all(['div', 'section', 'ul'], class_=['o-header__inner', 'o-header', 'o-disruptor', 'm-billboard', 'o-stagebox', 'o-listicle', 'm-supporter', 't-footer', 'm-sharing', 'lang-sub-nav']):
        tag.decompose()

    # Remove ads and ad-related containers
    for tag in soup.find_all(['div'], id=['TopLeaderboard', 'TopMedRect', 'MiddleRectangle', 'BottomLeaderboard', 'SmartNewsFeed']):
        tag.decompose()

    # Remove cookie banners and donation prompts
    for tag in soup.find_all(['div'], class_=['m-disruptor-content', 'm-disruptor-form']):
        tag.decompose()

    # Remove related articles, read more, latest news, trending sections
    for tag in soup.find_all(['div', 'section'], class_=['m-carousel', 'o-stagebox__content', 'o-listicle__more']):
        tag.decompose()

    # Remove social media sharing widgets
    for tag in soup.find_all(['div'], class_=['m-sharing']):
        tag.decompose()

    # Remove newsletter signup forms
    for tag in soup.find_all(['div'], class_=['m-subscribe', 'm-subscriber']):
        tag.decompose()

    # Remove footer widgets and social media sections
    for tag in soup.find_all(['div'], class_=['o-socializer', 'm-widget']):
        tag.decompose()

    # Remove other recommendation widgets
    for tag in soup.find_all(['div'], class_=['m-callout', 'm-flyer']):
        tag.decompose()

    return str(soup)