from bs4 import BeautifulSoup
import re
from datetime import datetime
import json

def parse_factcheck(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')

    # Find the main article container
    article_container = soup.find('article') or soup.find('main') or soup.find('div', class_='left-column')

    if not article_container:
        return []

    # Initialize result list
    results = []

    # Extract language
    language = 'en'

    # Extract JSON-LD data
    json_ld_scripts = soup.find_all('script', type='application/ld+json')
    claim_review_data = None
    article_data = None

    for script in json_ld_scripts:
        try:
            data = json.loads(script.string)
            if data.get('@type') == 'ClaimReview':
                claim_review_data = data
            elif data.get('@type') == 'Article':
                article_data = data
        except:
            continue

    # Extract headline
    headline = None
    if article_data and article_data.get('headline'):
        headline = article_data['headline']
    elif soup.find('h1'):
        headline = soup.find('h1').get_text(strip=True)

    # Extract body text
    body = ''
    article_content = article_container.find('div', id='article-content')
    if article_content:
        for element in article_content.find_all(['p', 'h2', 'h3', 'h4', 'h5', 'h6', 'li', 'blockquote']):
            if element.name == 'p' or element.name in ['h2', 'h3', 'h4', 'h5', 'h6']:
                body += element.get_text(strip=True) + '\n\n'

    # Extract claim
    claim = None
    if claim_review_data and claim_review_data.get('claimReviewed'):
        claim = claim_review_data['claimReviewed']
    elif article_container.find('div', class_='claim_cont'):
        claim = article_container.find('div', class_='claim_cont').get_text(strip=True)

    # Extract author_factcheck
    author_factcheck = None
    if article_data and article_data.get('author') and article_data['author'].get('name'):
        author_factcheck = article_data['author']['name']
    elif soup.find('div', class_='author_name_box'):
        author_factcheck = soup.find('div', class_='author_name_box').get_text(strip=True)

    # Extract published_at
    published_at = None
    if article_data and article_data.get('datePublished'):
        try:
            published_at = datetime.strptime(article_data['datePublished'], '%Y-%m-%dT%H:%M:%SZ').strftime('%d.%m.%Y')
        except:
            published_at = None
    elif soup.find('h3', class_='publish_date'):
        date_text = soup.find('h3', class_='publish_date').get_text(strip=True)
        try:
            # Try to parse different date formats
            if 'Updated' in date_text:
                date_text = date_text.replace('Updated', '').strip()
            published_at = datetime.strptime(date_text, '%B %d, %Y').strftime('%d.%m.%Y')
        except:
            try:
                published_at = datetime.strptime(date_text, '%B %d, %Y').strftime('%d.%m.%Y')
            except:
                published_at = None

    # Extract author_claim
    author_claim = None
    if claim_review_data and claim_review_data.get('itemReviewed') and claim_review_data['itemReviewed'].get('author'):
        author_claim = claim_review_data['itemReviewed']['author'].get('name')
    elif claim and 'Trump' in claim:
        author_claim = 'Donald Trump'

    # Extract stated_at
    stated_at = None
    if claim_review_data and claim_review_data.get('datePublished'):
        try:
            stated_at = datetime.strptime(claim_review_data['datePublished'], '%Y-%m-%dT%H:%M:%SZ').strftime('%d.%m.%Y')
        except:
            stated_at = None

    # Extract original_rating
    original_rating = None
    if claim_review_data and claim_review_data.get('reviewRating') and claim_review_data['reviewRating'].get('alternateName'):
        original_rating = claim_review_data['reviewRating']['alternateName']
    elif article_container.find('a', id='main_rating'):
        original_rating = article_container.find('a', id='main_rating').get_text(strip=True)

    # Create result dictionary
    result = {
        'headline': headline,
        'body': body.strip() if body else None,
        'claim': claim,
        'author_factcheck': author_factcheck,
        'published_at': published_at,
        'language': language,
        'author_claim': author_claim,
        'stated_at': stated_at,
        'original_rating': original_rating
    }

    # Only add non-empty results
    if any(value is not None for value in result.values()):
        results.append(result)

    return results