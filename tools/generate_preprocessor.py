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
OUTPUT_DIR_PREPROCESSOR= Path(__file__).resolve().parent.parent / "src" / "preprocessor" / "generated"

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
    path = Path(__file__).resolve().parent.parent / "data" / "preprocessor" / "few_shot_examples.json"
    with open(path, "r", encoding="utf-8") as f:
        examples = json.load(f)
    few_shots_message = []
    for ex in examples:
        few_shots_message.append({
            "role": "user",
            "content": f"Write the complete BeautifulSoup4 preprocessor for this type of HTML page::\n{ex['input_html']}"})
        few_shots_message.append({"role": "assistant", "content": json.dumps(ex["expected_output"])})
    return few_shots_message
def generate_preprocessor(url, portal_name):
    html = load_html(url)
    if not html:
       return
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {API_KEY}"
    }

    system_prompt = (
        """
        You are a Senior Data Engineer. Your task is to write a BeautifulSoup4 preprocessor script for fact-checking websites.
        The function must be named `preprocess_factcheck(html_content)` and return ONLY the cleaned HTML as a string.
        
        YOUR EXACT MISSION:
        Reduce the HTML size by targeting ONLY specific noisy widgets: "Related Articles", "Read More", "Latest News",
        "Trending", sidebars, cookie banners, donation prompts, and ads.
        DO NOT try to clean up the CSS grid or the structural wrappers of the page!
        

       STRICT BLACKLISTING RULES (NO EXCEPTIONS):
        1. TARGETED DECOMPOSE ONLY: 
            Analyze the provided HTML and identify the specific `class` or `id` names used for related articles,
            links, ads, sidebars and menus. 
            Remove them specifically using standard Python lists (e.g., `soup.find_all(['div', 'section', 'ul'],
            class_=['related-list', 'sidebar', 'read-more'])`).
        2. NO STRING OR CATCH-ALL LOOPS: 
            NEVER use `soup.find_all(string=...)` or `soup.find_all(text=...)`.
            Do NOT iterate over all generic tags to check their positions. 
            Searching by string returns Comment objects that break the pipeline.
        3. SAFE SEMANTIC TAGS:
            You may safely find and decompose global layout tags: `<nav>`, `<footer>`,
            `<aside>`, `<script>`, and `<style>`.
        4. CRITICAL VOID TAG RULE:
            NEVER globally decompose or loop over void/empty tags like `<input>`, `<img>`,
            `<meta>`, `<link>`, `<hr>`, or `<br>`. Only remove them if they happen to be inside a blacklisted layout container (like a footer or nav).
            Decomposing them globally breaks the 'html.parser' tree hierarchy.
        5. DEFENSIVE STRATEGY:
            If you are unsure whether a container belongs to the main content area or a related section,
            LEAVE IT INTACT. It is perfectly fine if some minor noise survives, but it is fatal if parts of the core page are lost.
        6. SAFEGUARDING GRIDS:
            NEVER blacklist generic CSS framework classes.
            DO NOT include classes like 'container', 'row', 'col-', 'wrapper', 'main', or 'page' in your decompose lists.
        7. SAFEGUARDING CONTENT:
            NEVER blacklist classes containing words like 'claim', 'body', 'conclusion', 'article', 'text', or 'cms-content'.
        8. ABSOLUTELY NO EMPTY-TAG LOOPS:
            Do NOT write loops that search for and remove empty tags (e.g., `if not element.contents:`).

        Return EXCLUSIVELY the executable Python code. Do not include markdown formatting like ```python, explanations, or usage examples.
        """
    )
    messages = [{"role": "system", "content": system_prompt}]
    messages.extend(load_few_shots())
    messages.append({
        "role": "user",
        "content": f"Write the complete BeautifulSoup4 preprocessor for this type of HTML page::\n\n{html}"})

    data = {
        "model": MODEL_ID,
        "messages": messages,
        "temperature": 0.0,
    }

    try:
        response = requests.post(API_URL, headers=headers, json=data)
        response.raise_for_status()

        preprocessor_code = response.json()["choices"][0]["message"]["content"]
        #Fallback cleaning
        preprocessor_code = preprocessor_code.replace("```python", "").replace("```", "").strip()

        os.makedirs(OUTPUT_DIR_PREPROCESSOR, exist_ok=True)
        path = os.path.join(OUTPUT_DIR_PREPROCESSOR, f"{portal_name.lower()}_preprocessor.py")

        with open(path, "w", encoding="utf-8") as f:
            f.write(preprocessor_code)
        logger.info(f"Successfully generated preprocessor for {portal_name.lower()}")
    except Exception as e:
        logger.error(f"Failed to generate preprocessor for {portal_name.lower()}: {e}")

