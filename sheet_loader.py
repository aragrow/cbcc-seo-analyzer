import pandas as pd
import gspread
import traceback
from google.oauth2.service_account import Credentials
from fastapi.templating import Jinja2Templates
# Templates
templates = Jinja2Templates(directory="templates")

# Define the scopes and credentials path
SCOPES = ["https://www.googleapis.com/auth/spreadsheets.readonly"]
SERVICE_ACCOUNT_FILE = "credentials/google_service_account.json"

def get_urls(sheet_id: str) -> dict:
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
            urls = [row[0].strip() for row in data_rows if len(row) > 0 and row[0].strip()]
    
            debug += f"\n📄 Extracted URLs: {urls}..."

            print(f"Extracted URLs: {urls}")

        # End for loop

        return {"url": urls, "debug": debug}

    except Exception as e:
         return {"error": str(e), "debug": debug}

def load_sheet(sheet_id: str) -> dict:
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

        sheet_data = {}

        # Loop through all tabs/worksheets
        for worksheet in spreadsheet.worksheets():
            title = worksheet.title
            if title != "Site Speed & Asset Optimization":
                result = load_site_speed_asset_optimization(worksheet)
                sheet_data[title] = result.get("sheet_data", {})

            if title != "Bad Links":
                result = load_bad_links(worksheet)
                sheet_data[title] = result.get("sheet_data", {})
            # End if

        # End for loop

        return {"sheet_data": sheet_data, "debug": debug}

    except Exception as e:
         return {"error": str(e), "debug": debug}

def load_site_speed_asset_optimization(worksheet) -> dict:
    """
    Analyze site speed optimization sheet.
    Returns a summary string of processed data.
    """

    try:
        title = worksheet.title
        debug += f"📄 Loading tab: {title}"
        sheet_data = {}

        # Read the first two rows as headers
        raw_header1 = worksheet.row_values(1)
        raw_header2 = worksheet.row_values(2)

        debug += f"\n📄 Raw Header 1: {raw_header1}"
        debug += f"\n📄 Raw Header 2: {raw_header2}"

        # Combine them into one row of unique, clean headers
        combined_headers = []
        for i in range(max(len(raw_header1), len(raw_header2))):
            part1 = raw_header1[i].strip() if i < len(raw_header1) else ""
            part2 = raw_header2[i].strip() if i < len(raw_header2) else ""
            combined = f"{part1} - {part2}".strip(" -")
            combined_headers.append(combined or f"Column_{i}")

        print(f"Combined Headers: {combined_headers}")

        # Get all values from the worksheet as raw rows (lists of lists)
        all_rows = worksheet.get_all_values()

        # Skip the first two rows if they are headers
        data_rows = all_rows[2:]  # Row indices start at 0

        print(f"Data Rows: {data_rows[:5]}...")
        # Extract just the first column (URL column), assuming it's in column A
        #urls = [row[0].strip() for row in data_rows if len(row) > 0 and row[0].strip()]

        # Convert to DataFrame
        #df = pd.DataFrame(urls, columns=["Page URL"])
        df = pd.DataFrame(data_rows, columns=combined_headers)

        debug += f"DataFrame created for '{title}', shape: {df.shape}"

        # Store in dict
        sheet_data = df

        debug += f"Tab '{title}' loaded successfully with {len(df)} URLs.\n"

        return {"sheet_data": sheet_data, "debug": debug}

    except Exception as e:
        return {"error": str(e), "debug": debug}
    
# End load_site_speed_asset_optimization

def load_bad_links(worksheet) -> dict:
    """
    Analyze site speed optimization sheet.
    Returns a summary string of processed data.
    """

    try:
        title = worksheet.title
        debug += f"📄 Loading tab: {title}"
        sheet_data = {}

        header = worksheet.row_values(1)

        # Get all values from the worksheet as raw rows (lists of lists)
        all_rows = worksheet.get_all_values()

        # Skip the first two rows if they are headers
        data_rows = all_rows[1:]  # Row indices start at 0

        print(f"Data Rows: {data_rows[:5]}...")
        # Extract just the first column (URL column), assuming it's in column A
        #urls = [row[0].strip() for row in data_rows if len(row) > 0 and row[0].strip()]

        # Convert to DataFrame
        #df = pd.DataFrame(urls, columns=["Page URL"])
        df = pd.DataFrame(data_rows, columns=header)

        debug += f"DataFrame created for '{title}', shape: {df.shape}"

        # Store in dict
        sheet_data = df

        debug += f"Tab '{title}' loaded successfully with {len(df)} URLs.\n"

        return {"sheet_data": sheet_data, "debug": debug}

    except Exception as e:
        return {"error": str(e), "debug": debug}
    
# End load_bad_links

    # End try-except

