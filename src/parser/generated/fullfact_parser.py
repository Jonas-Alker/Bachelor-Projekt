from bs4 import BeautifulSoup
import json
from datetime import datetime

def parse_factcheck(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    results = []

    # Extract schema.org ClaimReview data
    claim_review_data = None
    script_tags = soup.find_all('script', type='application/ld+json')
    for script in script_tags:
        try:
            data = json.loads(script.string)
            if isinstance(data, list):
                for item in data:
                    if item.get('@type') == 'ClaimReview':
                        claim_review_data = item
                        break
            elif isinstance(data, dict) and data.get('@type') == 'ClaimReview':
                claim_review_data = data
        except (json.JSONDecodeError, AttributeError):
            continue

    # Extract schema.org Article data
    article_data = None
    for script in script_tags:
        try:
            data = json.loads(script.string)
            if isinstance(data, dict) and data.get('@type') == 'Article':
                article_data = data
                break
        except (json.JSONDecodeError, AttributeError):
            continue

    # Extract main claim information
    claim = None
    original_rating = None
    stated_at = None
    if claim_review_data:
        claim = claim_review_data.get('claimReviewed')
        original_rating = claim_review_data.get('reviewBody')
        stated_at_str = claim_review_data.get('datePublished')
        if stated_at_str:
            try:
                stated_at = datetime.strptime(stated_at_str, '%Y-%m-%d').strftime('%d.%m.%Y')
            except ValueError:
                try:
                    stated_at = datetime.strptime(stated_at_str.split('T')[0], '%Y-%m-%d').strftime('%d.%m.%Y')
                except ValueError:
                    stated_at = None

    # Extract article information
    headline = None
    published_at = None
    author_factcheck = None
    language = 'en'
    if article_data:
        headline = article_data.get('headline')
        date_str = article_data.get('datePublished')
        if date_str:
            try:
                published_at = datetime.strptime(date_str, '%Y-%m-%dT%H:%M:%S%z').strftime('%d.%m.%Y')
            except ValueError:
                try:
                    published_at = datetime.strptime(date_str.split('T')[0], '%Y-%m-%d').strftime('%d.%m.%Y')
                except ValueError:
                    published_at = None
        author = article_data.get('author')
        if author and isinstance(author, list):
            for a in author:
                if a.get('@type') == 'Person':
                    author_factcheck = a.get('name')
                    break
        elif author and isinstance(author, dict) and author.get('@type') == 'Person':
            author_factcheck = author.get('name')

    # Extract author of the claim
    author_claim = None
    if claim_review_data and claim_review_data.get('author'):
        author_obj = claim_review_data.get('author')
        if isinstance(author_obj, dict) and author_obj.get('@type') == 'Organization':
            author_claim = author_obj.get('name')

    # Extract body text (main content)
    body = ''
    content_divs = soup.find_all('div', class_=lambda x: x and 'block-rich_text' in x)
    for div in content_divs:
        if div.find_parent(['div', 'section'], class_=lambda x: x and ('Read More' in x or 'Related' in x or 'Latest' in x or 'Trending' in x)):
            continue
        paragraphs = div.find_all('p', recursive=False)
        for p in paragraphs:
            if p.get('data-block-key'):
                body += p.get_text(strip=True) + ' '

    # Clean up body text
    body = ' '.join(body.split())

    # Create result dictionary
    if claim or original_rating:
        result = {
            'headline': headline,
            'body': body if body else None,
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