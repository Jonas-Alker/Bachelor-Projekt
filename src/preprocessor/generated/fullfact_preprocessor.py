from bs4 import BeautifulSoup

def preprocess_faktencheck(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')

    # Remove all script tags
    for script in soup(["script", "style", "noscript"]):
        script.decompose()

    # Remove header and footer
    header = soup.find('header')
    if header:
        header.decompose()

    footer = soup.find('footer')
    if footer:
        footer.decompose()

    # Remove navigation elements
    nav_elements = soup.find_all(['nav', 'ul', 'ol'])
    for nav in nav_elements:
        nav.decompose()

    # Remove social media sections
    social_sections = soup.find_all('section', class_='social-media')
    for section in social_sections:
        section.decompose()

    # Remove related articles section
    related_section = soup.find('section', class_='related-factchecks')
    if related_section:
        related_section.decompose()

    # Remove newsletter signup sections
    newsletter_sections = soup.find_all('section', class_='jumbotron')
    for section in newsletter_sections:
        section.decompose()

    # Remove donation sections
    donation_sections = soup.find_all('section', class_='donate')
    for section in donation_sections:
        section.decompose()

    # Remove breadcrumbs
    breadcrumbs = soup.find('nav', class_='breadcrumbs')
    if breadcrumbs:
        breadcrumbs.decompose()

    # Keep only the main article content
    article = soup.find('article')
    if article:
        # Create a new soup with just the article
        new_soup = BeautifulSoup(features='html.parser')
        new_soup.append(article)
        return str(new_soup)
    else:
        return str(soup)

import requests
if __name__ == "__main__":
    test_url = "https://fullfact.org/crime/southport-killer-rudakubana-prison-attack-claim-false/"

    response = requests.get(test_url)
    r = response.text
    response.raise_for_status()

    html = (preprocess_faktencheck(r))
    print(html)
