import json
import os
import datetime
import re
import gspread
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

from google_studio_ai import generate_report

def generate_txt_file_report(report, client_name):
    try:
        print("generating Text File with Canonical Data")
        report_dir = "report"
        os.makedirs(report_dir, exist_ok=True)
        now = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        # Sanitize client_name and url to be valid filenames
        safe_client_name = re.sub(r'[^A-Za-z0-9_\-]', '_', client_name)
        filename = f"{safe_client_name}_Canonical_Report_{now}.txt"
        filepath = os.path.join(report_dir, filename)
        with open(filepath, "w") as f:
            f.write(report)
        return filepath
    except Exception as e:
        raise ValueError(f"Unable to generate {filepath}") from e

def generate_canonical_tag_report(urls, canonicals, client_name):
  
    print("generating Canonical Tag Report")
    debug = ""

    with open(f"prompts/holistic_strategy_checks_to_canonical_tagging.md", "r") as f:
        custom_prompt = f.read()

    if not custom_prompt:
        raise ValueError(f"Prompt file for client '{client_name}' is empty or missing.")

    with open(f"report/example.txt", "r") as fi:
        example_report = fi.read()
    
    if not example_report:
        example_report = ''
    
    prompt = f"""
    You are a technical SEO expert with experience in interpreting the result from crawling all the urls and providing canonical taging.

    Make the report specific for the client {client_name}

    Given an array of audit results from crawling, analyze and summarize the key metrics based on the check requested.

    {custom_prompt}

    ## Format
    ---------------------------
    The results into a well-structured, human-readable report.

    At the end, include a **recommendations** section that:
    - Identifies problem areas
    - Suggests specific improvements
    - Prioritizes fixes based on potential SEO or UX impact
    
    ## Input:
    --------
    Below is the raw array of the , structured as JSON. Analyze and use it to create the report.

    #### urls with their canonicals:
    {json.dumps(urls, indent=2)}

    #### canonicals url:
    {json.dumps(canonicals, indent=2)}
    """

    try:
        report = generate_report(prompt)   
    except Exception as e:
        print(e)
        raise ValueError(f"LightHouse - Unable to gather analitics")
    
    try:
        file = generate_txt_file_report(report, client_name)
    except Exception as e:
        print(e)
        raise ValueError(f"Text - Unable to create Text file")

   # try:
   #     gdoc = txt_to_doc(file, client_name)
   # except Exception as e:
   #     print(e)
   #     raise ValueError(f"GDoc - Unable to create Google Doc")

    #return gdoc
    return file
