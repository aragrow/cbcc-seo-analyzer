import requests
from bs4 import BeautifulSoup
from xml.etree import ElementTree as ET
from urllib.parse import urlparse
import os
import gspread
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

from canonical_tag_report import generate_canonical_tag_report

MAIN_SITEMAP = os.getenv("MAIN_SITEMAP")
if not MAIN_SITEMAP:
    raise ValueError("MAIN_SITEMAP environment variable is not set. Please set it in your .env file.")

def preprocess_xml(xml_content):
    print("Fix common XML issues: newlines in tags and unescaped ampersands")
    xml_content = xml_content.replace('\n', '').replace('&', '&amp;')
    return xml_content

def parse_sitemap_index(xml_content):
    print("Parse sitemap index to extract sitemap URLs")
    #xml_content = preprocess_xml(xml_content)
    root = ET.fromstring(xml_content)
    print(f"Root: {root}")

    """root.findall('.//loc'):
        findall(): This method searches through the XML elements contained within root.
        './/loc': This is a simple XPath query.
        . means "starting from the current element" (which is root).
        // means "find all matching elements at any depth" (i.e., search the entire tree below root).
        loc means "find elements with the tag name <loc>".
        So, this part finds every single <loc> element anywhere inside the <sitemapindex> and returns them as a list of Element objects."""
    result = []
    # Use {*}, a wildcard for any namespace.
    # We also keep the 'if loc.text' check to avoid errors on empty tags.
    query = './/{*}loc'
    
    result = [loc.text.strip() for loc in root.findall(query) if loc.text]
                
    #print(f"Result: {result}")
    return result

def categorize_sitemap(sitemap_url):
    print("Categorize sitemap based on URL patterns")
    parsed = urlparse(sitemap_url)
    if 'product-sitemap' in parsed.path: return 'products'
    if 'pages' in parsed.query: return 'pages'
    if 'categories' in parsed.query: return 'categories'
    if 'brands' in parsed.query: return 'brands'
    if 'news' in parsed.query: return 'news'
    return 'other'

def parse_sitemap(sitemap_url):
    print("Parse individual sitemap to extract page URLs")
    try:
        response = requests.get(sitemap_url, timeout=10)
        response.raise_for_status()
        root = ET.fromstring(response.content)
        query = './/{*}loc'
        result = [loc.text.strip() for loc in root.findall(query) if loc.text]
        return result
    except Exception as e:
        print(f"Error parsing {sitemap_url}: {e}")
        return []

def categorize_urls(sitemap_urls):
    print("Categorize and parse all sitemaps URLs")
    categorized_urls = {
        'pages': [],
        'products': [],
        'categories': [],
        'brands': [],
        'news': [],
        'other': []
    }

    for sitemap_url in sitemap_urls:
        print(f"Processing: {sitemap_url}")
        category = categorize_sitemap(sitemap_url)
        page_urls = parse_sitemap(sitemap_url)
        print(f"page_urls: {page_urls}")
        categorized_urls[category].extend(page_urls)

    print(f"categorize_url: {len(categorized_urls)}")
    return categorized_urls

def get_canonical_tags(categorized_urls):
    print("Loop thru categorized url to get canonical tag")

    canonical_data = {category: [] for category in categorized_urls}

    print(f"Canonical Data: {canonical_data}")

    for category, urls in categorized_urls.items():
        if category != 'products': continue
        print(f"Processing Category: {category}")
        i = 0
        for url in urls:
            result = get_canonical(url)
            print(result)
            canonical_data[category].append({"url": url, "url_status_code": result['status_code'], "canonical_url": result['href']})
            i = i + 1
            if i>10: break
    print(f"Canonical Data: \n {canonical_data}")
    return canonical_data

def get_canonical(url):
    print(f"Retrieve canonical link from a webpage: {url}")
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        status_code = response.status_code
        canonical = soup.find('link', rel='canonical')
        return {"href": canonical['href'] if canonical else None, "status_code": status_code if status_code else None}
    except Exception as e:
        print(f"Error fetching {url}: {e}")
        return None

def get_canonical_info(categorized_urls_and_canonicals_tags):

    print("Extract unique canonical URLs from categorized data")
    unique_canonicals = set()
    for category, items in categorized_urls_and_canonicals_tags.items():
        for item in items:
            canonical_url = item.get("canonical_url")
            if canonical_url:
                unique_canonicals.add(canonical_url)
    print(f"Unique canonical URLs: {unique_canonicals}")

    for canonical_url in unique_canonicals:
        found = False
        for category, items in categorized_urls_and_canonicals_tags.items():
            print(f'Processing Canonical url: {items}')
            for item in items:
                if item.get("url") == canonical_url:
                    canonical_url.append({"canonical_url": canonical_url, "status": item.get("url_status_code")})
                    found = True
                    break
            if found:
                break
            # If not found, fetch status directly
            try:
                headers = {"User-Agent": "Mozilla/5.0"}
                response = requests.get(canonical_url, headers=headers, timeout=10)
                item.append({"status": response.status_code})
            except Exception as e:
                item.append({"status": None})

    print(f"Unique canonical URLs and status: {unique_canonicals}")

    return list(unique_canonicals)

def check_canonical_tags():
    print("Check canonical tags")
  
    print(f"Main SiteMap URLS: {MAIN_SITEMAP}")
    response = requests.get(MAIN_SITEMAP, timeout=10)
    sitemap_index_xml = response.text
    print(sitemap_index_xml)

    # Process sitemap index
    sitemap_urls = parse_sitemap_index(sitemap_index_xml)
    print(f"SiteMap URLS: {sitemap_urls}")

    categorized_urls = categorize_urls(sitemap_urls)
   
    categorized_urls_and_canonicals_tags = get_canonical_tags(categorized_urls)
    
    canonical_tags = get_canonical_info(categorized_urls_and_canonicals_tags)

    print(categorized_urls_and_canonicals_tags)

    report = generate_canonical_tag_report(categorized_urls_and_canonicals_tags, canonical_tags, 'webeyecare')

    if report:
        print('Report Completed')
    else:
        print('Unable to create report')
