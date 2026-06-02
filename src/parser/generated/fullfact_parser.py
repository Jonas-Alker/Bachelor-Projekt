from bs4 import BeautifulSoup

from bs4 import BeautifulSoup
import json
import re
from datetime import datetime

def parse_faktencheck(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    data = []

    # Parse JSON-LD data
    json_ld_scripts = soup.find_all('script', type='application/ld+json')
    claim_review = None
    article_data = None

    for script in json_ld_scripts:
        try:
            json_data = json.loads(script.string)
            if isinstance(json_data, list):
                for item in json_data:
                    if item.get('@type') == 'ClaimReview':
                        claim_review = item
                    elif item.get('@type') == 'Article':
                        article_data = item
            elif isinstance(json_data, dict):
                if json_data.get('@type') == 'ClaimReview':
                    claim_review = json_data
                elif json_data.get('@type') == 'Article':
                    article_data = json_data
        except (json.JSONDecodeError, AttributeError):
            continue

    # Extract claim information
    if claim_review:
        claim = claim_review.get('claimReviewed', '')
        rating = claim_review.get('reviewRating', {}).get('alternateName', '')
        claim_date_str = claim_review.get('datePublished', '')

        try:
            claim_date = datetime.strptime(claim_date_str, '%Y-%m-%d').strftime('%Y-%m-%d') if claim_date_str else None
        except (ValueError, TypeError):
            claim_date = None

        # Extract article information
        article_date_str = article_data.get('datePublished', '') if article_data else ''
        try:
            article_date = datetime.strptime(article_date_str, '%Y-%m-%dT%H:%M:%S%z').strftime('%Y-%m-%d') if article_date_str else None
        except (ValueError, TypeError):
            try:
                article_date = datetime.strptime(article_date_str, '%Y-%m-%d %H:%M:%S.%f%z').strftime('%Y-%m-%d') if article_date_str else None
            except (ValueError, TypeError):
                article_date = None

        title = article_data.get('headline', '') if article_data else ''
        language = 'en'  # Default language for this site

        # Find claim text in HTML
        claim_text_element = soup.find('p', class_='card-text')
        claim_text = claim_text_element.get_text(strip=True) if claim_text_element else claim

        # Find rating text in HTML
        rating_text_element = soup.find('p', class_='card-text', string=re.compile(r'False|True|Mostly|Partly', re.IGNORECASE))
        rating_text = rating_text_element.get_text(strip=True) if rating_text_element else rating

        data.append({
            'claim': claim_text,
            'artikel_datum': article_date,
            'sprache': language,
            'claim_datum': claim_date,
            'title': title,
            'rating': rating_text
        })

    return data

#For testing purposes only during programming
import requests
if __name__ == "__main__":
    test_url = "https://fullfact.org/politics/city-council-meeting-video-miscaptioned/"

    response = requests.get(test_url)
    r = response.text
    response.raise_for_status()

    print(parse_faktencheck(r))
