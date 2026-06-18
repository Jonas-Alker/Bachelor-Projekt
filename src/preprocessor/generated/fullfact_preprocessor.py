from bs4 import BeautifulSoup

def preprocess_factcheck(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Remove all script tags except those containing critical metadata
    for script in soup.find_all('script'):
        if not script.find(string=lambda text: 'Article' in str(text) or 'ClaimReview' in str(text)):
            script.decompose()
    
    # Remove header and navigation
    header = soup.find('header', class_='page-header')
    if header:
        header.decompose()
    
    # Remove footer
    footer = soup.find('footer', class_='footer')
    if footer:
        footer.decompose()
    
    # Remove Google Tag Manager scripts and noscript iframes
    gtm_script = soup.find('script', string=lambda text: 'Google Tag Manager' in str(text))
    if gtm_script:
        gtm_script.decompose()
    
    gtm_noscript = soup.find('noscript', string=lambda text: 'Google Tag Manager' in str(text))
    if gtm_noscript:
        gtm_noscript.decompose()
    
    # Remove cookie consent banners if present
    cookie_banner = soup.find(class_=['cookie-banner', 'cookie-consent', 'gdpr-consent'])
    if cookie_banner:
        cookie_banner.decompose()
    
    # Remove newsletter signup forms outside main content
    newsletter_forms = soup.find_all('div', class_=['inline-donate', 'jumbotron', 'signup_cta'])
    for form in newsletter_forms:
        form.decompose()
    
    # Remove social media sharing sections outside main content
    social_sections = soup.find_all('section', class_='social-media')
    for section in social_sections:
        section.decompose()
    
    # Remove related articles sections
    related_sections = soup.find_all('section', class_=['related-factchecks', 'topics'])
    for section in related_sections:
        section.decompose()
    
    # Remove donate sections outside main content
    donate_sections = soup.find_all('section', class_=['donate', 'jumbotron', 'bg-brand-accent-yellow'])
    for section in donate_sections:
        section.decompose()
    
    # Remove breadcrumbs if they exist (but keep the main article structure)
    breadcrumbs = soup.find('nav', class_='breadcrumbs')
    if breadcrumbs:
        breadcrumbs.decompose()
    
    # Remove any remaining navigation elements
    nav_elements = soup.find_all('nav', class_=['navbar', 'footer-links'])
    for nav in nav_elements:
        nav.decompose()
    
    # Remove any remaining form elements not part of the main content
    forms = soup.find_all('form', class_=['ga-signup-form'])
    for form in forms:
        form.decompose()
    
    # Remove any remaining script tags that might be tracking or interactive
    for script in soup.find_all('script'):
        if script.get('src') or 'gtm' in str(script).lower() or 'facebook' in str(script).lower() or 'twitter' in str(script).lower():
            script.decompose()
    
    # Remove any empty containers that might remain
    empty_containers = soup.find_all(['div', 'section', 'aside'], class_=lambda x: x and ('container' in x or 'row' in x or 'col' in x) and not x.strip())
    for container in empty_containers:
        container.decompose()
    
    return str(soup)