from bs4 import BeautifulSoup
import re
from datetime import datetime
import json

def parse_factcheck(html_content):
    """
    Parse fact-checking article HTML content and extract structured data.

    Args:
        html_content (str): HTML content of a fact-checking article

    Returns:
        list: List of dictionaries containing parsed fact-check data
    """

    # Parse HTML with BeautifulSoup
    soup = BeautifulSoup(html_content, 'html.parser')

    # Find the main article container
    article_container = soup.find('section', class_='main_outer_wrapper')
    if not article_container:
        return []

    # Initialize result list
    results = []

    # Extract language (default to English)
    language = 'en'

    # Extract headline
    headline_element = article_container.find('h1')
    headline = headline_element.get_text(strip=True) if headline_element else None

    # Extract body content
    body_element = article_container.find('article', id='article-content')
    body = ''
    if body_element:
        # Remove unwanted elements (ads, scripts, etc.)
        for unwanted in body_element.find_all(['script', 'style', 'iframe', 'div', 'span', 'svg', 'button', 'nav', 'aside', 'footer', 'form']):
            unwanted.decompose()

        # Get text content
        body = body_element.get_text(separator='\n', strip=True)

    # Extract claim from ClaimReview JSON-LD
    claim = None
    claim_review_script = soup.find('script', type='application/ld+json')
    if claim_review_script:
        try:
            claim_data = json.loads(claim_review_script.string)
            if claim_data.get('@type') == 'ClaimReview':
                claim = claim_data.get('claimReviewed')
        except (json.JSONDecodeError, AttributeError):
            pass

    # Extract author_factcheck from Article JSON-LD
    author_factcheck = None
    article_script = soup.find('script', type='application/ld+json')
    if article_script:
        try:
            article_data = json.loads(article_script.string)
            if article_data.get('@type') == 'Article':
                author_data = article_data.get('author', {})
                if isinstance(author_data, dict):
                    author_factcheck = author_data.get('name')
                elif isinstance(author_data, list) and len(author_data) > 0:
                    author_factcheck = author_data[0].get('name')
        except (json.JSONDecodeError, AttributeError):
            pass

    # Extract published_at from Article JSON-LD
    published_at = None
    if article_script:
        try:
            article_data = json.loads(article_script.string)
            if article_data.get('@type') == 'Article':
                date_published = article_data.get('datePublished')
                if date_published:
                    try:
                        # Parse ISO format date
                        dt = datetime.fromisoformat(date_published.replace('Z', '+00:00'))
                        published_at = dt.strftime('%d.%m.%Y')
                    except (ValueError, TypeError):
                        published_at = date_published
        except (json.JSONDecodeError, AttributeError):
            pass

    # Extract author_claim from the article content
    author_claim = None
    # Look for "By" or "By " in the article
    by_match = re.search(r'By\s+([^<]+)', str(article_container), re.IGNORECASE)
    if by_match:
        author_claim = by_match.group(1).strip()

    # Extract stated_at from the article content
    stated_at = None
    # Look for date patterns in the article
    date_patterns = [
        r'Published\s+([A-Za-z]+\s+\d{1,2},\s+\d{4})',
        r'Published\s+([A-Za-z]+\s+\d{1,2}\s+\d{4})',
        r'Published\s+(\d{1,2}\s+[A-Za-z]+\s+\d{4})',
        r'([A-Za-z]+\s+\d{1,2},\s+\d{4})'
    ]

    for pattern in date_patterns:
        date_match = re.search(pattern, str(article_container))
        if date_match:
            date_str = date_match.group(1)
            try:
                # Parse month name and year
                dt = datetime.strptime(date_str, '%B %d, %Y')
                stated_at = dt.strftime('%d.%m.%Y')
                break
            except (ValueError, TypeError):
                try:
                    # Try different format
                    dt = datetime.strptime(date_str, '%B %d %Y')
                    stated_at = dt.strftime('%d.%m.%Y')
                    break
                except (ValueError, TypeError):
                    try:
                        # Try day month year format
                        dt = datetime.strptime(date_str, '%d %B %Y')
                        stated_at = dt.strftime('%d.%m.%Y')
                        break
                    except (ValueError, TypeError):
                        pass

    # Extract original_rating from the rating section
    original_rating = None
    rating_element = article_container.find('a', id='main_rating')
    if rating_element:
        original_rating = rating_element.get_text(strip=True)

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

    # Only add non-empty results
    if any(value for value in result.values() if value is not None):
        results.append(result)

    return results