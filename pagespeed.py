import requests
from dotenv import load_dotenv
import os
import sys
import re

PAGE_SPEED_API_KEY = os.getenv("PAGE_SPEED_API_KEY")
if not PAGE_SPEED_API_KEY:
    raise ValueError("PAGE_SPEED_API_KEY environment variable is not set. Please set it in your .env file.")

PAGE_SPEED_API_ENDPOINT = os.getenv("PAGE_SPEED_API_ENDPOINT")
if not PAGE_SPEED_API_ENDPOINT:
    raise ValueError("PAGE_SPEED_API_ENDPOINT environment variable is not set. Please set it in your .env file.")


def analyze_both(url: str, completed: bool, row_no: int) -> dict:
    """
    Analyze a URL for both mobile and desktop strategies using Google PageSpeed Insights API.
    
    Args:
        url (str): The webpage URL to analyze.
        completed (bool): Whether the analysis is completed.
    
    Returns:
        dict: A dictionary with separate results for mobile and desktop.
    """

    print(f"PageSpeed analyzing: {url}")

    if completed:
        return {
            "url": url,
            "after_mobile": analyze_url(url, "mobile", row_no),
            "after_desktop": analyze_url(url, "desktop", row_no)
        }
    else:
        return {
            "url": url,
            "before_mobile": analyze_url(url, "mobile", row_no),
            "before_desktop": analyze_url(url, "desktop", row_no)
        }

def analyze_url(url: str, strategy: str, row_no: int) -> dict:
    """
    Helper function to query the PageSpeed API for one strategy.
    
    Args:
        url (str): The webpage URL.
        strategy (str): "mobile" or "desktop".
        api_key (str): Google API key.
    
    Returns:
        dict: A dictionary of Lighthouse category scores.
    """
    params = {
        "url": url,
        "strategy": strategy,
        "category": ["performance", "accessibility", "best-practices", "seo"]
    }

    print(f"PageSpeed analyzing: {strategy}")

    if PAGE_SPEED_API_KEY:
        params["key"] = PAGE_SPEED_API_KEY

    try:
        response = requests.get(PAGE_SPEED_API_ENDPOINT, params=params, timeout=60)
        response.raise_for_status()
        data = response.json()

        lighthouse = data.get("lighthouseResult", {})
        categories = lighthouse.get("categories", {})
        audits = data.get("lighthouseResult", {}).get("audits", {})
        # 🔍 Extract recommendations (opportunities)
        opportunities = [
            {
                "id": audit_id,
                "title": audit.get("title"),
                "description": audit.get("description"),
                "score": audit.get("score"),
                "displayValue": audit.get("displayValue"),
                "details": audit.get("details", {})
            }
            for audit_id, audit in audits.items()
            if audit.get("details", {}).get("type") == "opportunity"
        ]

        diagnostics = [
            {
                "id": audit_id,
                "title": audit.get("title"),
                "description": audit.get("description"),
                "score": audit.get("score"),
                "displayValue": audit.get("displayValue")
            }
            for audit_id, audit in audits.items()
            if audit.get("details", {}).get("type") == "diagnostic"
        ]

        result = {
            "strategy": strategy,
            "performance": int(categories.get("performance", {}).get("score", 0) * 100),
            "accessibility": int(categories.get("accessibility", {}).get("score", 0) * 100),
            "best_practices": int(categories.get("best-practices", {}).get("score", 0) * 100),
            "seo": int(categories.get("seo", {}).get("score", 0) * 100),
            # Audits - extract specific metrics          
            "first_contentful_paint": audits.get("first-contentful-paint", {}).get("displayValue"),
            "largest_contentful_paint": audits.get("largest-contentful-paint", {}).get("displayValue"),
            "total_blocking_time": audits.get("total-blocking-time", {}).get("displayValue"),
            "cumulative_layout_shift": audits.get("cumulative-layout-shift", {}).get("displayValue"),
            "speed_index": audits.get("speed-index", {}).get("displayValue"),
            "opportunities": opportunities,
            "diagnostics": diagnostics,
            "pass_fail_status": evaluate_pass_fail(categories, audits),
            "row_no": row_no
        }

        print(result)

        return result
    
    except requests.RequestException as e:
        return {"error": f"Request error: {e}", "strategy": strategy}
    except Exception as e:
        return {"error": f"Unexpected error: {e}", "strategy": strategy}

def score_as_percent(category):
    """
    Converts score (0.0–1.0) to percent or None.
    """
    if category and "score" in category:
        return round(category["score"] * 100)
    return None

def evaluate_pass_fail(categories, audits):

    try:
        lcp = extract_number(audits.get("largest-contentful-paint", {}).get("displayValue"))
        tbt = extract_number(audits.get("total-blocking-time", {}).get("displayValue"))      
        cls = extract_number(audits.get("cumulative-layout-shift", {}).get("displayValue"))
    except KeyError:
        return "insufficient_data"

    score = int(categories.get("performance", {}).get("score", 0) * 100)

    if (
        lcp <= 2.5 and
        tbt <= 200 and
        cls <= 0.1 and
        score >= 90
    ):
        return "PASS"
    else:
        return "FAIL"
    
def extract_number(value_str):
    if not isinstance(value_str, str):
        return None
    # Remove non-breaking spaces and extract numeric part
    cleaned = value_str.replace('\xa0', ' ').strip()
    match = re.search(r"[\d.]+", cleaned)
    if match:
        return float(match.group())
    return None
