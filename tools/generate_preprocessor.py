import requests
import json
import os
from dotenv import load_dotenv
from pathlib import Path

load_dotenv()

# Configuration
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
        The preprocessor should take the full HTML and remove all sections that do not belong to the main article.
        Remove all overhead such as navigation menus, footers, sidebars, related article links, and cookie banners.
        CRITICAL INSTRUCTIONS FOR BEAUTIFULSOUP:
        1. DO NOT extract elements to rebuild or construct a new HTML tree.
        2. DO NOT create new tags (like a new wrapper div).
        3. You must ONLY use the `.decompose()` or `.extract()` methods on unwanted elements (like navigation menus, footers, sidebars, cookie banners, related article links).
        4. Leave the rest of the original HTML tree completely intact.
        5. DO NOT use regular expressions (`re.compile`) for matching class names. If you need to match multiple classes, pass a standard Python list of strings (e.g., `class_=['class1', 'class2']`).
        CRITICAL PRESERVATION RULE: You MUST ensure that the HTML containers holding the following information are NEVER removed:
        1. Headline
        2. Main article text (body)
        3. The claim being evaluated
        4. Author of the article
        5. Language of the article
        6. Author of the claim
        7. Publication date of the article
        8. The date the original claim was made/quoted.
        9. The original fact-check rating
        
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

    except Exception as e:
        print(f"Error with the AI request: {e}")
