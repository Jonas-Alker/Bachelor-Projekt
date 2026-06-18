from bs4 import BeautifulSoup
import re
from datetime import datetime

def parse_factcheck(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Find the main article container
    main_article = soup.find('article', class_='m-textblock')
    if not main_article:
        return []

    # Initialize result list
    results = []

    # Extract language from html lang attribute
    language = soup.find('html').get('lang', None)

    # Extract author_factcheck and published_at from the author section
    author_section = soup.find('div', class_='m-author')
    author_factcheck = None
    published_at = None
    if author_section:
        author_link = author_section.find('a')
        if author_link:
            author_factcheck = author_link.get_text(strip=True)
        date_span = author_section.find('span', class_='m-author__date')
        if date_span:
            published_at_str = date_span.get_text(strip=True)
            try:
                # Parse date string like "May 14, 2026"
                published_at = datetime.strptime(published_at_str, '%B %d, %Y').strftime('%d.%m.%Y')
            except ValueError:
                pass

    # Extract headline from h1
    headline = None
    h1 = soup.find('h1', class_='c-title')
    if h1:
        headline = h1.get_text(strip=True)

    # Extract body text from the main article
    body = None
    if main_article:
        body = main_article.get_text(separator='\n', strip=True)

    # Extract claim from the statement section
    claim = None
    statement_section = soup.find('article', class_='m-statement')
    if statement_section:
        claim_quote = statement_section.find('div', class_='m-statement__quote')
        if claim_quote:
            claim = claim_quote.get_text(strip=True)

    # Extract author_claim and stated_at from the statement section
    author_claim = None
    stated_at = None
    if statement_section:
        author_meta = statement_section.find('div', class_='m-statement__meta')
        if author_meta:
            author_link = author_meta.find('a', class_='m-statement__name')
            if author_link:
                author_claim = author_link.get_text(strip=True)
            desc = author_meta.find('div', class_='m-statement__desc')
            if desc:
                stated_at_str = desc.get_text(strip=True)
                # Extract date from "stated on April 29, 2026 in an X post"
                date_match = re.search(r'(\w+ \d{1,2}, \d{4})', stated_at_str)
                if date_match:
                    try:
                        stated_at = datetime.strptime(date_match.group(1), '%B %d, %Y').strftime('%d.%m.%Y')
                    except ValueError:
                        pass

    # Extract original_rating from the meter section
    original_rating = None
    meter_section = statement_section.find('div', class_='m-statement__meter')
    if meter_section:
        img = meter_section.find('img')
        if img and 'alt' in img.attrs:
            original_rating = img['alt']

    # Create the result dictionary
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

    # Add to results list
    results.append(result)

    return results