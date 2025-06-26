import requests
import os
import json
from dotenv import load_dotenv
import sys

load_dotenv()  # Load variables from .env


# --- Configuration ---
# It's best to store your API key in an environment variable
# On Linux/macOS: export GOOGLE_SAFE_BROWSING_API_KEY='YOUR_API_KEY'
# On Windows: set GOOGLE_SAFE_BROWSING_API_KEY='YOUR_API_KEY'
# Replace 'your_app_name' with a unique identifier for your application.
# Replace '1.0' with your application's version.
CLIENT_ID = "larry-toxic-link-checker-script"
CLIENT_VERSION = "1.0"
GOOGLE_API_KEY = os.environ.get("GOOGLE_SAFE_BROWSING_API_KEY")
if not GOOGLE_API_KEY:
    raise ValueError("GOOGLE_API_KEY environment variable is not set. Please set it in your .env file.")


# Google Safe Browsing API Endpoint
API_URL = "https://safebrowsing.googleapis.com/v4/threatMatches:find"

# Threat types to check for (common ones)
THREAT_TYPES = ["MALWARE", "PHISHING", "UNWANTED_SOFTWARE", "SOCIAL_ENGINEERING"]
PLATFORM_TYPES = ["ANY_PLATFORM"]
THREAT_ENTRY_TYPES = ["URL"]

def check_toxic_link_gsb(url: str) -> tuple[bool, str | None]:
    print('Checking Toxic Link')
    """
    Checks a single URL against the Google Safe Browsing API.

    Args:
        url (str): The URL to check.

    Returns:
        tuple: (is_toxic, threat_type)
               is_toxic is True if a threat is found, False otherwise.
               threat_type is a string indicating the type of threat (e.g., 'MALWARE', 'PHISHING')
                           or None if no threat was found, or an error message string.
    """
    if not url:
        print("URL Missing")
        return False, "URL Missing."

    # Add a basic check for scheme if missing (GSB often expects it)
    if not url.startswith(('http://', 'https://')):
        print("Warning: URL does not start with http:// or https://.")
        return False, "URL does not start with http:// or https://."

    payload = {
        "client": {
            "clientId": CLIENT_ID,
            "clientVersion": CLIENT_VERSION
        },
        "threatInfo": {
            "threatTypes": THREAT_TYPES,
            "platformTypes": PLATFORM_TYPES,
            "threatEntryTypes": THREAT_ENTRY_TYPES,
            "threatEntries": [
                {"url": url}
            ]
        }
    }

    params = {"key": GOOGLE_API_KEY}

    try:

        print(f"Attempting POST to {API_URL} with key and payload...")
        print("--- Payload being sent ---")
        print(json.dumps(payload, indent=4)) # Pretty print the payload
        print("--------------------------")

        # Send the POST request to the Safe Browsing API
        response = requests.post(API_URL, params=params, json=payload)

        # Raise an exception for bad status codes (4xx or 5xx)
        response.raise_for_status()

        result = response.json()

        # The API returns a 'matches' key if any threats are found
        if 'matches' in result and result['matches']:
            # If there are matches, the link is considered toxic.
            # We can extract the first threat type for simplicity.
            threat_type = result['matches'][0].get('threatType', 'UNKNOWN')
            return True, threat_type
        else:
            # No matches means the API didn't flag it
            return False, None

    except requests.exceptions.RequestException as e:
        # Handle network errors, connection issues, or API errors
        print(f"API Request Error: {e}")
        sys.exit(1)
        # Check if it's likely an invalid API key error (often 400 or 403)
        if response is not None and (response.status_code == 400 or response.status_code == 403):
            return False, f"Possible API Key error or invalid request ({response.status_code})"
        return False, f"Request failed: {e}"
    except Exception as e:
        # Catch any other unexpected errors
        print(f"An unexpected error occurred: {e}")
        return False, f"Unexpected error: {e}"
    
def strip_www(domain):
    """Removes 'www.' prefix from a domain name for easier comparison."""
    # Ensure case-insensitivity for www check
    if domain.lower().startswith('www.'):
        return domain[4:]
    return domain