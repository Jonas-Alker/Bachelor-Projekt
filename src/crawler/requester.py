import requests
import time
import random
import logging

from requests.adapters import HTTPAdapter
from urllib3 import Retry

#Getting Logger
logger = logging.getLogger(__name__)

session = requests.Session()
session.headers.update({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5',
    'DNT': '1',  # Do Not Track
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
})

retries = Retry(
    total=2,
    backoff_factor=1,
    status_forcelist=[500, 502, 503, 504],
    raise_on_status=False
)
session.mount('https://', HTTPAdapter(max_retries=retries))
session.mount('http://', HTTPAdapter(max_retries=retries))

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

        r =session.get(url, timeout=timeout)
        r.raise_for_status()
        return r.text
    except requests.exceptions.HTTPError as e:
        logger.error(f"HTTP Error ({url}): {e}")
        return None
    except requests.exceptions.RequestException as e:
        logger.error(f"Fetch Connection Error ({url}): {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected Error fetching ({url}): {e}")
        return None
