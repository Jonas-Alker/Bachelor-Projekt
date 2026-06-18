from bs4 import BeautifulSoup
from datetime import datetime
import re

def parse_factcheck(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    results = []

    # Find all statement articles
    statement_articles = soup.find_all('article', class_=lambda x: x and 'm-statement' in x.split())

    for article in statement_articles:
        # Extract claim and claim author
        claim_author_tag = article.find('a', class_='m-statement__name')
        claim_author = claim_author_tag.get_text(strip=True) if claim_author_tag else None

        claim_text_tag = article.find('div', class_='m-statement__quote')
        claim = claim_text_tag.get_text(strip=True) if claim_text_tag else None

        # Extract stated_at date
        stated_at_tag = article.find('div', class_='m-statement__desc')
        stated_at = None
        if stated_at_tag:
            stated_at_text = stated_at_tag.get_text(strip=True)
            # Extract date from text like "stated on April 29, 2026 in an X post"
            date_match = re.search(r'stated on (\w+ \d{1,2},? \d{4})', stated_at_text)
            if date_match:
                try:
                    stated_at = datetime.strptime(date_match.group(1), '%B %d, %Y').strftime('%d.%m.%Y')
                except ValueError:
                    pass

        # Extract original rating
        rating_img = article.find('img', alt=lambda x: x and x in ['true', 'mostly-true', 'half-true', 'mostly-false', 'false', 'pants-fire'])
        original_rating = rating_img['alt'] if rating_img else None

        # Extract headline from title or h1
        headline_tag = soup.find('h1', class_='c-title')
        headline = headline_tag.get_text(strip=True) if headline_tag else None

        # Extract body text
        body_tag = soup.find('article', class_='m-textblock')
        body = None
        if body_tag:
            body = body_tag.get_text(strip=True)

        # Extract author_factcheck
        author_tag = soup.find('a', href=lambda x: x and '/staff/' in x)
        author_factcheck = author_tag.get_text(strip=True) if author_tag else None

        # Extract published_at
        date_tag = soup.find('span', class_='m-author__date')
        published_at = None
        if date_tag:
            date_text = date_tag.get_text(strip=True)
            # Extract date from text like "May 14, 2026"
            date_match = re.search(r'(\w+ \d{1,2}, \d{4})', date_text)
            if date_match:
                try:
                    published_at = datetime.strptime(date_match.group(1), '%B %d, %Y').strftime('%d.%m.%Y')
                except ValueError:
                    pass

        # Language is always English for this site
        language = 'en'

        # Create result dictionary
        result = {
            'headline': headline,
            'body': body,
            'claim': claim,
            'author_factcheck': author_factcheck,
            'published_at': published_at,
            'language': language,
            'author_claim': claim_author,
            'stated_at': stated_at,
            'original_rating': original_rating
        }
        results.append(result)

    return results