import json
import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()  # Load variables from .env

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
if not GOOGLE_API_KEY:
    raise ValueError("GOOGLE_API_KEY environment variable is not set. Please set it in your .env file.")

GOOGLE_MODEL = os.getenv("GOOGLE_MODEL")
if not GOOGLE_MODEL:
    raise ValueError("GOOGLE_MODEL environment variable is not set. Please set it in your .env file.")

# ✅ Set your Gemini API key
genai.configure(api_key=GOOGLE_API_KEY)


# 🔁 Send to Gemini and get report
def generate_report(prompt):
    model = genai.GenerativeModel(GOOGLE_MODEL)

    response = model.generate_content(prompt)
    return response.text


