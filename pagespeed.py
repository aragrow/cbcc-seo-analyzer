import requests
from dotenv import load_dotenv
import os
import sys

PAGE_SPEED_API_KEY = os.getenv("PAGE_SPEED_API_KEY")
if not PAGE_SPEED_API_KEY:
    raise ValueError("PAGE_SPEED_API_KEY environment variable is not set. Please set it in your .env file.")

PAGE_SPEED_API_ENDPOINT = os.getenv("PAGE_SPEED_API_ENDPOINT")
if not PAGE_SPEED_API_ENDPOINT:
    raise ValueError("PAGE_SPEED_API_ENDPOINT environment variable is not set. Please set it in your .env file.")


def analyze_both(url: str, completed: bool) -> dict:
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
            "after_mobile": analyze_url(url, strategy="mobile"),
            "after_desktop": analyze_url(url, strategy="desktop")
        }
    else:
        return {
            "url": url,
            "before_mobile": analyze_url(url, strategy="mobile"),
            "before_desktop": analyze_url(url, strategy="desktop")
        }

def analyze_url(url: str, strategy: str) -> dict:
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
        "strategy": strategy
    }

    print(f"PageSpeed analyzing: {strategy}")

    if PAGE_SPEED_API_KEY:
        params["key"] = PAGE_SPEED_API_KEY

    try:
        response = requests.get(PAGE_SPEED_API_ENDPOINT, params=params, timeout=60)
        response.raise_for_status()
        data = response.json()

        lighthouse = data.get("lighthouseResult", {})
        audits = lighthouse.get("audits", {})
        categories = lighthouse.get("categories", {})

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
            "opportunities": opportunities,
            "diagnostics": diagnostics,
            "pass_fail_status": evaluate_pass_fail(categories)
        }

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

def evaluate_pass_fail(data):
    audits = data.get("performance", {}).get("audits", {})
    score = data.get("performance", {}).get("score", 0) * 100

    try:
        lcp = audits["largest-contentful-paint"]["numericValue"]  # in ms
        tbt = audits["total-blocking-time"]["numericValue"]        # in ms
        cls = audits["cumulative-layout-shift"]["numericValue"]    # unitless
    except KeyError:
        return "insufficient_data"

    # Convert ms to seconds for LCP
    lcp_sec = lcp / 1000

    if (
        lcp_sec <= 2.5 and
        tbt <= 200 and
        cls <= 0.1 and
        score >= 90
    ):
        return "pass"
    else:
        return "fail"