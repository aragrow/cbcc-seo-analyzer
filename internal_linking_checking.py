import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import time

# Define a reasonable user agent
headers = {
    'User-Agent': 'Mozilla/5.0 (compatible; SimpleInternalLinkChecker/1.0; +https://yourwebsite.com/contact)' # Replace with your info if deploying
}

# Define common generic anchor texts (case-insensitive, stripped of whitespace)
GENERIC_ANCHORS = {'click here', 'read more', 'learn more', 'find out more', 'more info', 'here'}

def is_internal_link(base_url, link_url):
    """Checks if a given URL is internal to the base URL's domain."""
    if not link_url:
        return False

    # Use urljoin to handle relative URLs
    absolute_link_url = urljoin(base_url, link_url)

    try:
        base_parts = urlparse(base_url)
        link_parts = urlparse(absolute_link_url)

        # Compare netloc (domain) - case-insensitive comparison after stripping www.
        base_domain = base_parts.netloc.lower().replace('www.', '')
        link_domain = link_parts.netloc.lower().replace('www.', '')

        # Check if domain matches and scheme is http/https, and path is not empty (avoids just comparing domains without paths)
        return base_domain == link_domain and link_parts.scheme in ['http', 'https'] and bool(link_parts.path or link_parts.query or link_parts.fragment)

    except ValueError:
        # Handle potential issues with URL parsing
        return False

def analyze_page_internal_link(url):
    """Analyzes a single webpage for internal linking characteristics."""
    print(f"Analyzing: {url}")
    
    try:
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status() # Raise an HTTPError for bad responses (4xx or 5xx)
        html_content = response.text
    except requests.exceptions.RequestException as e:
        print(f"\nError fetching page {url}: {e}")
        return {"result": "FAIL", "reason": f"Could not fetch page: {e}", "details": {}}

    soup = BeautifulSoup(html_content, 'html.parser')

    internal_links_found = []
    broken_internal_links = []
    generic_anchor_count = 0
    total_links_checked = 0

    # Find all <a> tags with href attributes
    for a_tag in soup.find_all('a', href=True):
        href = a_tag.get('href')
        
        # Resolve the URL to handle relative paths
        full_url = urljoin(url, href)

        if is_internal_link(url, full_url):
            internal_links_found.append(full_url)
            total_links_checked += 1

            # Check anchor text
            anchor_text = a_tag.get_text().strip()
            if anchor_text.lower() in GENERIC_ANCHORS:
                 generic_anchor_count += 1

            # Check the status of the internal link
            # Add a small delay between requests to be polite
            # time.sleep(0.1) # Uncomment this line if you are checking many links on many pages

    # --- Determine Pass/Fail ---

    result = "PASS"
    reason = "Internal linking checks passed for this page."
    details = {
        "total_internal_links_found": len(internal_links_found),
        "generic_anchor_count": generic_anchor_count,
        "recommendations": []
    }

    if len(internal_links_found) == 0:
        result = "FAIL"
        reason = "No outgoing internal links found on this page."
        details["recommendations"].append("Add relevant internal links to other pages on your site.")

    # --- Add Recommendations (not affecting Pass/Fail) ---
    if len(internal_links_found) > 0 and generic_anchor_count == len(internal_links_found):
         details["recommendations"].append("All internal links use generic anchor text. Use more descriptive anchor text relevant to the destination page.")
    elif generic_anchor_count > 0 and generic_anchor_count/len(internal_links_found) > 0.5: # Threshold, adjustable
         details["recommendations"].append(f"Many internal links ({generic_anchor_count}/{len(internal_links_found)}) use generic anchor text. Use more descriptive anchor text relevant to the destination page where possible.")


    print("\n--- Analysis Results ---")
    print(f"Result: {result}")
    print(f"Reason: {reason}")
    print(f"\nDetails:")
    print(f"  Total outgoing internal links found: {details['total_internal_links_found']}")

    print(f"  Internal links using generic anchor text: {details['generic_anchor_count']}")

    if details['recommendations']:
        print("\nRecommendations:")
        for rec in details['recommendations']:
            print(f"  - {rec}")
    else:
        print("\nRecommendations: None.")


    print("------------------------")

    return {"result": result, "reason": reason, "details": details}

def analyze_page_internal_links(worksheet,urls_to_analyze):
    results = []
    base_url = ""  # Replace with your base URL if needed
    for item in urls_to_analyze:
        target_url = item['url']
        try:
            if base_url == "":
                # Extract base URL from the first URL in the list
                base_url = target_url
                if base_url.startswith("http://"):
                    base_url = base_url.replace("http://", "https://")
                elif not base_url.startswith("https://"):
                    base_url = "https://" + base_url

                url = base_url
            else:
                url = base_url + '/' + target_url

            result = analyze_page_internal_link(url)

        except Exception as e:
                results.append({"result": "Error", "reason": str(e), "details": url})           

        results.append(result)
    
    print(results)