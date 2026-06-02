from bs4 import BeautifulSoup

def preprocess_faktencheck(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')

    # Remove all script and style elements
    for script in soup(["script", "style", "noscript"]):
        script.decompose()

    # Remove header and footer
    header = soup.find('header', class_='o-header')
    if header:
        header.decompose()

    footer = soup.find('footer', class_='t-footer')
    if footer:
        footer.decompose()

    # Remove navigation menus and sidebars
    nav = soup.find('div', class_='o-menu-list')
    if nav:
        nav.decompose()

    sidebar = soup.find('div', class_='t-row__right')
    if sidebar:
        sidebar.decompose()

    # Remove ads and promotional content
    ads = soup.find_all(['div', 'section'], class_=lambda x: x and ('ad' in x.lower() or 'adhesion' in x.lower() or 'flyer' in x.lower()))
    for ad in ads:
        ad.decompose()

    # Remove social sharing elements
    sharing = soup.find('div', class_='m-sharing')
    if sharing:
        sharing.decompose()

    # Remove newsletter signup forms
    newsletter = soup.find('section', class_='m-disruptor-content')
    if newsletter:
        newsletter.decompose()

    # Remove related articles and listicles
    listicles = soup.find_all('section', class_=lambda x: x and ('listicle' in x.lower() or 'carousel' in x.lower()))
    for listicle in listicles:
        listicle.decompose()

    # Remove author info if it's not part of the main article
    author = soup.find('div', class_='m-author')
    if author:
        author.decompose()

    # Remove callout boxes that aren't part of the main content
    callouts = soup.find_all('div', class_=lambda x: x and ('callout' in x.lower() or 'superbox' in x.lower()))
    for callout in callouts:
        callout.decompose()

    # Remove the Truth-O-Meter section at the bottom
    truth_o_meter = soup.find('section', class_='o-stagebox')
    if truth_o_meter:
        truth_o_meter.decompose()

    # Remove supporter/membership sections
    supporter = soup.find('section', class_='m-supporter')
    if supporter:
        supporter.decompose()

    # Remove the main navigation section at the bottom
    main_nav = soup.find('div', class_='o-footer-list')
    if main_nav:
        main_nav.decompose()

    # Remove the socializer section at the bottom
    socializer = soup.find('div', class_='o-socializer--inverted')
    if socializer:
        socializer.decompose()

    # Remove the meta section at the bottom
    meta = soup.find('div', class_='m-meta')
    if meta:
        meta.decompose()

    # Remove the GPT ad slots
    ad_slots = soup.find_all('div', id=lambda x: x and ('Leaderboard' in x or 'MedRect' in x or 'MiddleRectangle' in x))
    for slot in ad_slots:
        slot.decompose()

    # Remove the disruptor section (newsletter popup)
    disruptor = soup.find('section', class_='o-disruptor')
    if disruptor:
        disruptor.decompose()

    # Remove the main navigation section in the middle
    main_nav_middle = soup.find('section', class_='o-listicle')
    if main_nav_middle:
        main_nav_middle.decompose()

    # Return the cleaned HTML
    return str(soup)

#For testing purposes only during programming
import requests
if __name__ == "__main__":
    test_url = "https://www.politifact.com/factchecks/2026/may/14/kathy-castor/kid-care-florida-desantis-health-insurance/"

    response = requests.get(test_url)
    r = response.text
    response.raise_for_status()

    html = (preprocess_faktencheck(r))
    print(html)
