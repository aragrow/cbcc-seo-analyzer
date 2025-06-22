from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import pandas as pd
from dotenv import load_dotenv
import os

# from sheet_processer import process_sheet
from sheet_loader import load_sheet, get_urls


load_dotenv()  # Load variables from .env

global debug
global client_name
debug = "Executing Main Script...\n"
client_name = 'webeyecare'

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

@app.get("/load-sheet", response_class=HTMLResponse)            
async def load_sheet_form(request: Request):
    return templates.TemplateResponse("load_sheet.html", {"request": request, "stage": "before", "error": None})
# End load_sheet_form_before

@app.post("/load-sheet", response_class=HTMLResponse)
async def load_sheet_post(request: Request, sheet_id: str = Form(...)):
    global client_name
    debug = f"Loading Sheet. Sheet ID: {sheet_id}\n"
    if not sheet_id:
        return templates.TemplateResponse("load_sheet.html", {
            "request": request,
            "error": "Sheet ID is required."
        })
    # Load the sheet data
    try:
        if not sheet_id.strip():
            debug += "Sheet Id cannot be empty"
            raise ValueError("Sheet ID cannot be empty.")
        
        result = get_urls(sheet_id)

        print(f"URLs to analyze: {result.get('urls', [])}\n")
        urls_to_analyze = result.get('urls', [])
        debug += result.get('debug', '')

        if not urls_to_analyze:
            raise ValueError("No URLs found to analyze.")

        load_return = load_sheet(sheet_id, urls_to_analyze, client_name)

        if "error" in load_return:
            raise ValueError(f"{load_return['debug']}\n")
       
        
        if not load_return['data_rows']:
            raise ValueError("No data found in the sheet. Please check the sheet ID and try again.\n")

        print("Sheet data loaded successfully.\n")
            
        return templates.TemplateResponse("sheet_result.html", {
            "request": request,
            "sheet_id": sheet_id,
       #     "result": process_result,
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

