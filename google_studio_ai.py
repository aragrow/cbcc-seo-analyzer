import json
import google.generativeai as genai
from dotenv import load_dotenv
import os

load_dotenv()  # Load variables from .env

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
if not GOOGLE_API_KEY:
    raise ValueError("GOOGLE_API_KEY environment variable is not set. Please set it in your .env file.")

GOOGLE_MODEL = os.getenv("GOOGLE_MODEL")
if not GOOGLE_MODEL:
    raise ValueError("GOOGLE_MODEL environment variable is not set. Please set it in your .env file.")

# ✅ Set your Gemini API key
genai.configure(api_key=GOOGLE_API_KEY)

# 🟡 Your PageSpeed Insights array (example)
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

# 🧠 Prompt template
def create_prompt(data):
    return f"""
You are a technical web performance auditor. Analyze the following PageSpeed Insights results and generate a structured report similar to a Lighthouse audit.

For each URL, include:
- 📊 Performance
- ♿ Accessibility
- ✔️ Best Practices
- 🔍 SEO
- 💡 Recommendations (specific, actionable steps)

Format:
------------------------------------------------------------
🔗 URL: [url]
🧪 Mobile / Desktop Strategy
✅ Performance:
✅ Accessibility:
✅ Best Practices:
✅ SEO:
💡 Recommendations:
------------------------------------------------------------

Here is the raw PageSpeed data:
{json.dumps(data, indent=2)}
"""

# 🔁 Send to Gemini and get report
def generate_lighthouse_style_report(pagespeed_data):
    model = genai.GenerativeModel(GOOGLE_MODEL)
    prompt = create_prompt(pagespeed_data)

    response = model.generate_content(prompt)
    return response.text

# 📝 Main
if __name__ == "__main__":
    try:
        report = generate_lighthouse_style_report(pagespeed_results)
        with open("gemini_lighthouse_report.txt", "w") as f:
            f.write(report)
        print("✅ Report saved to gemini_lighthouse_report.txt")
    except Exception as e:
        print(f"❌ Error: {e}")
