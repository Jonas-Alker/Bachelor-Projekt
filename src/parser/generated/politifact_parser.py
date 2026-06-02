from bs4 import BeautifulSoup

from bs4 import BeautifulSoup
import json
from datetime import datetime

def parse_faktencheck(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    results = []

    # Find all statement articles
    statements = soup.find_all('article', class_=lambda x: x and 'm-statement' in x)

    for statement in statements:
        claim_element = statement.find('div', class_='m-statement__quote')
        claim = claim_element.get_text(strip=True) if claim_element else None

        claim_date_element = statement.find('div', class_='m-statement__desc')
        claim_date = claim_date_element.get_text(strip=True) if claim_date_element else None

        # Extract claim date from the statement description
        claim_date_parsed = None
        if claim_date:
            # Try to extract date from text like "stated on May 20, 2026 in an X post"
            try:
                date_str = claim_date.split('stated on ')[1].split(' in ')[0]
                claim_date_parsed = datetime.strptime(date_str, '%B %d, %Y').strftime('%Y-%m-%d')
            except (IndexError, ValueError):
                pass

        # Find rating
        rating_element = statement.find('img', alt=True)
        rating = rating_element['alt'].lower() if rating_element and rating_element.get('alt') else None

        # Find title
        title_element = soup.find('h1', class_='c-title')
        title = title_element.get_text(strip=True) if title_element else None

        # Find article date
        article_date_element = soup.find('span', class_='m-author__date')
        artikel_datum = article_date_element.get_text(strip=True) if article_date_element else None

        # Language (default to 'en' for English)
        sprache = 'en'

        # Create result dictionary
        result = {
            'claim': claim,
            'artikel_datum': artikel_datum,
            'sprache': sprache,
            'claim_datum': claim_date_parsed,
            'title': title,
            'rating': rating
        }

        # Replace None with null
        for key in result:
            if result[key] is None:
                result[key] = None

        results.append(result)

    return json.dumps(results)

#For testing purposes only during programming
import requests
if __name__ == "__main__":
    test_url = "https://www.politifact.com/factchecks/2026/may/14/kathy-castor/kid-care-florida-desantis-health-insurance/"

    response = requests.get(test_url)
    r = response.text
    response.raise_for_status()

    print(parse_faktencheck(r))
