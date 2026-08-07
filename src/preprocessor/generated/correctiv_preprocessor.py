from bs4 import BeautifulSoup

def preprocess_factcheck(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')

    # Remove global layout tags
    for tag in soup(['nav', 'footer', 'aside', 'script', 'style']):
        tag.decompose()

    # Remove donation prompts and ads
    for element in soup.find_all(['div', 'section', 'article'], class_=[
        'wp-block-group', 'wp-block-heading', 'popup__section-recherche',
        'popup__ad-container-faktencheck', 'corre-popup-schweiz',
        'corre-target', 'ad-container', 'wp-elements-dc7c9a687ecbcdd885567145f7b8a6e9',
        'wp-elements-263b56ed3f77d8c8f88210b5befcc352',
        'wp-elements-6cf9f66b5be7ba45f9e9ad942184ddc6',
        'wp-container-core-group-is-layout-2cecd1a6'
    ]):
        element.decompose()

    # Remove cookie banners and consent manager
    for element in soup.find_all(['div', 'section'], class_=[
        'consentmanager', 'cmplazyload', 'cmplazyload-placeholder'
    ]):
        element.decompose()

    # Remove related articles sections
    for element in soup.find_all(['div', 'section'], class_=[
        'related__container', 'list list--related', 'detail__list',
        'related__item', 'list__item', 'list__box'
    ]):
        element.decompose()

    # Remove read more sections
    for element in soup.find_all(['div', 'section'], class_=[
        'list__bar', 'more', 'more__text', 'list__more'
    ]):
        element.decompose()

    # Remove latest news and trending sections
    for element in soup.find_all(['div', 'section'], class_=[
        'list__header', 'topline', 'topline__link'
    ]):
        element.decompose()

    # Remove sidebars and menus
    for element in soup.find_all(['div', 'section'], class_=[
        'header__navigation', 'navigation', 'navigation__list',
        'navigation__item', 'navigation__link', 'header__progress',
        'hamburger', 'header__navigation--mobile', 'header__navigation--desktop'
    ]):
        element.decompose()

    # Remove empty containers that might be leftovers
    for element in soup.find_all(['div', 'section', 'ul', 'li']):
        if not element.contents and not element.find():
            element.decompose()

    return str(soup)