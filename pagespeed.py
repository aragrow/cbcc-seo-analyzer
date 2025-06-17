import requests

def analyze_both(url: str, API_KEY: str = None, API_ENDPOINT: str = None) -> dict:
    """
    Analyze a URL for both mobile and desktop strategies using Google PageSpeed Insights API.
    
    Args:
        url (str): The webpage URL to analyze.
        api_key (str): Google API key.
    
    Returns:
        dict: A dictionary with separate results for mobile and desktop.
    """
    return {
        "mobile": analyze_url(url, strategy="mobile", API_KEY=API_KEY, API_ENDPOINT=API_ENDPOINT),
        "desktop": analyze_url(url, strategy="desktop", API_KEY=API_KEY, API_ENDPOINT=API_ENDPOINT  )
    }

def analyze_url(url: str, strategy: str, API_KEY: str = None, API_ENDPOINT: str = None) -> dict:
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

    if API_KEY:
        params["key"] = API_KEY

    try:
        response = requests.get(API_ENDPOINT, params=params, timeout=20)
        response.raise_for_status()
        data = response.json()

        lighthouse = data.get("lighthouseResult", {})
        categories = lighthouse.get("categories", {})

        return {
            "url": data.get("id"),
            "strategy": strategy,
            "performance": score_as_percent(categories.get("performance")),
            "accessibility": score_as_percent(categories.get("accessibility")),
            "best_practices": score_as_percent(categories.get("best-practices")),
            "seo": score_as_percent(categories.get("seo")),
        }

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
