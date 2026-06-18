from bs4 import BeautifulSoup

def preprocess_factcheck(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Remove global layout tags
    for tag in soup(['nav', 'header', 'footer', 'aside', 'script', 'style']):
        tag.decompose()
    
    # Remove specific layout containers by class/id
    layout_containers = soup.find_all(['div', 'section', 'ul', 'li', 'ol'],
        class_=['page-header', 'navbar', 'breadcrumbs', 'social-media', 'topics',
                'related-factchecks', 'jumbotron', 'donate', 'signup_cta',
                'inline-donate', 'cms-content', 'container', 'row', 'col-12',
                'col-md-6', 'col-lg-8', 'bg-brand-primary', 'bg-brand-neutral-grey',
                'animate-links', 'brand-legal', 'footer-links', 'social-links',
                'brand-logo', 'form-row', 'form-group', 'form-label-group'])
    
    for container in layout_containers:
        container.decompose()
    
    # Remove specific layout containers by id
    for id_name in ['ga-inline-donate', 'ga-newsletter-signup', 'ff-navbar']:
        element = soup.find(id=id_name)
        if element:
            element.decompose()
    
    # Remove meta tags and link tags from head
    head = soup.find('head')
    if head:
        for meta in head.find_all(['meta', 'link']):
            meta.decompose()
    
    # Remove specific button classes
    buttons = soup.find_all('button', class_=['navbar-toggler', 'btn-brand-accent-yellow',
                                           'btn-brand-accent-pink', 'btn-brand-neutral-black'])
    for button in buttons:
        button.decompose()
    
    # Remove specific div classes that might contain noise
    noise_divs = soup.find_all('div', class_=['mx-n2', 'mx-sm-0', 'no-gutters',
                                           'card-body-text', 'card-claim-body',
                                           'card-conclusion-body', 'highlight-js'])
    for div in noise_divs:
        div.decompose()
    
    # Remove empty or near-empty elements that might remain
    for element in soup.find_all():
        if not element.contents and not element.name in ['img', 'svg']:
            element.decompose()
    
    return str(soup)