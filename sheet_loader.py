import pandas as pd
import gspread
from gspread_dataframe import set_with_dataframe
from gspread_formatting import (
    get_conditional_format_rules,
    ConditionalFormatRule,
    BooleanRule,
    BooleanCondition,
    CellFormat,
    Color,
    GridRange
)
import traceback
from google.oauth2.service_account import Credentials
from fastapi.templating import Jinja2Templates
from datetime import datetime

from check_inpage_urls import check_inpage_urls
from pagespeed import analyze_both
from seo_report import generate_seo_report

# Templates
templates = Jinja2Templates(directory="templates")

# Define the scopes and credentials path
SCOPES_READONLY = ["https://www.googleapis.com/auth/spreadsheets.readonly"]
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

SERVICE_ACCOUNT_FILE = "credentials/google_service_account.json"

def get_urls(sheet_id: str) -> dict:

    """
    Loads all tabs in the Google Sheet into a dictionary of pandas DataFrames.
    Includes debug output to confirm correct data types.
    """
    try:
        debug = ''
        print(f"Getting URL from load_sheet for sheet_id: {sheet_id}\n")        
        # Authenticate and connect to Google Sheets
        try:
            creds = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
            debug += "Credentials loaded successfully.\n"
        except Exception as cred_err:
            debug += f"Error loading credentials: {cred_err}\n"
            raise

        try:
            client = gspread.authorize(creds)
            debug += "Client authorized successfully.\n"
        except Exception as client_err:
            debug += f"Error authorizing Client: {client_err}\n"
            raise

        try:
            spreadsheet = client.open_by_key(sheet_id)
            debug += "Spreadsheet opened successfully.\n"
        except Exception as e:
            debug += f"Error opening spreadsheet: {traceback.format_exc()}\n"
            raise
            
        print("Spreadsheet '{spreadsheet.title}' loaded successfully.\n")

        # Loop through all tabs/worksheets
        for worksheet in spreadsheet.worksheets():
            title = worksheet.title
            if title != "Site Speed & Asset Optimization": continue

            # Get all values from the worksheet as raw rows (lists of lists)
            all_rows = worksheet.get_all_values()

            # Skip the first two rows if they are headers
            data_rows = all_rows[2:]  # Row indices start at 0

            start_row_index = 3  # This is the actual Google Sheet row number where data starts (after skipping headers)

            # Extract URLs and metadata with the real worksheet row number
            urls = [
                {
                    "url": row[0].strip(),                    # Column A (URL)
                    "before_completed": row[12].strip(),      # Column M (index 12)
                    "after_completed": row[24].strip(),       # Column Y (index 24)
                    "row_no": start_row_index + i             # Google Sheets row number
                }
                for i, row in enumerate(data_rows)            # <-- FIXED: you need `enumerate()` here
                if len(row) > 24 and row[0].strip()           # Only include rows with enough columns and a non-empty URL
            ]
        
        # End for loop

        if not urls:
            debug += "No URLs found in the worksheet.\n"
            raise ValueError("No URLs found in the worksheet.")
            
        print(f"Extracted URLs: {urls}")

        return {"urls": urls, "debug": debug}

    except Exception as e:
        return {"error": str(e), "debug": debug}

