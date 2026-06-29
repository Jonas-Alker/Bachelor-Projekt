import requests
import json
import os
from dotenv import load_dotenv
from pathlib import Path
import logging

#Getting Logger
logger = logging.getLogger(__name__)

# Configuration
load_dotenv()
API_KEY = os.getenv("KICONNECT_API_KEY")
API_URL = "https://chat.kiconnect.nrw/api/v1/chat/completions"
MODEL_ID = "MistralSmall_4"

if not API_KEY:
    print("Error: API_KEY is empty!")

# Target
OUTPUT_DIR_PARSER= Path(__file__).resolve().parent.parent / "src" / "parser" / "generated"

def load_html(url):
    """
    Downloads the HTML from the URL provided

    :param url: url to download
    :return: HTML content
    """
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.text

    except Exception as e:
        print(f"Error loading URL: {e}")
        return None

def load_few_shots():
    """
        Loads a few shot partial prompt, if any are stored in the file 'data/parser/few_shot_examples.json'.
        :return: few shot partial prompt
        """
    path = Path(__file__).resolve().parent.parent / "data" / "parser" / "few_shot_examples.json"
    with open(path, "r", encoding="utf-8") as f:
        examples = json.load(f)
    few_shots_message = []
    for ex in examples:
        few_shots_message.append({
            "role": "user",
            "content": f"Write the complete BeautifulSoup4 parser for this type of HTML page:\n{ex['input_html']}"})
        few_shots_message.append({"role": "assistant", "content": json.dumps(ex["expected_output"])})
    return few_shots_message

def generate_parser(url, portal_name):
    html = load_html(url)
    if not html:
       return
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {API_KEY}"
    }

    system_prompt = (
        """
        You are a Senior Data Engineer. Your task is to write a BeautifulSoup4 parser script for fact-checking websites.
        The function must be named `parse_factcheck(html_content)` and must return a Python list of dictionaries (which represents a JSON array).
        
        Actively avoid extracting claims, headlines, or ratings from widgets containing classes/IDs related to "Read More", "Related", "Latest", or "Trending".

        OUTPUT FORMAT:
        Each dictionary in the list MUST contain exactly the following keys:
        'headline', 'body' (the main text of the article), 'claim', 'author_factcheck', 'published_at', 'language',
        'author_claim', 'stated_at' (when the claim was made) and 'original_rating' (the exact wording from the page).
        If a field does not exist or cannot be found in the HTML, set its value to `None`.
        If there are multiple claims in the HTML, add a new dictionary to the list for each claim.
        
        CRITICAL DATE DEFINITIONS:
        - 'published_at': The date when this specific fact-checking article was published or updated by the fact-checker. 
        - 'stated_at': The date when the original claim was made, posted, or spoken by the person or entity being checked. 
        This is usually an older date than published_at.
        
        CRITICAL AUTHOR DEFINITIONS:
        - 'author_factcheck': The author of the fact-checking article, sometime called fact-checker.
        - 'author_claim': The author of the claim, usually a public figure.
        The generated Python code must attempt to format extracted dates as 'DD.MM.YYYY'.
        Do NOT use excessively complex regular expressions (`re.compile`) for class matching to avoid syntax errors; prefer standard string lists.
        Return EXCLUSIVELY the executable Python code. Do not include markdown formatting like ```python, explanations, or usage examples.
        """
    )
    messages = [{"role": "system", "content": system_prompt}]
    messages.extend(load_few_shots())
    messages.append({
        "role": "user",
        "content": f"Write the complete BeautifulSoup4 parser for this type of HTML page:\n\n{html}"})

    data = {
        "model": MODEL_ID,
        "messages": messages,
        "temperature": 0.0,
    }

    try:
        response = requests.post(API_URL, headers=headers, json=data)
        response.raise_for_status()

        parser_code = response.json()["choices"][0]["message"]["content"]
        parser_code = parser_code.replace("```python", "").replace("```", "").strip()

        os.makedirs(OUTPUT_DIR_PARSER, exist_ok=True)
        path = os.path.join(OUTPUT_DIR_PARSER, f"{portal_name.lower()}_parser.py")

        with open(path, "w", encoding="utf-8") as f:
            f.write(parser_code)

        logger.info(f"Successfully generated parser for {portal_name.lower()}")

    except Exception as e:
        logger.error(f"Failed to generate parser for {portal_name.lower()}: {e}")
