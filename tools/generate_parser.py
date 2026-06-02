import requests
import json
import os
from dotenv import load_dotenv
from pathlib import Path

load_dotenv()

# Konfiguration
API_KEY = os.getenv("KICONNECT_API_KEY")
API_URL = "https://chat.kiconnect.nrw/api/v1/chat/completions"
MODEL_ID = "MistralSmall_4"

if not API_KEY:
    print("Error: API_KEY is empty!")

#Target
OUTPUT_DIR_PARSER= Path(__file__).resolve().parent.parent / "src" / "parser" / "generated"

def load_html(url):
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.text

    except Exception as e:
        print(f"Fehler beim Laden der URL: {e}")
        return None

def load_few_shots():

    path = Path(__file__).resolve().parent.parent / "data" / "parser" / "few_shot_examples.json"
    with open(path, "r", encoding="utf-8") as f:
        examples = json.load(f)
    few_shots_message = []
    for ex in examples:
        few_shots_message.append({
            "role": "user",
            "content": f"Schreibe jetzt den kompletten Parser für Seiten dieses HTML Typs:\n{ex['input_html']}"})
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
        """Du bist ein Senior Data Engineer. Deine Aufgabe ist es, BeautifulSoup4-Parserfür Faktencheck-Webseiten zu 
        schreiben. Die Funktion muss `parse_faktencheck(html_content)` heißen und nur die Daten nur als JSON-Array 
        zurück geben. 
        Jedes Objekt im Array muss folgende Keys enthalten:
        `claim`, `artikel_datum`, `sprache`, `claim_datum`, `title`, `rating`.
        Wenn ein Feld nicht exestiert, setzte den Wert auf null.
        Es können auch mehrere Claims pro hmtl vorhanden sein, in dem Fall füge ein weiteres Objekt dem Array hinzu.
        Gib AUSSCHLIESSLICH den Python-Code zurück, ohne Erklärungen oder Markdown-Formatierung.
        """
    )
    messages = [{"role": "system", "content": system_prompt}]
    messages.extend(load_few_shots())
    messages.append({
        "role": "user",
        "content": f"Schreibe jetzt den kompletten Parser für Seiten dieses HTML Typs:\n\n{html}"})

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

    except Exception as e:
        print(f"Error with the AI request: {e}")

#For testing purposes only during programming
if __name__ == "__main__":
    test_url = "https://fullfact.org/health/melanoma-is-not-the-most-common-cancer-globally/"
    portal_name = "Fullfact"

    generate_parser(test_url, portal_name)