def load_sheet(sheet_id: str, urls_to_analyze = [], client_name = '') -> dict:
    """
    Loads all tabs in the Google Sheet into a dictionary of pandas DataFrames.
    Includes debug output to confirm correct data types.
    """
    try:
        debug = ""
        print(f"Executing load_sheet for sheet_id: {sheet_id}\n")        
        # Authenticate and connect to Google Sheets
        try:
            creds = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
        except Exception as cred_err:
            print(f"Error loading credentials: {cred_err}\n")
            raise

        try:
            client = gspread.authorize(creds)
        except Exception as client_err:
            print(f"Error authorizing Client: {client_err}\n")
            raise

        try:
            spreadsheet = client.open_by_key(sheet_id)        
        except Exception as e:
            print(f"Error opening spreadsheet: {traceback.format_exc()}\n")
            raise
            
        print(f"Spreadsheet '{spreadsheet.title}' loaded successfully.\n")

        # Loop through all tabs/worksheets
        for worksheet in spreadsheet.worksheets():
            title = worksheet.title
            if title == "Site Speed & Asset Optimization":
                result = load_site_speed_asset_optimization(worksheet, urls_to_analyze, client_name)
                debug += result.get("debug", "")

            if title == "Bad Links":
            #   result = load_bad_links(worksheet, urls_to_analyze)
                debug += result.get("debug", "")
            # End if

        # End for loop

        return {"debug": debug}

    except Exception as e:
        return {"error": str(e), "debug": debug}

def load_site_speed_asset_optimization(worksheet, urls_to_analyze, client_name) -> dict:
    """
    Analyze site speed optimization sheet.
    Returns a summary string of processed data.
    """

    try:
        title = worksheet.title

        print(f"Executing load_site_speed_asset_optimization for worksheet: {title}\n")
        print(f"Client Name: {client_name}")
        print(f"URLs: {urls_to_analyze}")

        insights_data = []

        base_url = ""  # Replace with your base URL if needed
        for url_info in urls_to_analyze:
            print(f"Processing URL INFO: {url_info}\n")
            url, before_completed, after_completed, row_no = url_info["url"], url_info["before_completed"], url_info["after_completed"], url_info["row_no"]
            print(f"Processing URL: {url}\n")
            try:
                if base_url == "":
                    # Extract base URL from the first URL in the list
                    base_url = url
                    if base_url.startswith("http://"):
                        base_url = base_url.replace("http://", "https://")
                    elif not base_url.startswith("https://"):
                        base_url = "https://" + base_url

                    url = base_url
                else:
                    url = base_url + '/' + url
                
                print(f"Checking URL: {url}")  
                if(before_completed == 'TRUE' and after_completed == 'TRUE'): continue  

                result = analyze_both(url, before_completed, row_no)

                if not result:
                    debug += f"\nNo result returned from analyze_both for URL: {url}"
                    raise ValueError(f"No result returned from analyze_both for URL: {url}")

                report = generate_seo_report(result, client_name, url)

                if not report:
                    raise ValueError("No SEO Report Generated.")

                # Add the report afterward
                result["report"] = report

                insights_data.append(result)

            except Exception as e:
                insights_data.append({"url": url, "error": str(e)})
        
        print(insights_data)

        try:

            # === Step 2: Prepare DataFrame ===
            records = []
            today = datetime.today().strftime('%m/%d/%Y')

            for entry in insights_data:
                url = entry.get('url')
                report = entry.get('report')
                before_mobile = entry.get('before_mobile', {})
                before_desktop = entry.get('before_desktop', {})
                after_mobile = entry.get('after_mobile', {})
                after_desktop = entry.get('after_desktop', {})

                row_no = before_mobile.get('row_no') or after_mobile.get('row_no')
                if not row_no:
                    print(f"Skipping {url} — missing row number")
                    continue

                if before_mobile and before_desktop:

                    record = {
                        "Date Reviewed": today,
                        "Core Web Vital Assestment (before)": before_mobile.get('pass_fail_status', None),
                        "Performance (before)": before_mobile.get('performance', None),
                        "Accessibility (before)": before_mobile.get('accessibility', None),
                        "Best Practices (before)": before_mobile.get('best_practices', None),
                        "SEO (before)": before_mobile.get('seo', None),
                        "Performance (before)_D": before_desktop.get('performance', None),
                        "Accessibility (before)_D": before_desktop.get('accessibility', None),
                        "Best Practices (before)_D": before_desktop.get('best_practices', None),
                        "SEO (before)_D": before_desktop.get('seo', None),
                        "Recomendations": report,
                        "Completed": True
                    }

                    #records.append(record)

                    df = pd.DataFrame([record])
                    range = [f"B{row_no}:M{row_no}"]
                    print(f"Range: {range}")
                    # Clear existing data
                    worksheet.batch_clear(range)

                    set_with_dataframe(worksheet, df, row=row_no, col=2, include_column_header=False)

                else: 

                    record = {
                        "Date Reviewed": today,
                        "Core Web Vital Assestment (after)": after_mobile.get('pass_fail_status', None),
                        "Performance (after)": after_mobile.get('performance', None),
                        "Accessibility (after)": after_mobile.get('accessibility', None),
                        "Best Practices (after)": after_mobile.get('best_practices', None),
                        "SEO (after)": after_mobile.get('seo', None),
                        "Performance (after)_D": after_desktop.get('performance', None),
                        "Accessibility (after)_D": after_desktop.get('accessibility', None),
                        "Best Practices (after)_D": after_desktop.get('best_practices', None),
                        "SEO (after)_D": after_desktop.get('seo', None),
                        "Recomendations": report,
                        "Completed": True
                    }

                    df = pd.DataFrame([record])
                    range = [f"N{row_no}:Y{row_no}"]
                    print(f"Range: {range}")
                    # Clear existing data
                    worksheet.batch_clear(range)

                    set_with_dataframe(worksheet, df, row=row_no, col=14, include_column_header=False)

            apply_asset_optimization_formatting(worksheet)
  
        except Exception as e:
            print("Error writing to Google Sheet:", e)
            debug += f'Error writing to Google Sheet: {e}'
            return {"error": str(e), "debug": debug}
        # Write the DataFrame to the worksheet
        

        print("Google Sheet updated successfully.")


    except Exception as e:
        return {"error": str(e), "debug": debug}
    
