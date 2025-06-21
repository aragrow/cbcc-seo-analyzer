from google_studio_ai import generate_lighthouse_style_report
import json
import os
import datetime
import re

def generate_txt_file_report(report, client_name, url):
    
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
    return f"Report saved to {filepath}"

def generate_seo_report(data, client_name, url):

    debug = ""

    with open(f"prompts/{client_name}__pagespeed-audit-prompt.md", "r") as f:
        custom_prompt = f.read()

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
    
    report = generate_lighthouse_style_report(prompt)

    if not report:
        debug += "Failed to generate Lighthouse style report.\n"
        raise ValueError(f"Report generation failed: {debug}")
    
    file = generate_txt_file_report(report, client_name, url)

    if not file:
        debug += "Failed to generate TXT file report.\n"
        raise ValueError(f"File generation failed: {debug}") 