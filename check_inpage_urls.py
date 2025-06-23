import requests
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
from datetime import datetime, timezone
from urllib.parse import urlparse
from check_toxic_links import (
    check_toxic_link_gsb,
    strip_www
)

def check_inpage_urls(page_url):
    results = []
    debug = ''
    print ('### Checking in-page URLs for:', page_url)

    #debug = f"\nChecking in-page URLs for: {page_url}\n"
    #print(f"Checking in-page URLs for: {page_url}")
    try:

        page_parts = urlparse(page_url)
        page_domain = strip_www(page_parts.netloc)

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
                if x > 100:
                    print(f"Reached limit of 100 URLs for tag: {tag}")
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
                    print(f"-- Checking URL: {abs_url} ")
                    r = requests.head(abs_url, allow_redirects=True, timeout=5)
                    if r.status_code != 200:
                        results.append({
                            "page_url": page_url,
                            "audit_date": datetime.now(timezone.utc).strftime("%m/%d/%Y"),
                            "in_page_url": abs_url,
                            "status_code": r.status_code,
                            "tag": tag,
                            "notes": ''
                        })
                except Exception as e:
                    print(f"Error Checking Link Status: {e}")
                    return False

                try:
                    
                    abs_parts = urlparse(abs_url)
                    abs_domain = strip_www(abs_parts.netloc)

                    if (abs_domain != page_domain): 
                        print('External Link')
                        is_toxic, threat_info = check_toxic_link_gsb(abs_url)      
                        if is_toxic:
                            results.append({
                                "page_url": page_url,
                                "audit_date": datetime.now(timezone.utc).strftime("%m/%d/%Y"),
                                "in_page_url": abs_url,
                                "status_code": "Toxic",
                                "tag": tag,
                                "notes": {threat_info}
                            })

                except Exception as e:
                    print(f"Error Checking Link Toxicity: {e}")
                    return False

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