# End load_site_speed_asset_optimization

def load_bad_links(worksheet, urls_to_analyze) -> dict:
    """
    Analyze site speed optimization sheet.
    Returns a summary string of processed data.
    """

    try:
        debug = f"Executing load_bad_links for worksheet: {worksheet.title}\n"
        title = worksheet.title
        debug += f"📄 Loading tab: {title}"
       
        # Get all values from the worksheet as raw rows (lists of lists)
        all_rows = worksheet.get_all_values()

        # Skip the first two rows if they are headers
        data_rows = all_rows[1:]  # Row indices start at 0

        # Extract just the first column (URL column), assuming it's in column A
        #urls = [row[0].strip() for row in data_rows if len(row) > 0 and row[0].strip()]

        # Loop through urls_to_analyze and execute check_inpage_urls(url)
        results = []
        base_url = ""  # Replace with your base URL if needed
        for url in urls_to_analyze:
            try:
                if base_url == "":
                    # Extract base URL from the first URL in the list
                    base_url = url
                    print(f"Base URL set to: {base_url}")
                    if base_url.startswith("http://"):
                        base_url = base_url.replace("http://", "https://")
                        print(f"Base URL set to: {base_url}")
                    elif not base_url.startswith("https://"):
                        base_url = "https://" + base_url
                        print(f"Base URL set to: {base_url}")

                    url = base_url
                else:
                    url = base_url + '/' + url
                
                #print(f"Checking URL: {url}")           
                result = check_inpage_urls(url)

                results.append(result)

            except Exception as e:
                results.append({"url": url, "error": str(e)})
        
        # End for loop
        # print(results)
        try:
            
            # Flatten the nested list
            flat_data = [item for sublist in results for item in sublist]

            # Convert to DataFrame
            #df = pd.DataFrame(urls, columns=["Page URL"])
            headers = ["page_url", "audit_date", "in_page_url", "status_code", "tag"]
            df = pd.DataFrame(flat_data, columns=headers)

            # Clear existing data
            worksheet.clear()

            set_with_dataframe(worksheet, df, row=1, col=1, include_column_header=True)

            apply_bad_links_formatting(worksheet)
                    
        except Exception as e:
            print("Error writing to Google Sheet:", e)
        # Write the DataFrame to the worksheet
        

        print("Google Sheet updated successfully.")

        return {"status": "success", "debug": debug}

    except Exception as e:
        return {"error": str(e), "debug": debug}
    
