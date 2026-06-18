from bs4 import BeautifulSoup

def preprocess_factcheck(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')

    # Remove global layout tags
    for tag in soup(['nav', 'header', 'footer', 'aside', 'script', 'style', 'noscript']):
        tag.decompose()

    # Remove specific layout containers by class/id
    layout_containers = soup.find_all(['div', 'section', 'ul', 'li', 'article'], class_=[
        'global-wrapper', 'o-header', 'o-header__inner', 'o-header__branding', 'o-header__menu',
        'o-header__donate', 'o-header__search', 't-menu', 'm-togglist', 'm-togglist__list',
        'm-togglist__panel', 'm-togglist__checkbox', 'm-togglist__label', 'o-socializer',
        'o-socializer__item', 'o-socializer__social', 'o-socializer__subscribe', 'm-follow',
        'm-subscribe', 'm-search', 'm-search__checkbox', 'm-search__toggle', 'm-search__content',
        'm-search__form', 'm-search__input', 'm-search__submit', 'lang-sub-nav', 'o-disruptor',
        'o-disruptor__close', 'o-disruptor__wrapper', 'o-disruptor__content', 'o-disruptor__form',
        'm-disruptor-content', 'm-disruptor-form', 'm-disruptor-form__items', 'm-disruptor-form__item',
        'm-disruptor-form__title', 'm-billboard', 'o-stagebox', 'o-stagebox__wrapper', 'o-stagebox__inner',
        'o-stagebox__header', 'o-stagebox__title', 'o-stagebox__content', 'o-stagebox__subtitle',
        'o-listicle', 'o-listicle__inner', 'o-listicle__header', 'o-listicle__title', 'o-listicle__content',
        'o-listicle__list', 'o-listicle__item', 'o-listicle__more', 'm-carousel', 'm-carousel__item',
        'm-statement', 'm-statement__author', 'm-statement__avatar', 'm-statement__meta', 'm-statement__content',
        'm-statement__body', 'm-statement__quote-wrap', 'm-statement__quote', 'm-statement__meter',
        'm-statement__footer', 'm-statement__subline', 'm-statement__image', 'm-statement__desc',
        'm-statement__name', 'm-statement__image', 'm-statement__quote-wrap', 'm-statement__quote',
        'm-statement__meter', 'm-statement__footer', 'm-statement__subline', 'm-statement--boxed',
        'm-statement--is-medium', 'm-statement--is-large', 'm-statement--is-xlarge', 'm-statement--true',
        'm-statement--mostly-true', 'm-statement--half-true', 'm-statement--mostly-false', 'm-statement--false',
        'm-statement--pants-fire', 'm-callout', 'm-callout--large', 'm-callout__title', 'm-callout__body',
        'm-callout__link', 'm-callout__icon', 'm-textblock', 'm-superbox', 'm-superbox__header',
        'm-superbox__title', 'm-superbox__content', 'm-author', 'm-author__img', 'm-author__content',
        'm-flyer', 'm-flyer--in-sidebar', 'c-flyer', 'c-flyer--in-sidebar', 'c-button',
        'c-button--small', 'c-button--large', 'c-button--hollow', 'c-button--light', 'c-input', 'c-input--light',
        'c-input__inner', 'c-input__field', 'c-select', 'c-select--light', 'c-select__inner', 't-row',
        't-row__left', 't-row__center', 't-row__right', 'm-widget', 'm-widget__title', 'm-widget__content',
        'm-sharing', 'm-sharing__checkbox', 'm-sharing__toggle', 'm-sharing__list', 'm-sharing__item',
        'm-meta', 'm-meta__inner', 'm-meta__item', 'm-branding', 'm-branding__logo', 'm-branding__subline',
        'm-branding__claim', 'm-togglist', 'm-togglist__list', 'm-togglist__panel', 'm-togglist__checkbox',
        'm-togglist__label', 'm-menu-list', 'm-menu-list__inner', 'm-menu-list__item', 'm-list',
        'm-list--horizontal', 'm-list__item', 'm-article', 'm-article__inner', 'm-article__header',
        'm-article__title', 'm-article__content', 'm-article__footer', 'm-article__meta', 'm-article__image',
        'm-article__quote', 'm-article__quote-wrap', 'm-article__quote-source', 'm-article__quote-author',
        'm-article__quote-date', 'm-article__rating', 'm-article__rating-meter', 'm-article__rating-text',
        'm-article__rating-description', 'm-article__sources', 'm-article__sources-title', 'm-article__sources-list',
        'm-article__sources-item', 'm-article__tags', 'm-article__tags-title', 'm-article__tags-list',
        'm-article__tags-item', 'm-article__share', 'm-article__share-title', 'm-article__share-list',
        'm-article__share-item', 'm-article__disclaimer', 'm-article__disclaimer-text', 'm-supporter',
        'm-supporter__inner', 'm-supporter__content', 'm-supporter__header', 'm-supporter__title',
        'm-supporter__body', 'm-supporter__branding', 'rounded-select-label', 'c-image', 'c-image__thumb',
        'c-image__original', 'c-image__caption', 'c-image__caption-inner', 't-footer', 't-footer__wrapper',
        'o-footer-list', 'o-footer-list__item', 'o-footer-list__inner', 'o-menu-list', 'o-menu-list__inner',
        'o-menu-list__item', 'm-follow--inverted', 'm-subscribe--inverted', 'm-notfound', 'm-notfound__title',
        'm-notfound__content', 'm-notfound__image', 'm-notfound__body', 'short-on-time'
    ])
    for container in layout_containers:
        container.decompose()

    # Remove ads and ad-related containers
    ad_containers = soup.find_all(['div'], id=[
        'TopLeaderboard', 'TopMedRect', 'MiddleRectangle', 'BottomLeaderboard', 'BottomLeaderboard_Adhesion',
        'SmartNewsFeed'
    ])
    for ad in ad_containers:
        ad.decompose()

    # Remove cookie banners and consent dialogs
    cookie_containers = soup.find_all(['div'], class_=[
        'js-svg', 'c-icon-defs'
    ])
    for cookie in cookie_containers:
        cookie.decompose()

    # Remove sharing widgets
    sharing_widgets = soup.find_all(['div'], class_=['m-sharing'])
    for widget in sharing_widgets:
        widget.decompose()

    # Remove donation prompts
    donation_containers = soup.find_all(['section'], class_=['m-supporter'])
    for donation in donation_containers:
        donation.decompose()

    # Remove related articles and recommendation widgets
    related_containers = soup.find_all(['div', 'section'], class_=[
        'm-carousel', 'o-stagebox', 'o-stagebox__wrapper', 'o-stagebox__inner'
    ])
    for related in related_containers:
        related.decompose()

    # Remove empty or near-empty elements that might remain
    for element in soup.find_all():
        if not element.contents or (len(element.contents) == 1 and not str(element.contents[0]).strip()):
            element.decompose()

    return str(soup)