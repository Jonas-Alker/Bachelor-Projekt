import json
from pathlib import Path
from dotenv import load_dotenv
import requests
import os

load_dotenv()

# Configuration
API_KEY = os.getenv("KICONNECT_API_KEY")
API_URL = "https://chat.kiconnect.nrw/api/v1/chat/completions"
MODEL_ID = "MistralSmall_4"

if not API_KEY:
    print("Error: API_KEY is empty!")
def load_few_shots():
    path = Path(__file__).resolve().parent.parent.parent / "data" / "parser" / "few_shot_examples.json"
    with open(path, "r", encoding="utf-8") as f:
        examples = json.load(f)
    few_shots_message = []
    for ex in examples:
        few_shots_message.append({
            "role": "user",
            "content": f"Analysiere das HTML-Dokument und extrahiere die Daten gemäß dem definierten Schema:\n{ex['input_html']}"})
        few_shots_message.append({"role": "assistant", "content": json.dumps(ex["expected_output"])})
    return few_shots_message


def extract_claim(html_content):
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {API_KEY}"
    }
    system_prompt =(
        """Analysiere das folgende HTML und extrahiere alle Claims. Die Daten dürfen nur als JSON-Array 
        zurück geben. 
        Jedes Objekt im Array muss folgende Keys enthalten:
        `claim`, `artikel_datum`, `sprache`, `claim_datum`, `title`, `rating`.
        Wenn ein Feld nicht exestiert, setzte den Wert auf null.
        Bei dem raiting übernimm genau den Wortlaut von der Seite, auch wenn dieser nicht True oder False ist.
        Es können auch mehrere Claims pro hmtl vorhanden sein, in dem Fall füge ein weiteres Objekt dem Array hinzu.
        Gib AUSSCHLIESSLICH den das JSON-Array zurück, ohne Erklärungen oder Erläuterungen.
        """
    )
    messages = [{"role": "system", "content": system_prompt}]
    messages.extend(load_few_shots())
    messages.append({
        "role": "user",
        "content": f"Analysiere das HTML-Dokument und extrahiere die Daten gemäß dem definierten Schema:\n\n{html_content}"})
    data = {
        "model": MODEL_ID,
        "messages": messages,
        "temperature": 0.0,
        "response_format": {
        "type": "json_schema" #specify the schema in more detail
    }
    }

    try:
        reply = requests.post(API_URL, headers=headers, json=data)
        reply.raise_for_status()

        reply_json = reply.json()["choices"][0]["message"]["content"]
        reply_json = reply_json.replace("```json", "").replace("```", "").strip()

        print("")###just for debugging, will be removed after finishing script
    except Exception as e:
        print(f"Error with the AI request: {e}")


#For testing purposes only during programming
if __name__ == "__main__":
    test_url = "https://fullfact.org/politics/city-council-meeting-video-miscaptioned/"

    response = requests.get(test_url)
    r = response.text
    response.raise_for_status()

    extract_claim(r)