from bs4 import BeautifulSoup
import re
from datetime import datetime

def parse_factcheck(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    results = []

    # Extract language
    language = 'en'
    lang_element = soup.find('html', {'lang': True})
    if lang_element and 'lang' in lang_element.attrs:
        language = lang_element['lang'].split('-')[0]

    # Extract main fact-check article
    article = soup.find('article', class_=re.compile(r'm-statement--is-\w+'))
    if not article:
        return results

    # Extract claim and author_claim
    claim_element = article.find('div', class_='m-statement__quote')
    claim = claim_element.get_text(strip=True) if claim_element else None

    # Extract author_claim
    author_claim_element = article.find('a', class_='m-statement__name')
    author_claim = author_claim_element.get_text(strip=True) if author_claim_element else None

    # Extract stated_at
    stated_at_element = article.find('div', class_='m-statement__desc')
    stated_at = None
    if stated_at_element:
        stated_at_text = stated_at_element.get_text(strip=True)
        date_match = re.search(r'stated on (\w+ \d{1,2}, \d{4})', stated_at_text)
        if date_match:
            try:
                stated_at = datetime.strptime(date_match.group(1), '%B %d, %Y').strftime('%d.%m.%Y')
            except:
                pass

    # Extract original_rating
    rating_element = article.find('img', alt=True)
    original_rating = rating_element['alt'] if rating_element and 'alt' in rating_element.attrs else None

    # Extract author_factcheck
    author_factcheck_element = soup.find('a', href=re.compile(r'/staff/'))
    author_factcheck = author_factcheck_element.get_text(strip=True) if author_factcheck_element else None

    # Extract published_at
    published_at_element = soup.find('span', class_='m-author__date')
    published_at = None
    if published_at_element:
        date_text = published_at_element.get_text(strip=True)
        try:
            published_at = datetime.strptime(date_text, '%B %d, %Y').strftime('%d.%m.%Y')
        except:
            pass

    # Extract headline
    headline_element = soup.find('h1', class_=re.compile(r'c-title--\w+'))
    headline = headline_element.get_text(strip=True) if headline_element else None

    # Extract body
    body_element = soup.find('article', class_='m-textblock')
    body = None
    if body_element:
        for unwanted in body_element.find_all(['div', 'section'], class_=re.compile(r'm-(callout|author|superbox)')):
            unwanted.decompose()
        body = body_element.get_text(strip=True)

    # Create result dictionary
    if claim or headline:
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