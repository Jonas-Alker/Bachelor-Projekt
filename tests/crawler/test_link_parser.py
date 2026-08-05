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

def test_ignore_mailto_and_javascript():
    """Tests if mailto: and javascript: links are correctly ignored."""
    html = """
    <html>
        <body>
            <a href="mailto:test@example.com">Mail</a>
            <a href="javascript:void(0)">JS</a>
            <a href="javascript:alert('hello')">JS Alert</a>
            <a href="/valid-page">Valid</a>
        </body>
    </html>
    """
    expected = {"https://example.com/valid-page"}
    assert extract_sublinks(html, BASE_URL, DOMAIN) == expected

def test_keep_query_parameters():
    """Tests if valid query parameters are preserved in the URL."""
    html = """
    <html>
        <body>
            <a href="/search?q=faktencheck&page=1">Search</a>
            <a href="https://example.com/article?id=42#comments">Article with Query and Fragment</a>
        </body>
    </html>
    """
    expected = {
        "https://example.com/search?q=faktencheck&page=1",
        "https://example.com/article?id=42"
    }
    assert extract_sublinks(html, BASE_URL, DOMAIN) == expected

def test_ignore_uppercase_extensions():
    """Tests if uppercase file extensions like .JPG or .PDF are ignored."""
    html = """
    <html>
        <body>
            <a href="/document.PDF">PDF Uppercase</a>
            <a href="/image.JPG">JPG Uppercase</a>
            <a href="/valid-page">Valid Page</a>
        </body>
    </html>
    """
    expected = {"https://example.com/valid-page"}
    assert extract_sublinks(html, BASE_URL, DOMAIN) == expected