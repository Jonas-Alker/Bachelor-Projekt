from bs4 import BeautifulSoup
import json
from datetime import datetime

def parse_factcheck(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Find the main article container
    main_container = soup.find('main', class_='fact-check')
    if not main_container:
        main_container = soup.find('article')
    if not main_container:
        main_container = soup.find('div', class_='container')
    
    if not main_container:
        return []
    
    results = []
    
    # Parse JSON-LD data
    json_ld_scripts = main_container.find_all('script', type='application/ld+json')
    claim_review_data = None
    article_data = None
    
    for script in json_ld_scripts:
        try:
            data = json.loads(script.string)
            if isinstance(data, list):
                for item in data:
                    if isinstance(item, dict) and item.get('@type') == 'ClaimReview':
                        claim_review_data = item
                    elif isinstance(item, dict) and item.get('@type') == 'Article':
                        article_data = item
            elif isinstance(data, dict):
                if data.get('@type') == 'ClaimReview':
                    claim_review_data = data
                elif data.get('@type') == 'Article':
                    article_data = data
        except (json.JSONDecodeError, AttributeError):
            continue
    
    # Extract data from ClaimReview
    claim = None
    original_rating = None
    stated_at = None
    author_claim = None
    
    if claim_review_data:
        claim = claim_review_data.get('claimReviewed')
        review_rating = claim_review_data.get('reviewRating', {})
        original_rating = review_rating.get('alternateName')
        date_published = claim_review_data.get('datePublished')
        if date_published:
            try:
                stated_at = datetime.strptime(date_published, '%Y-%m-%d').strftime('%d.%m.%Y')
            except ValueError:
                try:
                    stated_at = datetime.strptime(date_published.split('T')[0], '%Y-%m-%d').strftime('%d.%m.%Y')
                except ValueError:
                    stated_at = None
    
    # Extract data from Article
    headline = None
    published_at = None
    author_factcheck = None
    language = 'en'
    
    if article_data:
        headline = article_data.get('headline')
        date_published = article_data.get('datePublished')
        if date_published:
            try:
                published_at = datetime.strptime(date_published.split('T')[0], '%Y-%m-%d').strftime('%d.%m.%Y')
            except ValueError:
                try:
                    published_at = datetime.strptime(date_published, '%Y-%m-%d').strftime('%d.%m.%Y')
                except ValueError:
                    published_at = None
        
        author = article_data.get('author', [])
        if author and isinstance(author, list):
            for a in author:
                if isinstance(a, dict) and a.get('@type') == 'Person':
                    author_factcheck = a.get('name')
    
    # Extract body text from the main article
    body = ''
    article_body = main_container.find('div', class_='cms-content')
    if article_body:
        for p in article_body.find_all('p', recursive=False):
            if p.get('data-block-key') or p.find_parent('div', class_='block-rich_text'):
                body += p.get_text(strip=True) + ' '
    
    # Extract claim from the claim card
    claim_card = main_container.find('div', class_='card-claim-body')
    if claim_card:
        claim_text = claim_card.find('p', class_='card-text')
        if claim_text:
            claim = claim_text.get_text(strip=True)
    
    # Extract original rating from the conclusion card
    conclusion_card = main_container.find('div', class_='card-conclusion-body')
    if conclusion_card:
        original_rating = conclusion_card.find('p', class_='card-text')
        if original_rating:
            original_rating = original_rating.get_text(strip=True)
    
    # Extract author from the citation section
    citation = main_container.find('cite', class_='citation')
    if not citation:
        citation = main_container.find('a', href=lambda x: x and '/authors/' in x)
    
    if citation:
        author_factcheck = citation.get_text(strip=True)
    
    # Create result dictionary
    result = {
        'headline': headline,
        'body': body.strip() if body else None,
        'claim': claim,
        'author_factcheck': author_factcheck,
        'published_at': published_at,
        'language': language,
        'author_claim': None,
        'stated_at': stated_at,
        'original_rating': original_rating
    }
    
    results.append(result)
    
    return results