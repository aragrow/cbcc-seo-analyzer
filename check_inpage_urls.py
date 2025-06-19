import requests
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup

def check_inpage_urls(page_url):
    result = []
    debug = f"\nChecking in-page URLs for: {page_url}\n"
    print(f"Checking in-page URLs for: {page_url}")
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(page_url, headers=headers, timeout=10)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, 'html.parser')

        # Collect all tag types with URLs
        tags_attrs = {
            'a': 'href',
            'img': 'src',
            'script': 'src',
            'link': 'href',
            'iframe': 'src',
            'source': 'src',
        }

        print(tags_attrs)

        seen = set()
        for tag, attr in tags_attrs.items():
            for element in soup.find_all(tag):
                raw_url = element.get(attr)
                print(f"Found {tag} URL: {raw_url}")
                if not raw_url:
                    continue

                # Build absolute URL
                abs_url = urljoin(page_url, raw_url)

                # Avoid duplicates
                if abs_url in seen:
                    continue
                seen.add(abs_url)

                # Check URL status
                try:

                    r = requests.head(abs_url, allow_redirects=True, timeout=5)
                    status = r.status_code
                    debug += f"\nChecking URL: {abs_url}: Status Code: {status}"
                    print(f"Checking URL: {abs_url}: Status Code: {status}  ")

                except Exception as e:
                    status = f"ERROR: {str(e)}"

                result.append({
                    "in_page_url": abs_url,
                    "status": status,
                    "tag": tag
                })

        return {
            "page_url": page_url,
            "in_page_urls": result,
            "debug": debug
        }

    except Exception as ex:
        return {
            "page_url": page_url,
            "error": str(ex),
            "in_page_urls": [],
            "debug": debug 
        }
