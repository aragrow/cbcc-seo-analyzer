from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import pandas as pd
from dotenv import load_dotenv
import os

from sheet_processer import process_sheet
from sheet_loader import load_sheet, get_urls
from pagespeed import analyze_url

load_dotenv()  # Load variables from .env

global debug
debug = "Executing Main Script...\n"

PAGE_SPEED_API_KEY = os.getenv("PAGE_SPEED_API_KEY")
if not PAGE_SPEED_API_KEY:
    raise ValueError("PAGE_SPEED_API_KEY environment variable is not set. Please set it in your .env file.")

PAGE_SPEED_API_ENDPOINT = os.getenv("PAGE_SPEED_API_ENDPOINT")
if not PAGE_SPEED_API_ENDPOINT:
    raise ValueError("PAGE_SPEED_API_ENDPOINT environment variable is not set. Please set it in your .env file.")

# Replace with your actual Google API key

app = FastAPI()

# Static files (optional)
app.mount("/static", StaticFiles(directory="static"), name="static")

# Templates
templates = Jinja2Templates(directory="templates")

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request, "message": "Welcome to the SEO Analyzer!"})
# End home

@app.get("/load-sheet-before", response_class=HTMLResponse)            
async def load_sheet_form_before(request: Request):
    return templates.TemplateResponse("load_sheet.html", {"request": request, "stage": "before", "error": None})
# End load_sheet_form_before

@app.post("/load-sheet-before", response_class=HTMLResponse)
async def load_sheet_post_before(request: Request, sheet_id: str = Form(...)):
    global debug
    debug = f"Loading Sheet Before. Sheet ID: {sheet_id}\n"
    if not sheet_id:
        return templates.TemplateResponse("load_sheet.html", {
            "request": request,
            "error": "Sheet ID is required."
        })
    # Load the sheet data
    try:
        if not sheet_id.strip():
            raise ValueError("Sheet ID cannot be empty.")
        
        debug += f"Received Sheet ID: {sheet_id}\n"
        result = get_urls(sheet_id)

        debug += f"URLs to analyze: {result.get('urls', [])}\n"
        urls_to_analyze = result.get('urls', [])
        debug += result.get('debug', '')

        if not urls_to_analyze:
            debug += "No URLs found to analyze.\n"
            raise

        load_return = load_sheet(sheet_id, urls_to_analyze)
        debug += load_return.get('debug', '')

        if "error" in load_return:
            debug += f"{load_return['debug']}\n"
            debug += f"Error loading sheet: {load_return['error']}\n"
            raise 
        
        if not load_return['data_rows']:
            debug += "No data found in the sheet. Please check the sheet ID and try again."
            raise

        debug += f"Sheet data loaded successfully.\n"

        debug += f"Processing sheet data for stage 'before'.\n"
        
        process_result = process_sheet(urls_to_analyze, load_return['data_rows'], 'before')

        if not process_result:
            debug += "No valid data found in the sheet. Please check the sheet contents."   
            raise ValueError("No valid data found in the sheet. Please check the sheet contents.")
        
        debug += f"Sheet data for stage 'before' Processed.\n"

        return templates.TemplateResponse("sheet_result.html", {
            "request": request,
            "sheet_id": sheet_id,
            "result": process_result,
            "debug": f"Debug info: {debug}"
        })
    except Exception as e:
        return templates.TemplateResponse("error_sheet.html", {
            "request": request,
            "stage": "before",
            "sheet_id": sheet_id,
            "error": str(e),
            "debug": f"Debug info: {debug}"
        })
# End load_sheet_post_before

def write_new_sheet(sheet_name: str, data: dict):

    # Here you would implement the logic to write the data to the specified sheet
    # For example, using gspread to update a Google Sheet
    try:
        # Assuming you have a function `update_google_sheet` to handle the actual update
        update_google_sheet(sheet_name, data)
    except Exception as e:
        print(f"Error writing to sheet {sheet_name}: {e}")
#End write_new_sheet

def update_google_sheet(sheet_name: str, data: dict):
    """
    Placeholder function to update a Google Sheet with the provided data.
    You would implement the actual logic here using gspread or similar library.
    """
    print(f"Updating sheet '{sheet_name}' with data: {data}")
    # Actual implementation would go here
    # For example, using gspread to update a Google Sheet
    # creds = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
    # client = gspread.authorize(creds)
    # spreadsheet = client.open_by_key(sheet_id)
    # worksheet = spreadsheet.worksheet(sheet_name)
    # worksheet.update([data.keys()] + list(zip(*data.values())))
    # This is a placeholder; you would implement the actual update logic here
    print(f"Sheet '{sheet_name}' updated successfully.")            

# End update_google_sheet