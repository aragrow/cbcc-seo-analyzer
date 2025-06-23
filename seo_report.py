from google_studio_ai import generate_lighthouse_style_report
import json
import os
import datetime
import re
from report_to_gdoc import txt_to_doc

def generate_txt_file_report(report, client_name, url):
    try:
        print("generating Text File with SEO Report")
        report_dir = "report"
        os.makedirs(report_dir, exist_ok=True)
        now = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        # Sanitize client_name and url to be valid filenames
        safe_client_name = re.sub(r'[^A-Za-z0-9_\-]', '_', client_name)
        safe_url = re.sub(r'[^A-Za-z0-9_\-]', '_', url)
        filename = f"{safe_client_name}_{safe_url}_{now}.txt"
        filepath = os.path.join(report_dir, filename)
        with open(filepath, "w") as f:
            f.write(report)
        return filepath
    except Exception as e:
        raise ValueError(f"Unable to generate {filepath}") from e

def generate_seo_report(data, client_name, url):
  
    print("generating SEO Report")
    debug = ""

    with open(f"prompts/{client_name}__pagespeed-audit-prompt.md", "r") as f:
        custom_prompt = f.read()

    if not custom_prompt:
        raise ValueError(f"Prompt file for client '{client_name}' is empty or missing.")

    prompt = f"""
    You are a technical SEO expert with experience in interpreting Google PageSpeed Insights data.

    Given an array of audit results from the PageSpeed API (mobile and desktop), analyze and summarize the key metrics as if it were a Lighthouse report. Provide a clear breakdown of:

    - Performance
    - Accessibility
    - Best Practices
    - SEO

    ## Format
    The results into a well-structured, human-readable report.
    The report should be divided in two sections the Mobile and the Desktop Report.
    The report should be in markup to copy to a google doc.

    At the end, include a **recommendations** section that:
    - Identifies problem areas
    - Suggests specific improvements
    - Prioritizes fixes based on potential SEO or UX impact

    {custom_prompt}

    ## Input

    Below is the raw PageSpeed Insights API output, structured as JSON. Analyze and use it to populate the fields above.

    {json.dumps(data, indent=2)}
    """
    try:
        report = generate_lighthouse_style_report(prompt)   
    except Exception as e:
        print(e)
        raise ValueError(f"LightHouse - Unable to gather analitics")
    
    try:
        file = generate_txt_file_report(report, client_name, url)
    except Exception as e:
        print(e)
        raise ValueError(f"Text - Unable to create Text file")

    try:
        gdoc = txt_to_doc(file, client_name)
    except Exception as e:
        print(e)
        raise ValueError(f"GDoc - Unable to create Google Doc")

    return gdoc
    
