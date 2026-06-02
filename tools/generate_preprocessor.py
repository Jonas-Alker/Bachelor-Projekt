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
OUTPUT_DIR_PREPROCESSOR= Path(__file__).resolve().parent.parent / "src" / "preprocessor" / "generated"

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
            "content": f"Schreibe jetzt den kompletten Preprosesor für Seiten dieses HTML Typs:\n{ex['input_html']}"})
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
        """Du bist ein Senior Data Engineer. Deine Aufgabe ist es, BeautifulSoup4-Preprossesor für Faktencheck-Webseiten zu 
        schreiben. Die Funktion muss `preprocess_faktencheck(html_content)` heißen und nur die die gereinigt HTML zurückgeben. 
        Der Preprocessor soll eine vollständige HTML bekommen und von dieser alle Abschnitte Entfernen die nicht zum 
        Hauptartikel gehören oder Anmerkungen/Anotationen zu diesem sind. 
        Jeglicher Overhead, wie Menüs, verwandte Artikel und ähnliches sollen entfernt werden.  
        Gib AUSSCHLIESSLICH den Python-Code zurück, ohne Erklärungen oder Markdown-Formatierung.
        """
    )
    messages = [{"role": "system", "content": system_prompt}]
    messages.extend(load_few_shots())
    messages.append({
        "role": "user",
        "content": f"Schreibe jetzt den kompletten Preprosesor für Seiten dieses HTML Typs:\n\n{html}"})

    data = {
        "model": MODEL_ID,
        "messages": messages,
        "temperature": 0.0,
    }

    try:
        response = requests.post(API_URL, headers=headers, json=data)
        response.raise_for_status()

        preprocessor_code = response.json()["choices"][0]["message"]["content"]
        preprocessor_code = preprocessor_code.replace("```python", "").replace("```", "").strip()

        os.makedirs(OUTPUT_DIR_PREPROCESSOR, exist_ok=True)
        path = os.path.join(OUTPUT_DIR_PREPROCESSOR, f"{portal_name.lower()}_preprocessor.py")

        with open(path, "w", encoding="utf-8") as f:
            f.write(preprocessor_code)

    except Exception as e:
        print(f"Error with the AI request: {e}")

#For testing purposes only during programming
if __name__ == "__main__":
    test_url = "https://www.politifact.com/factchecks/2026/may/14/kathy-castor/kid-care-florida-desantis-health-insurance/"
    portal_name = "Politifact"

    generate_preprocessor(test_url, portal_name)
