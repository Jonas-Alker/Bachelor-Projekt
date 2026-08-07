from bs4 import BeautifulSoup
from datetime import datetime
import re

def parse_factcheck(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    results = []

    # Extract language from HTML lang attribute
    language = soup.find('html').get('lang', None)
    if language:
        language = language.split('-')[0]

    # Extract main headline from h1 tag
    headline = None
    h1_tag = soup.find('h1', class_='secondary-title')
    if h1_tag:
        headline = h1_tag.get_text(strip=True)

    # Extract published date from time tag
    published_at = None
    time_tag = soup.find('time', class_='detail__date')
    if time_tag and 'datetime' in time_tag.attrs:
        try:
            date_str = time_tag['datetime']
            dt = datetime.strptime(date_str, '%Y-%m-%dT%H:%M:%S%z')
            published_at = dt.strftime('%d.%m.%Y')
        except (ValueError, TypeError):
            pass

    # Extract author_factcheck from author link
    author_factcheck = None
    author_link = soup.find('a', class_='detail__authors-link')
    if author_link:
        author_factcheck = author_link.get_text(strip=True)

    # Extract body text from main content area
    body = None
    content_div = soup.find('div', class_='detail__content')
    if content_div:
        body = ' '.join([p.get_text(strip=True) for p in content_div.find_all('p')])

    # Extract claim from detail__box-content
    claim = None
    claim_box = soup.find('div', class_='detail__box-content')
    if claim_box:
        claim = claim_box.get_text(strip=True)

    # Extract author_claim from detail__box-footer
    author_claim = None
    claim_footer = soup.find('div', class_='detail__box-footer')
    if claim_footer:
        author_claim = claim_footer.find('div').get_text(strip=True) if claim_footer.find('div') else None

    # Extract stated_at from claim footer
    stated_at = None
    if claim_footer:
        date_div = claim_footer.find_all('div')
        if len(date_div) > 1:
            date_text = date_div[1].get_text(strip=True)
            if 'Datum:' in date_text:
                date_str = date_text.replace('Datum:', '').strip()
                try:
                    dt = datetime.strptime(date_str, '%d.%m.%Y')
                    stated_at = dt.strftime('%d.%m.%Y')
                except (ValueError, TypeError):
                    pass

    # Extract original_rating from detail__rating
    original_rating = None
    rating_div = soup.find('div', class_='detail__rating')
    if rating_div:
        rating_text = rating_div.get_text(strip=True)
        if rating_text:
            original_rating = rating_text

    # Create result dictionary
    if headline or body or claim:
        result = {
            'headline': headline,
            'body': body,
            'claim': claim,
            'author_factcheck': author_factcheck,
            'published_at': published_at,
            'language': language,
            'author_claim': author_claim,
            'stated_at': stated_at,
            'original_rating': original_rating
        }
        results.append(result)

    return results