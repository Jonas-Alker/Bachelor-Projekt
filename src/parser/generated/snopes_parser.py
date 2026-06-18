from bs4 import BeautifulSoup
import re
from datetime import datetime
import json

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

    # Extract main rating from ClaimReview
    original_rating = None
    if 'claim_review' in structured_data:
        review = structured_data['claim_review']
        if 'reviewRating' in review:
            rating = review['reviewRating']
            if 'alternateName' in rating:
                original_rating = rating['alternateName']

    # Extract claim from ClaimReview
    claim = None
    if 'claim_review' in structured_data:
        review = structured_data['claim_review']
        if 'claimReviewed' in review:
            claim = review['claimReviewed']

    # Extract headline from Article
    headline = None
    if 'article' in structured_data:
        article = structured_data['article']
        if 'headline' in article:
            headline = article['headline']

    # Extract author from Article
    author_factcheck = None
    if 'article' in structured_data:
        article = structured_data['article']
        if 'author' in article:
            author = article['author']
            if 'name' in author:
                author_factcheck = author['name']

    # Extract published date from Article
    published_at = None
    if 'article' in structured_data:
        article = structured_data['article']
        if 'datePublished' in article:
            published_at = article['datePublished']

    # Extract modified date from Article
    modified_at = None
    if 'article' in structured_data:
        article = structured_data['article']
        if 'dateModified' in article:
            modified_at = article['dateModified']

    # Format dates
    def format_date(date_str):
        if not date_str:
            return None
        try:
            dt = datetime.strptime(date_str, '%Y-%m-%dT%H:%M:%SZ')
            return dt.strftime('%d.%m.%Y')
        except:
            return None

    published_at = format_date(published_at)
    modified_at = format_date(modified_at)

    # Extract author of claim from page content
    author_claim = None
    claim_element = soup.find('div', class_='claim_cont')
    if claim_element:
        claim_text = claim_element.get_text(strip=True)
        # Look for patterns like "U.S. President Donald Trump" or similar
        claim_author_pattern = re.compile(r'(?:U\.S\.|President|Vice\s+President|Senator|Rep\.|Governor)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)', re.IGNORECASE)
        match = claim_author_pattern.search(claim_text)
        if match:
            author_claim = match.group(1)

    # Extract stated_at date from page content
    stated_at = None
    article_content = soup.find('article', id='article-content')
    if article_content:
        text = article_content.get_text()
        # Look for date patterns in the article text
        date_pattern = re.compile(r'(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},\s+\d{4}')
        match = date_pattern.search(text)
        if match:
            stated_at_str = match.group(0)
            try:
                dt = datetime.strptime(stated_at_str, '%B %d, %Y')
                stated_at = dt.strftime('%d.%m.%Y')
            except:
                pass

    # Extract language
    language = 'en'

    # Extract body text
    body = None
    article_content = soup.find('article', id='article-content')
    if article_content:
        # Remove unwanted elements
        for element in article_content.find_all(['div', 'section', 'aside', 'script', 'style', 'iframe', 'svg']):
            element.decompose()

        # Get all paragraphs
        paragraphs = article_content.find_all('p')
        body = '\n\n'.join([p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True)])

    # Return result
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