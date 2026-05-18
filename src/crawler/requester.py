import requests
import time
import random

def fetch_page(url, timeout= 10):
    try:
        time.sleep(random.uniform(0.1, 0.3))

        r = requests.get(url, timeout=timeout)
        r.raise_for_status()
        return r.text

    except Exception as e:
        print(f"Fetch Error({url}): {e}")
        return None
