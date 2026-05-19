from bs4 import BeautifulSoup

###
#WARNING: AI generated (Gemini)
###
def prepare_for_llm(html_content):
    """Staucht PolitiFact-HTML für das LLM zusammen."""

    # 1. Groben Standard-Müll über den Base-Processor filtern
    soup = BeautifulSoup(html_content, "html.parser")

    # 2. PolitiFact-spezifischen Extra-Müll löschen (NEU)
    # Wir suchen gezielt nach den Klassen für den Newsletter-PopUp und andere Artikel
    politifact_noise = [
        soup.find("section", class_="o-disruptor"),  # Der große Newsletter-Kasten
        soup.find("div", class_="m-carousel"),  # Die Vorschau anderer Faktenchecks unten
        soup.find("section", class_="m-billboard")  # Eventuelle Werbebanner-Plätze
    ]

    for element in politifact_noise:
        if element:  # Wichtig, falls ein Element auf einer Unterseite mal fehlt
            element.decompose()

    # 3. Inhalt auf den Haupt-Content isolieren
    main_content = soup.find("main", class_="global-content")
    if main_content:
        soup = main_content

    # 4. Attribute säubern (macht die Tags nackt)
    for tag in soup.find_all(True):
        allowed_attrs = ["href", "alt"]
        attrs = dict(tag.attrs)
        for attr in attrs:
            if attr not in allowed_attrs:
                del tag[attr]

    # 5. Finale Text-Kompression über den Base-Processor
    compressed_html = str(soup)
    return compressed_html