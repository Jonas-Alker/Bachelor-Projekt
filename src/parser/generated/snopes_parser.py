from bs4 import BeautifulSoup
import re
from datetime import datetime

def parse_factcheck(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')

    # Extract structured data from JSON-LD scripts
    json_ld_scripts = soup.find_all('script', type='application/ld+json')
    structured_data = {}
    for script in json_ld_scripts:
        try:
            data = json.loads(script.string)
            if data.get('@type') == 'Article':
                structured_data['article'] = data
            elif data.get('@type') == 'ClaimReview':
                structured_data['claim_review'] = data
            elif data.get('@type') == 'Organization':
                structured_data['organization'] = data
            elif data.get('@type') == 'BreadcrumbList':
                structured_data['breadcrumb'] = data
        except:
            continue

    # Extract main headline
    headline = structured_data.get('article', {}).get('headline', None)

    # Extract body text
    body = None
    article_content = soup.find('article', id='article-content')
    if article_content:
        body = ' '.join(p.get_text() for p in article_content.find_all('p'))

    # Extract claim
    claim = structured_data.get('claim_review', {}).get('claimReviewed', None)

    # Extract author of factcheck
    author_factcheck = structured_data.get('article', {}).get('author', {}).get('name', None)

    # Extract published date
    published_at = structured_data.get('article', {}).get('datePublished', None)
    if published_at:
        try:
            published_at = datetime.strptime(published_at, '%Y-%m-%dT%H:%M:%SZ').strftime('%d.%m.%Y')
        except:
            published_at = None

    # Extract language
    language = 'en'

    # Extract author of claim
    author_claim = None
    claim_author = structured_data.get('claim_review', {}).get('itemReviewed', {}).get('author', {}).get('name', None)
    if claim_author:
        author_claim = claim_author

    # Extract stated date
    stated_at = None
    if structured_data.get('claim_review'):
        date_published = structured_data['claim_review'].get('datePublished', None)
        if date_published:
            try:
                stated_at = datetime.strptime(date_published, '%Y-%m-%dT%H:%M:%SZ').strftime('%d.%m.%Y')
            except:
                stated_at = None

    # Extract original rating
    original_rating = structured_data.get('claim_review', {}).get('reviewRating', {}).get('alternateName', None)

    # Return the parsed data
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

    return result