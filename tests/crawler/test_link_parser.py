from src.crawler.link_parser import extract_sublinks

BASE_URL = "https://example.com/blog/"
DOMAIN = "example.com"

def test_extract_valid_internal_links():
    """Tests if normal internal and relative links are extracted correctly."""
    html = """
        <html>
            <body>
                <a href="/about">About Us</a>
                <a href="https://example.com/contact">Contact</a>
                <a href="pricing">Pricing</a>
            </body>
        </html>
        """
    expected = {
        "https://example.com/about",
        "https://example.com/contact",
        "https://example.com/blog/pricing"}
    assert extract_sublinks(html, BASE_URL, DOMAIN) == expected

def test_ignore_external_domains():
    """Test if links to other domains are ignored."""
    html = """
    <html>
        <body>
            <a href="https://google.com">Google</a>
            <a href="https://sub.example.com/page">Subdomain</a>
            <a href="/valid-internal">Internal</a>
        </body>
    </html>
    """
    expected = {"https://example.com/valid-internal"}
    assert extract_sublinks(html, BASE_URL, DOMAIN) == expected

def test_strip_fragments_and_trailing_slashes():
    """Tests if URL fragments (#) and trailing slashes are removed."""
    html = """
    <html>
        <body>
            <a href="/home/">Home with Slash</a>
            <a href="/about#section1">About with Fragment</a>
        </body>
    </html>
    """
    expected = {
        "https://example.com/home",
        "https://example.com/about"
    }
    assert extract_sublinks(html, BASE_URL, DOMAIN) == expected

def test_ignore_excluded_extensions():
    """Test if media and document files (.jpg, .pdf, .png) are ignored."""
    html = """
    <html>
        <body>
            <a href="/document.pdf">PDF</a>
            <a href="/image.jpg">JPG</a>
            <a href="/graphic.png">PNG</a>
            <a href="/valid-page">Valid Page</a>
        </body>
    </html>
    """
    expected = {"https://example.com/valid-page"}
    assert extract_sublinks(html, BASE_URL, DOMAIN) == expected

def test_empty_html_or_no_links():
    """Test the behaviour with empty HTML or when there are no links."""
    html = "<html><body><p>Keine Links hier.</p></body></html>"
    assert extract_sublinks(html, BASE_URL, DOMAIN) == set()