from bs4 import BeautifulSoup
import re
from datetime import datetime

def parse_factcheck(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Find the main article container
    main_article = soup.find('article', class_='m-textblock')
    if not main_article:
        return []

    # Initialize result list
    results = []

    # Extract language from html lang attribute
    language = soup.find('html').get('lang', None)

    # Extract headline
    headline_elem = main_article.find_previous('h1', class_='c-title')
    headline = headline_elem.get_text(strip=True) if headline_elem else None

    # Extract body text
    body = main_article.get_text(separator='\n', strip=True)

    # Extract claim from statement block
    claim_elem = main_article.find('div', class_='m-statement__quote')
    claim = claim_elem.get_text(strip=True) if claim_elem else None

    # Extract author_factcheck
    author_factcheck_elem = main_article.find_previous('div', class_='m-author')
    author_factcheck = None
    published_at = None
    if author_factcheck_elem:
        author_factcheck = author_factcheck_elem.find('a').get_text(strip=True) if author_factcheck_elem.find('a') else None
        date_text = author_factcheck_elem.find('span', class_='m-author__date').get_text(strip=True) if author_factcheck_elem.find('span', class_='m-author__date') else None
        if date_text:
            try:
                # Parse date in format like "May 14, 2026"
                date_obj = datetime.strptime(date_text, '%B %d, %Y')
                published_at = date_obj.strftime('%d.%m.%Y')
            except ValueError:
                published_at = None

    # Extract author_claim from statement block
    author_claim_elem = main_article.find('a', class_='m-statement__name')
    author_claim = author_claim_elem.get_text(strip=True) if author_claim_elem else None

    # Extract stated_at from statement block
    stated_at_elem = main_article.find('div', class_='m-statement__desc')
    stated_at = None
    if stated_at_elem:
        stated_at_text = stated_at_elem.get_text(strip=True)
        # Extract date from text like "stated on April 29, 2026 in an X post"
        date_match = re.search(r'(\w+ \d{1,2}, \d{4})', stated_at_text)
        if date_match:
            try:
                date_obj = datetime.strptime(date_match.group(1), '%B %d, %Y')
                stated_at = date_obj.strftime('%d.%m.%Y')
            except ValueError:
                stated_at = None

    # Extract original_rating from meter image alt text
    rating_elem = main_article.find('img', alt=True)
    original_rating = rating_elem['alt'] if rating_elem and 'alt' in rating_elem.attrs else None

    # Create result dictionary
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

    # Add to results list
    results.append(result)

    return results