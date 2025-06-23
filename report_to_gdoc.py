import os
import gspread
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

# === CONFIGURATION ===

GOOGLE_DRIVE_REPORT_FOLDER = os.getenv("GOOGLE_DRIVE_REPORT_FOLDER")
if not GOOGLE_DRIVE_REPORT_FOLDER:
    raise ValueError("GOOGLE_DRIVE_REPORT_FOLDER environment variable is not set. Please set it in your .env file.")

SCOPES = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]

SERVICE_ACCOUNT_FILE = "credentials/google_service_account.json"

# === SETUP GOOGLE API AUTH ===
creds = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
gc = gspread.authorize(creds)
drive_service = build('drive', 'v3', credentials=creds)
docs_service = build("docs", "v1", credentials=creds)

def txt_to_doc(filepath: str, client_name):

    try:
        # === LOAD TXT FILE ===
        with open(filepath, "r", encoding="utf-8") as file:
            lines = file.readlines()

        # === PARSE LINES TO ROWS ===
        # You can choose CSV-style or one-column-per-line
        rows = [[line.strip()] for line in lines if line.strip()]  # Single-column format

        # === DERIVE SHEET NAME FROM FILE PATH ===
        # Target Google Drive path
        folder_path_parts = [GOOGLE_DRIVE_REPORT_FOLDER, client_name]
        parent_id = "root"
        doc_title = os.path.splitext(os.path.basename(filepath))[0]

        # Step 1: Find or create each folder level
        for folder_name in folder_path_parts:
            query = f"'{parent_id}' in parents and name = '{folder_name}' and mimeType = 'application/vnd.google-apps.folder'"
            response = drive_service.files().list(q=query, fields="files(id)").execute()
            files = response.get("files", [])

            if files:
                parent_id = files[0]["id"]
            else:
                new_folder = drive_service.files().create(
                    body={
                        "name": folder_name,
                        "mimeType": "application/vnd.google-apps.folder",
                        "parents": [parent_id]
                    },
                    fields="id"
                ).execute()
                parent_id = new_folder["id"]

        # === STEP 2: READ TXT FILE CONTENT ===
        with open(filepath, "r", encoding="utf-8") as f:
            lines = f.readlines()

        # Format: one row per line, one column (A) per row
        data_rows = [[line.strip()] for line in lines if line.strip()]


        # === STEP 3: CREATE GOOGLE DOC ===
        doc_metadata = {
            "title": doc_title,
            "parents": [parent_id]  # Put the doc in the correct folder
        }
        doc = drive_service.files().create(
            body=doc_metadata,
            fields="id"
        ).execute()
        doc_id = doc.get("id")

        # === STEP 4: INSERT TEXT INTO DOC ===
        requests = []
        for line in lines:
            line = line.strip()
            if line:
                requests.append({
                    "insertText": {
                        "location": {"index": 1},
                        "text": line + "\n"
                    }
                })

        if requests:
            docs_service.documents().batchUpdate(documentId=doc_id, body={"requests": requests[::-1]}).execute()
            print(f"Google Doc '{doc_title}' created with {len(lines)} lines.")

        # === STEP 5: Output the link
        print(f" View it here: https://docs.google.com/document/d/{doc_id}/edit")

        return f"https://docs.google.com/document/d/{doc_id}/edit"
    
    except Exception as e:
        print(f"Error: {e}")
        return False
