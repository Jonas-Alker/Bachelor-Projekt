from bs4 import BeautifulSoup

def preprocess_factcheck(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')

    # Remove all script tags
    for script in soup.find_all('script'):
        script.decompose()

    # Remove all style tags
    for style in soup.find_all('style'):
        style.decompose()

    # Remove all noscript tags
    for noscript in soup.find_all('noscript'):
        noscript.decompose()

    # Remove header
    header = soup.find('header', class_='o-header')
    if header:
        header.decompose()

    # Remove lang sub nav
    lang_sub_nav = soup.find('div', class_='lang-sub-nav')
    if lang_sub_nav:
        lang_sub_nav.decompose()

    # Remove disruptor section (donation popup)
    disruptor = soup.find('section', class_='o-disruptor')
    if disruptor:
        disruptor.decompose()

    # Remove billboard ad section
    billboard = soup.find('section', class_='m-billboard')
    if billboard:
        billboard.decompose()

    # Remove stagebox section (related articles)
    stagebox = soup.find('section', class_='o-stagebox')
    if stagebox:
        stagebox.decompose()

    # Remove listicle section (related articles)
    listicle = soup.find('section', class_='o-listicle')
    if listicle:
        listicle.decompose()

    # Remove supporter section (donation call)
    supporter = soup.find('section', class_='m-supporter')
    if supporter:
        supporter.decompose()

    # Remove footer
    footer = soup.find('footer', class_='t-footer')
    if footer:
        footer.decompose()

    # Remove sharing section
    sharing = soup.find('div', class_='m-sharing')
    if sharing:
        sharing.decompose()

    # Remove SVG definitions
    svg_defs = soup.find('div', class_='js-svg')
    if svg_defs:
        svg_defs.decompose()

    # Remove cookie consent and GDPR related elements
    gdpr_scripts = soup.find_all('script', src=lambda x: x and 'consensu.org' in x)
    for script in gdpr_scripts:
        script.decompose()

    # Remove ad slots
    ad_slots = soup.find_all(['div'], id=lambda x: x and ('TopLeaderboard' in x or 'TopMedRect' in x or 'BottomLeaderboard' in x or 'MiddleRectangle' in x))
    for ad in ad_slots:
        ad.decompose()

    # Remove flyer ads
    flyers = soup.find_all('div', class_=lambda x: x and 'c-flyer' in x)
    for flyer in flyers:
        flyer.decompose()

    # Remove callout sections
    callouts = soup.find_all('div', class_=lambda x: x and 'm-callout' in x)
    for callout in callouts:
        callout.decompose()

    # Remove author section (keep only if it's the main article author)
    author_sections = soup.find_all('div', class_='m-author')
    for author in author_sections:
        author.decompose()

    # Remove carousel section (related articles)
    carousel = soup.find('div', class_='m-carousel')
    if carousel:
        carousel.decompose()

    # Remove superbox section (sources)
    superbox = soup.find('section', id='sources')
    if superbox:
        superbox.decompose()

    # Remove t-row sections that are not part of the main content
    t_rows = soup.find_all('section', class_='t-row')
    for row in t_rows:
        # Keep only the center column if it contains the main article
        center_div = row.find('div', class_='t-row__center')
        if center_div:
            left_div = row.find('div', class_='t-row__left')
            right_div = row.find('div', class_='t-row__right')
            if left_div:
                left_div.decompose()
            if right_div:
                right_div.decompose()
        else:
            row.decompose()

    # Remove o-stage section (claim section)
    o_stage = soup.find('section', class_='o-stage')
    if o_stage:
        o_stage.decompose()

    # Remove t-menu (mobile menu)
    t_menu = soup.find('div', class_='t-menu')
    if t_menu:
        t_menu.decompose()

    # Remove m-widget sections in footer area
    widgets = soup.find_all('div', class_='m-widget')
    for widget in widgets:
        widget.decompose()

    # Return the cleaned HTML as a string
    return str(soup)