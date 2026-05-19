from bs4 import BeautifulSoup
import re

def clean_html_noise(html):
    soup = BeautifulSoup(html, "html.preprocessor")

    noise_selection = [
        "nav", "footer", "header", "script", "style",
        ".cookie-banner", ".sidebar", ".social-share"
    ]
    for selector in noise_selection:
        for element in soup.find_all(selector):
            element.decompose()

    return str(soup)

def clean_text_whitespace(html):
    if not html:
        return ""
    clean = re.sub(r"\s+", " ", str(html))
    return clean