# End load_bad_links

def apply_bad_links_formatting(worksheet) :

    debug = "Applying Bad Links Formating"
    try: 
        # Define formatting rules
        range_d = GridRange.from_a1_range('D1:D', worksheet)

        rule_green = ConditionalFormatRule(
            ranges=[range_d],
            booleanRule=BooleanRule(
                condition=BooleanCondition('NUMBER_EQ', ['200']),
                format=CellFormat(backgroundColor=Color(0.8, 1, 0.8))
            )
        )

        rule_yellow = ConditionalFormatRule(
            ranges=[range_d],
            booleanRule=BooleanRule(
                condition=BooleanCondition('NUMBER_EQ', ['301']),
                format=CellFormat(backgroundColor=Color(1, 1, 0.6))
            )
        )

        rule_red = ConditionalFormatRule(
            ranges=[range_d],
            booleanRule=BooleanRule(
                condition=BooleanCondition('CUSTOM_FORMULA', ['=AND(ISNUMBER(D1), D1<>200, D1<>301)']),
                format=CellFormat(backgroundColor=Color(1, 0.8, 0.8))
            )
        )

        # Apply rules
        rules = get_conditional_format_rules(worksheet)
        rules.clear()
        rules.extend([rule_green, rule_yellow, rule_red])
        rules.save()

        return {"debug": debug}
    
    # End try-except
    except Exception as e:
        return {"error": str(e), "debug": debug}

def apply_asset_optimization_formatting(worksheet) :

    debug = "Applying Asset Optimization Formatting"
    try: 

        # Define ranges
        range_1 = GridRange.from_a1_range('D3:K', worksheet)
        range_2 = GridRange.from_a1_range('P3:W', worksheet)

        rule_green = ConditionalFormatRule(
            ranges=[range_1, range_2],
            booleanRule=BooleanRule(
                condition=BooleanCondition('NUMBER_BETWEEN', ['90', '100']),
                format=CellFormat(backgroundColor=Color(0.8, 1, 0.8))
            )
        )

        rule_yellow = ConditionalFormatRule(
            ranges=[range_1, range_2],
            booleanRule=BooleanRule(
                condition=BooleanCondition('NUMBER_BETWEEN', ['50', '89']),
                format=CellFormat(backgroundColor=Color(1, 1, 0.6))
            )
        )

        rule_red = ConditionalFormatRule(
            ranges=[range_1, range_2],
              booleanRule=BooleanRule(
                condition=BooleanCondition('NUMBER_BETWEEN', ['0', '49']),
                format=CellFormat(backgroundColor=Color(1, 0.8, 0.8))
            )
        )

        # Create GridRange from A1 notation
        range_c = GridRange.from_a1_range('C3:C', worksheet)
        range_d = GridRange.from_a1_range('O3:O', worksheet)

        rule_pass = ConditionalFormatRule(
            ranges=[range_c,range_d],
            booleanRule=BooleanRule(
                condition=BooleanCondition('TEXT_EQ', ['PASS']),
                format=CellFormat(backgroundColor=Color(0.8, 1, 0.8))
            )
        )

        rule_fail = ConditionalFormatRule(
            ranges=[range_c, range_d],
            booleanRule=BooleanRule(
                condition=BooleanCondition('TEXT_EQ', ['FAIL']),
                format=CellFormat(backgroundColor=Color(1, 0.8, 0.8))
            )
        )

        # Apply rules
        rules = get_conditional_format_rules(worksheet)
        rules.clear()
        rules.extend([rule_green, rule_yellow, rule_red, rule_pass, rule_fail])
        rules.save()

        return {"debug": debug}
    
    # End try-except
    except Exception as e:
        return {"error": str(e), "debug": debug}