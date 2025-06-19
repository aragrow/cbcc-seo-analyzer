import requests
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
from datetime import datetime, timezone



def check_inpage_urls(page_url):
    results = []
    debug = ''
    print ('### Checking in-page URLs for:', page_url)

    #debug = f"\nChecking in-page URLs for: {page_url}\n"
    #print(f"Checking in-page URLs for: {page_url}")
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

        #print(tags_attrs)

        seen = set()
      
        for tag, attr in tags_attrs.items():
            x = 0
            for element in soup.find_all(tag):
                x += 1
                if x > 5:
                    print(f"Reached limit of 5 URLs for tag: {tag}")
                    break
              
                raw_url = element.get(attr)
                #print(f"Found {tag} URL: {raw_url}")
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
                    status_code = r.status_code
                    #debug += f"\nChecking URL: {abs_url}: Status Code: {status}"
                    print(f"-- Checking URL: {abs_url}: Status Code: {status_code}  ")

                except Exception as e:
                    status = f"ERROR: {str(e)}"

                results.append({
                    "page_url": page_url,
                    "audit_date": datetime.now(timezone.utc).strftime("%m/%d/%Y"),
                    "in_page_url": abs_url,
                    "status_code": status_code,
                    "tag": tag
                })
            # End For   
        # End For
        return results

    except Exception as ex:
        return {
            "page_url": page_url,
            "error": str(ex),
            "in_page_urls": [],
            "debug": debug 
        }
