import json
import requests
from dotenv import load_dotenv
import os

load_dotenv()  # Load variables from .env

ABACUS_API_KEY = os.getenv("ABACUS_API_KEY")
if not ABACUS_API_KEY:
    raise ValueError("ABACUS_API_KEY environment variable is not set. Please set it in your .env file.")

MODEL_ID = os.getenv("MODEL_ID")
if not MODEL_ID:
    raise ValueError("MODEL_ID environment variable is not set. Please set it in your .env file.")

# Example PageSpeed results
pagespeed_results = [
    {
        "url": "https://webeyecare.com",
        "after_mobile": {
            "error": "Unexpected error: 'NoneType' object has no attribute 'get'",
            "strategy": "mobile"
        },
        "after_desktop": {
            "error": "Request error: HTTPSConnectionPool(host='www.googleapis.com', port=443): Read timed out. (read timeout=20)",
            "strategy": "desktop"
        }
    }
]

def create_prompt(pagespeed_results):
    intro = """You are a technical web auditor. Please analyze the following PageSpeed Insights results and generate a structured report similar to a Chrome Lighthouse audit.

Include sections:
- Performance
- Accessibility
- Best Practices
- SEO
- Recommendations (clear, actionable steps)

Use the following format per site:
---------------------------------------------
🔍 URL: [url]
📱 Mobile | 🖥️ Desktop
✅ Performance:
✅ Accessibility:
✅ Best Practices:
✅ SEO:
💡 Recommendations:
---------------------------------------------

Raw PageSpeed Data:
"""
    return intro + json.dumps(pagespeed_results, indent=2)

def send_to_abacus(prompt):
    url = "https://api.abacus.ai/v1/deployTextGenerationModel"
    payload = {
        "apiKey": ABACUS_API_KEY,
        "modelDeploymentId": MODEL_ID,
        "prompt": prompt,
        "temperature": 0.7,
        "maxTokens": 1500,
        "topP": 0.9
    }

    response = requests.post(url, json=payload)
    if response.ok:
        result = response.json()
        return result.get("generatedText", "No text generated.")
    else:
        raise Exception(f"Error from Abacus.AI: {response.status_code} - {response.text}")

if __name__ == "__main__":
    try:
        prompt = create_prompt(pagespeed_results)
        report = send_to_abacus(prompt)
        with open("abacus_lighthouse_report.txt", "w") as f:
            f.write(report)
        print("✅ Report generated and saved to abacus_lighthouse_report.txt")
    except Exception as e:
        print(f"❌ Error: {e}")
