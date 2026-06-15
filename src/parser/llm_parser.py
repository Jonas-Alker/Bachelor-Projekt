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
            "content": f"Analyze the HTML document and extract the data in accordance with the defined schema:\n{ex['input_html']}"})
        few_shots_message.append({"role": "assistant", "content": json.dumps(ex["expected_output"])})
    return few_shots_message


def parse_factcheck(html_content):
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {API_KEY}"
    }
    system_prompt =(
        """Analyze the following HTML and extract all relevant fact-checking data.
        The data must be returned ONLY as a JSON array of objects.
        Each object must contain exactly the following keys:
        'headline', 'body' (the main text of the article), 'claim', 'author_factcheck', 'published_at', 'language',
        'author_claim', 'stated_at' (when the claim was made) and 'original_rating' (the exact wording from the page).
        CRITICAL DATE DEFINITIONS:
        - 'published_at': The date when this specific fact-checking article was published or updated by the fact-checker. 
        - 'stated_at': The date when the original claim was made, posted, or spoken by the person or entity being checked. 
        This is usually an older date than published_at.
        CRITICAL AUTHOR DEFINITIONS:
        - 'author_factcheck': The author of the fact-checking article, sometime called fact-checker.
        - 'author_claim': The author of the claim, usually a public figure.
        If information for a specific field does not exist, set the value to null. 
        All dates must be strictly formatted as 'DD.MM.YYYY' (Day. Month. Year).
        There may be multiple claims per HTML document, in that case, add another object to the array.
        Return ONLY the valid JSON array, without any explanations, markdown blocks, or comments.
        """
    )
    messages = [{"role": "system", "content": system_prompt}]
    messages.extend(load_few_shots())
    messages.append({
        "role": "user",
        "content": f"Analyse the HTML document and extract the data in accordance with the defined schema:\n\n{html_content}"})

    #Detailed JSON Schema
    json_schema = {
        "name": "fact_check",
        "schema": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "headline": {"type": ["string","null"]},
                    "body": {"type": ["string","null"]},
                    "claim": {"type": ["string","null"]},
                    "author_factcheck": {"type": ["string","null"]},
                    "published_at": {"type": ["string","null"],
                                     "description": "Date formatted strictly as DD:MM:YYYY"},
                    "language": {"type": ["string","null"]},
                    "author_claim": {"type": ["string","null"]},
                    "stated_at": {"type": ["string","null"],
                                  "description": "Date formatted strictly as DD:MM:YYYY"},
                    "original_rating": {"type": ["string","null"]}
                },
                "required": ["headline", "body", "claim", "author_factcheck", "published_at", "language",
                             "author_claim", "stated_at", "original_rating"],
                "additionalProperties": False
            }
        },
        "strict": True
    }

    data = {
        "model": MODEL_ID,
        "messages": messages,
        "temperature": 0.0,
        "response_format": {
            "type": "json_schema",
            "json_schema": json_schema
        }
    }

    try:
        reply = requests.post(API_URL, headers=headers, json=data)
        reply.raise_for_status()

        reply_json = reply.json()["choices"][0]["message"]["content"]
        reply_json = reply_json.replace("```json", "").replace("```", "").strip()
        return reply_json
    except Exception as e:
        print(f"Error with the AI request: {e}")


#For testing purposes only during programming
if __name__ == "__main__":
    test_url = "https://www.politifact.com/factchecks/2026/jun/10/graham-platner/Susan-Collins-Trump-vote-Maine-senate-election/"

    response = requests.get(test_url)
    r = response.text
    response.raise_for_status()

    parse_factcheck(r)