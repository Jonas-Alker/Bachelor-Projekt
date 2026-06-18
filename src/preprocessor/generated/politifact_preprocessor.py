from bs4 import BeautifulSoup

def preprocess_factcheck(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')

    # Remove donation prompts
    donation_containers = soup.find_all(['div', 'section'], class_=['m-disruptor-content', 'm-disruptor-form', 'm-supporter'])
    for container in donation_containers:
        container.decompose()

    # Remove ads
    ad_containers = soup.find_all(['div'], id=['TopLeaderboard', 'TopMedRect', 'MiddleRectangle', 'BottomLeaderboard'])
    for container in ad_containers:
        container.decompose()

    # Remove cookie banner and related elements
    cookie_banner = soup.find('div', class_='js-svg c-icon-defs')
    if cookie_banner:
        cookie_banner.decompose()

    # Remove sharing widgets
    sharing_widget = soup.find('div', class_='m-sharing')
    if sharing_widget:
        sharing_widget.decompose()

    # Remove footer
    footer = soup.find('footer', class_='t-footer')
    if footer:
        footer.decompose()

    # Remove global scripts and styles
    for tag in soup(['script', 'style']):
        tag.decompose()

    # Remove navigation elements
    nav_elements = soup.find_all(['nav', 'header', 'aside'])
    for element in nav_elements:
        element.decompose()

    # Remove social media and newsletter sections
    social_newsletter = soup.find_all(['div'], class_=['o-socializer', 'm-subscribe'])
    for element in social_newsletter:
        element.decompose()

    # Remove related articles and latest news sections
    related_sections = soup.find_all(['section'], class_=['o-stagebox', 'o-listicle'])
    for section in related_sections:
        section.decompose()

    # Remove trending and other sidebar content
    sidebar_content = soup.find_all(['div'], class_=['m-callout', 'm-carousel', 'm-widget'])
    for content in sidebar_content:
        content.decompose()

    return str(soup)