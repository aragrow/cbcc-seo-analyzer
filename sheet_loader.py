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

from check_inpage_urls import check_inpage_urls
from pagespeed import analyze_url, analyze_both

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

        debug = f"Getting URL from load_sheet for sheet_id: {sheet_id}\n"        
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
            
        debug += f"Spreadsheet '{spreadsheet.title}' loaded successfully.\n"

        sheet_data = {}

        # Loop through all tabs/worksheets
        for worksheet in spreadsheet.worksheets():
            title = worksheet.title
            if title != "Site Speed & Asset Optimization":
                debug += f"Skipping tab: {title}\n"
                continue
            # End if

            debug += f"📄 Loading tab: {title}"

            # Get all values from the worksheet as raw rows (lists of lists)
            all_rows = worksheet.get_all_values()

            # Skip the first two rows if they are headers
            data_rows = all_rows[2:]  # Row indices start at 0
            debug += f"\n📄 Data Rows: {data_rows[:5]}..."

            # Extract just the first column (URL column), assuming it's in column A
            urls = [
                {
                    "url": row[0].strip(),
                    "completed": str(row[13]).strip().lower() == "true"
                }
                for row in data_rows
                if len(row) > 13 and row[0].strip()
            ]
    
            debug += f"\n📄 Extracted URLs: {urls}..."

            print(f"Extracted URLs: {urls}")

        # End for loop

        debug += f"Tab '{title}' loaded successfully with {len(urls)} URLs.\n"
        return {"urls": urls, "debug": debug}

    except Exception as e:
        return {"error": str(e), "debug": debug}

def load_sheet(sheet_id: str, urls_to_analyze = []) -> dict:
    """
    Loads all tabs in the Google Sheet into a dictionary of pandas DataFrames.
    Includes debug output to confirm correct data types.
    """
    try:

        debug = f"Executing load_sheet for sheet_id: {sheet_id}\n"        
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
            
        debug += f"Spreadsheet '{spreadsheet.title}' loaded successfully.\n"

        # Loop through all tabs/worksheets
        for worksheet in spreadsheet.worksheets():
            title = worksheet.title
            if title == "Site Speed & Asset Optimization":
                result = load_site_speed_asset_optimization(worksheet, urls_to_analyze)
                debug += result.get("debug", "")

            if title == "Bad Links":
             #   result = load_bad_links(worksheet, urls_to_analyze)
                debug += result.get("debug", "")
            # End if

        # End for loop

        return {"debug": debug}

    except Exception as e:
        return {"error": str(e), "debug": debug}

def load_site_speed_asset_optimization(worksheet, urls_to_analyze) -> dict:
    """
    Analyze site speed optimization sheet.
    Returns a summary string of processed data.
    """

    try:
        debug = f"Executing load_site_speed_asset_optimization for worksheet: {worksheet.title}\n"
        title = worksheet.title
        debug += f"📄 Loading tab: {title}"
        sheet_data = {}

        # Read the first two rows as headers
        raw_header1 = worksheet.row_values(1)
        raw_header2 = worksheet.row_values(2)

        # debug += f"\n📄 Raw Header 1: {raw_header1}"
        # debug += f"\n📄 Raw Header 2: {raw_header2}"

        # Combine them into one row of unique, clean headers
        combined_headers = []
        for i in range(max(len(raw_header1), len(raw_header2))):
            part1 = raw_header1[i].strip() if i < len(raw_header1) else ""
            part2 = raw_header2[i].strip() if i < len(raw_header2) else ""
            combined = f"{part1} - {part2}".strip(" -")
            combined_headers.append(combined or f"Column_{i}")

        debug += f"\n📄 Combined Headers: {combined_headers}"

        # Get all values from the worksheet as raw rows (lists of lists)
        all_rows = worksheet.get_all_values()

        # Skip the first two rows if they are headers
        data_rows = all_rows[2:]  # Row indices start at 0
        results = []
        base_url = ""  # Replace with your base URL if needed
        for url_info in urls_to_analyze:
            url, completed = url_info["url"], url_info["completed"]
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
                result = analyze_both(url, completed)

                results.append(result)

            except Exception as e:
                results.append({"url": url, "error": str(e)})
        
        print(results)

        # Extract just the first column (URL column), assuming it's in column A
        #urls = [row[0].strip() for row in data_rows if len(row) > 0 and row[0].strip()]

        # Convert to DataFrame
        #df = pd.DataFrame(urls, columns=["Page URL"])
        df = pd.DataFrame(data_rows, columns=combined_headers)

        debug += f"\nDataFrame created for '{title}', shape: {df.shape}"

        try:
            
            # ✅ Flatten the nested list
            flat_data = [item for sublist in results for item in sublist]

            # Convert to DataFrame

            df = pd.DataFrame(flat_data, columns=combined_headers)

            # Clear existing data
            worksheet.clear(["A3:Z"])

           # set_with_dataframe(worksheet, df, row=3, col=1, include_column_header=False)

           # apply_asset_optimization_formatting(worksheet)

            print("✅ Data written successfully.")
            
        except Exception as e:
            print("❌ Error writing to Google Sheet:", e)
        # Write the DataFrame to the worksheet
        

        debug += "Google Sheet updated successfully."


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
        sheet_data = {}

        header = worksheet.row_values(1)

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
            
            # ✅ Flatten the nested list
            flat_data = [item for sublist in results for item in sublist]

            # Convert to DataFrame
            #df = pd.DataFrame(urls, columns=["Page URL"])
            headers = ["page_url", "audit_date", "in_page_url", "status_code", "tag"]
            df = pd.DataFrame(flat_data, columns=headers)

            # Clear existing data
            worksheet.clear()

            set_with_dataframe(worksheet, df, row=1, col=1, include_column_header=True)

            apply_bad_links_formatting(worksheet)

            print("✅ Data written successfully.")
            
        except Exception as e:
            print("❌ Error writing to Google Sheet:", e)
        # Write the DataFrame to the worksheet
        

        debug += "Google Sheet updated successfully."

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

    debug = "Applying Bad Links Formating"
    try: 

        # Define ranges
        range_1 = GridRange.from_a1_range('C2:L', worksheet)
        range_2 = GridRange.from_a1_range('O2:X', worksheet)

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

        # Apply rules
        rules = get_conditional_format_rules(worksheet)
        rules.clear()
        rules.extend([rule_green, rule_yellow, rule_red])
        rules.save()

        return {"debug": debug}
    
    # End try-except
    except Exception as e:
        return {"error": str(e), "debug": debug}