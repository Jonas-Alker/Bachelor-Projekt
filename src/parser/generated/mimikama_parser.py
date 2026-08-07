from bs4 import BeautifulSoup
import re
from datetime import datetime
import locale

def parse_factcheck(html_content):
    """
    Parse fact-checking article HTML content and extract structured data.

    Args:
        html_content (str): HTML content of the fact-checking article

    Returns:
        list: List of dictionaries containing parsed fact-checking data
    """

    # Set locale for German date parsing
    locale.setlocale(locale.LC_TIME, 'de_DE.UTF-8')

    soup = BeautifulSoup(html_content, 'html.parser')

    # Extract all fact-check entries (multiple claims per article)
    entries = []

    # Find the main content area
    main_content = soup.find('div', class_='entry-content')
    if not main_content:
        return entries

    # Extract language
    language = 'de'  # Default to German

    # Extract author of fact-check
    author_factcheck = None
    author_element = soup.find('a', class_='url fn n')
    if author_element:
        author_factcheck = author_element.get_text(strip=True)

    # Extract publication date
    published_at = None
    published_element = soup.find('time', class_='entry-date published')
    if published_element and 'datetime' in published_element.attrs:
        try:
            published_at = datetime.strptime(published_element['datetime'], '%Y-%m-%dT%H:%M:%S%z')
            published_at = published_at.strftime('%d.%m.%Y')
        except:
            pass

    # Extract last update date
    updated_at = None
    updated_element = soup.find('time', class_='updated')
    if updated_element and 'datetime' in updated_element.attrs:
        try:
            updated_at = datetime.strptime(updated_element['datetime'], '%Y-%m-%dT%H:%M:%S%z')
            updated_at = updated_at.strftime('%d.%m.%Y')
        except:
            pass

    # Extract headline
    headline = None
    headline_element = soup.find('h1', class_='entry-title')
    if headline_element:
        headline = headline_element.get_text(strip=True)

    # Extract body text (main article content)
    body = None
    body_element = soup.find('div', class_='entry-content')
    if body_element:
        # Remove unwanted elements (widgets, related articles, etc.)
        for unwanted in body_element.find_all(['div', 'section'], class_=re.compile(r'(Read More|Related|Latest|Trending|mk-cta-stack|mk-cluster-footer|mimikama-sources|mimikama-footer)', re.IGNORECASE)):
            unwanted.decompose()

        # Remove script and style elements
        for script in body_element.find_all(['script', 'style']):
            script.decompose()

        # Get clean text
        body = body_element.get_text(separator='\n', strip=True)

    # Extract claims and ratings
    claim_elements = main_content.find_all(['p', 'div'], class_=re.compile(r'(behauptung-box|claim|Behauptung|Claim)', re.IGNORECASE))

    for claim_element in claim_elements:
        # Skip if this is a widget or container element
        if any(unwanted in str(claim_element) for unwanted in ['Read More', 'Related', 'Latest', 'Trending']):
            continue

        claim = None
        claim_text = claim_element.get_text(separator=' ', strip=True)

        # Clean up claim text
        if claim_text:
            claim = claim_text.replace('Die Behauptung', '').strip()
            claim = re.sub(r'\s+', ' ', claim)

        # Extract author of claim
        author_claim = None
        claim_source = claim_element.find('p', class_=re.compile(r'behauptung-quelle|claim-source', re.IGNORECASE))
        if claim_source:
            author_claim_text = claim_source.get_text(strip=True)
            if 'Aufgestellt von:' in author_claim_text:
                author_claim = author_claim_text.replace('Aufgestellt von:', '').strip()
            elif 'Quelle:' in author_claim_text:
                author_claim = author_claim_text.replace('Quelle:', '').strip()

        # Extract stated_at date (when claim was made)
        stated_at = None
        stated_element = claim_element.find_next('time')
        if stated_element and 'datetime' in stated_element.attrs:
            try:
                stated_at = datetime.strptime(stated_element['datetime'], '%Y-%m-%dT%H:%M:%S%z')
                stated_at = stated_at.strftime('%d.%m.%Y')
            except:
                pass

        # Extract original rating
        original_rating = None
        rating_element = main_content.find('div', class_=re.compile(r'bewertung-1|bewertung-\d+', re.IGNORECASE))
        if rating_element:
            rating_text = rating_element.get_text(separator=' ', strip=True)
            if 'Faktencheck:' in rating_text:
                original_rating = rating_text.replace('Faktencheck:', '').strip()
            elif 'Ergebnis:' in rating_text:
                original_rating = rating_text.replace('Ergebnis:', '').strip()

        # Create entry
        entry = {
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

        # Only add if we have a claim
        if entry['claim']:
            entries.append(entry)

    # If no claims found, create a single entry with available data
    if not entries and (headline or body):
        entry = {
            'headline': headline,
            'body': body,
            'claim': None,
            'author_factcheck': author_factcheck,
            'published_at': published_at,
            'language': language,
            'author_claim': None,
            'stated_at': None,
            'original_rating': None
        }
        entries.append(entry)

    return entries