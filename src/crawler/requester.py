import requests
import time
import random

def fetch_page(url, timeout= 10):
    """Fetches the HTML content of a given URL.
    To avoid overloading the target server and mimic human-like behavior,
    the function introduces a short, randomized delay before making the request.

    :param url: The web address of the page to fetch.
    :param timeout: The maximum number of seconds to wait for the server
            to send data before giving up. Defaults to 10.
    :return: The raw HTML content of the page as a string if successful;
        None if an HTTP error or connection issue occurs.
    """
    try:
        time.sleep(random.uniform(0.1, 0.3))

        r = requests.get(url, timeout=timeout)
        r.raise_for_status()
        return r.text

    except Exception as e:
        print(f"Fetch Error({url}): {e}")
        return None
