from bs4 import BeautifulSoup
import json
from datetime import datetime

def parse_factcheck(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Locate the primary article container
    main_container = soup.find('main', class_='fact-check')
    if not main_container:
        main_container = soup.find('article')
    
    if not main_container:
        return []
    
    # Initialize result list
    results = []
    
    # Extract JSON-LD data
    ld_scripts = main_container.find_all('script', type='application/ld+json')
    claim_review_data = None
    article_data = None
    
    for script in ld_scripts:
        try:
            data = json.loads(script.string)
            if isinstance(data, list):
                for item in data:
                    if item.get('@type') == 'ClaimReview':
                        claim_review_data = item
                    elif item.get('@type') == 'Article':
                        article_data = item
            elif isinstance(data, dict):
                if data.get('@type') == 'ClaimReview':
                    claim_review_data = data
                elif data.get('@type') == 'Article':
                    article_data = data
        except (json.JSONDecodeError, AttributeError):
            continue
    
    # Extract headline
    headline = None
    if article_data and 'headline' in article_data:
        headline = article_data['headline']
    
    # Extract body text
    body = ''
    body_div = main_container.find('div', class_='cms-content')
    if body_div:
        for p in body_div.find_all('p', recursive=True):
            if p.get('data-nosnippet') is None:
                body += p.get_text(strip=True) + ' '
    
    # Extract claim
    claim = None
    if claim_review_data and 'claimReviewed' in claim_review_data:
        claim = claim_review_data['claimReviewed']
    
    # Extract author_factcheck
    author_factcheck = None
    if claim_review_data and 'author' in claim_review_data and isinstance(claim_review_data['author'], dict):
        author_factcheck = claim_review_data['author'].get('name')
    elif article_data and 'author' in article_data:
        authors = article_data['author']
        if isinstance(authors, list):
            author_factcheck = ', '.join([a.get('name', '') for a in authors if 'name' in a])
        elif isinstance(authors, dict):
            author_factcheck = authors.get('name')
    
    # Extract published_at
    published_at = None
    if article_data and 'datePublished' in article_data:
        date_str = article_data['datePublished']
        try:
            if 'T' in date_str:
                dt = datetime.fromisoformat(date_str)
            else:
                dt = datetime.strptime(date_str, '%Y-%m-%d')
            published_at = dt.strftime('%d.%m.%Y')
        except (ValueError, TypeError):
            pass
    
    # Extract language
    language = 'en'
    
    # Extract author_claim
    author_claim = None
    if claim_review_data and 'claimReviewed' in claim_review_data:
        # Try to extract from claim text if it contains the author
        claim_text = claim_review_data['claimReviewed']
        if 'by' in claim_text.lower():
            parts = claim_text.split('by')
            if len(parts) > 1:
                author_claim = parts[-1].strip()
    
    # Extract stated_at
    stated_at = None
    if claim_review_data and 'datePublished' in claim_review_data:
        date_str = claim_review_data['datePublished']
        try:
            if 'T' in date_str:
                dt = datetime.fromisoformat(date_str)
            else:
                dt = datetime.strptime(date_str, '%Y-%m-%d')
            stated_at = dt.strftime('%d.%m.%Y')
        except (ValueError, TypeError):
            pass
    
    # Extract original_rating
    original_rating = None
    if claim_review_data and 'reviewRating' in claim_review_data:
        rating = claim_review_data['reviewRating']
        if isinstance(rating, dict):
            original_rating = rating.get('alternateName')
    
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
    
    results.append(result)
    
    return results