"""
Website scraping module for extracting content from SMB websites.
"""

import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from typing import Optional
import config


def is_valid_url(url: str) -> bool:
    """Validate URL format."""
    try:
        result = urlparse(url)
        return all([result.scheme in ('http', 'https'), result.netloc])
    except Exception:
        return False


def normalize_url(url: str) -> str:
    """Ensure URL has a scheme."""
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url
    return url.rstrip('/')


def fetch_page(url: str) -> Optional[str]:
    """Fetch a single page and return its HTML content."""
    try:
        headers = {'User-Agent': config.USER_AGENT}
        response = requests.get(
            url,
            headers=headers,
            timeout=config.REQUEST_TIMEOUT,
            allow_redirects=True
        )
        response.raise_for_status()
        return response.text
    except requests.RequestException as e:
        print(f"Error fetching {url}: {e}")
        return None


def extract_text_content(html: str) -> dict:
    """Extract relevant text content from HTML."""
    soup = BeautifulSoup(html, 'html.parser')

    # Remove script and style elements
    for element in soup(['script', 'style', 'nav', 'footer', 'header']):
        element.decompose()

    # Extract metadata
    title = soup.title.string if soup.title else ""

    meta_description = ""
    meta_tag = soup.find('meta', attrs={'name': 'description'})
    if meta_tag and meta_tag.get('content'):
        meta_description = meta_tag['content']

    # Extract main content
    main_content = soup.get_text(separator='\n', strip=True)

    # Limit content length to avoid token bloat
    if len(main_content) > 15000:
        main_content = main_content[:15000] + "..."

    return {
        'title': title,
        'meta_description': meta_description,
        'content': main_content
    }


def find_relevant_pages(base_url: str, html: str) -> list[str]:
    """Find links to About, Products, Contact, Careers pages."""
    soup = BeautifulSoup(html, 'html.parser')

    keywords = {
        'about': ['about', 'company', 'who-we-are', 'our-story'],
        'products': ['products', 'services', 'solutions', 'offerings', 'what-we-do'],
        'contact': ['contact', 'get-in-touch', 'reach-us'],
        'careers': ['careers', 'jobs', 'work-with-us', 'join-us', 'team'],
    }

    found_pages = {}

    for link in soup.find_all('a', href=True):
        href = link['href'].lower()
        link_text = link.get_text().lower()

        for page_type, kws in keywords.items():
            if page_type not in found_pages:
                for kw in kws:
                    if kw in href or kw in link_text:
                        full_url = urljoin(base_url, link['href'])
                        # Only include internal links
                        if urlparse(full_url).netloc == urlparse(base_url).netloc:
                            found_pages[page_type] = full_url
                            break

    return list(found_pages.values())


def scrape_website(url: str) -> dict:
    """
    Main function to scrape a website and gather all relevant content.

    Returns:
        dict with 'url', 'success', 'pages' (list of page contents), 'error' (if any)
    """
    url = normalize_url(url)

    if not is_valid_url(url):
        return {
            'url': url,
            'success': False,
            'pages': [],
            'error': 'Invalid URL format'
        }

    result = {
        'url': url,
        'success': False,
        'pages': [],
        'error': None
    }

    # Fetch homepage
    homepage_html = fetch_page(url)
    if not homepage_html:
        result['error'] = 'Failed to fetch homepage'
        return result

    homepage_content = extract_text_content(homepage_html)
    homepage_content['page_type'] = 'homepage'
    homepage_content['url'] = url
    result['pages'].append(homepage_content)

    # Find and fetch relevant subpages
    subpage_urls = find_relevant_pages(url, homepage_html)

    for subpage_url in subpage_urls[:4]:  # Limit to 4 subpages
        subpage_html = fetch_page(subpage_url)
        if subpage_html:
            subpage_content = extract_text_content(subpage_html)
            subpage_content['url'] = subpage_url
            # Determine page type from URL
            subpage_content['page_type'] = 'subpage'
            result['pages'].append(subpage_content)

    result['success'] = True
    return result


def get_combined_content(scraped_data: dict) -> str:
    """Combine all scraped pages into a single text for LLM processing."""
    if not scraped_data['success']:
        return ""

    sections = []
    for page in scraped_data['pages']:
        section = f"=== {page['page_type'].upper()}: {page['url']} ===\n"
        if page['title']:
            section += f"Title: {page['title']}\n"
        if page['meta_description']:
            section += f"Description: {page['meta_description']}\n"
        section += f"\nContent:\n{page['content']}\n"
        sections.append(section)

    return "\n\n".join(sections)
