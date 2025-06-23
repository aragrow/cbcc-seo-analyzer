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

    # === DERIVE SHEET NAME FROM FILE PATH ===
    # Target Google Drive path
    folder_path_parts = [GOOGLE_DRIVE_REPORT_FOLDER, client_name]
    parent_id = "root"
    doc_title = os.path.splitext(os.path.basename(filepath))[0]

    try:
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

    except Exception as e:
        print(f"Error Find or create each folder level: {e}")
        return False

    try:
        # === STEP 2: READ TXT FILE CONTENT ===
        with open(filepath, "r", encoding="utf-8") as f:
            lines = f.readlines()

        # Format: one row per line, one column (A) per row
        data_rows = [[line.strip()] for line in lines if line.strip()]

    except Exception as e:
        print(f"Error Reading the text file: {e}")
        return False

    try:
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
    except Exception as e:
        print(f"Error Creating Google Doc: {e}")
        return False
    
    try:
        drive_service.permissions().create(
            fileId=doc_id,
            body={
                "type": "user",  # or 'domain', 'group', or 'anyone'
                "role": "writer",  # 'reader', 'commenter', or 'writer'
                "emailAddress": creds.service_account_email  # replace with real address
            },
            sendNotificationEmail=False,  # Don't send email notification
            fields="id"
        ).execute()

    except Exception as e:
        print(f"Error Granting Permission Google Doc: {e}")
        return False

    
    # === STEP 4: INSERT TEXT INTO DOC ===

    try:
        doc = docs_service.documents().get(documentId=doc_id).execute()
        content = doc.get("body", {}).get("content", [])
        end_index = content[-1]["endIndex"] if content else 1
    
    except Exception as e:
        print(f"Error Requesting Google Doc: {e}")
        return False

    requests = []
    for line in lines:
        try:
            text = str(line).strip()
            if not text:
                continue
            requests.append({
                "insertText": {
                    "location": {"index": end_index},
                    "text": text + "\n"
                }
            })
            end_index += len(text) + 1
        except Exception as ex:
            print(f"Skipped line due to error: {ex} — line: {line}")

    print(requests)
    print("-------")
    print(f"Doc Id: {doc_id}")

    try:
        if requests:
            docs_service.documents().batchUpdate(documentId=doc_id, body={"requests": requests}).execute()
            print(f"Successfully inserted {len(requests)} lines")
        else:
            print(" No valid lines to insert.")

    except Exception as e:
        print(f"Error Inserting Text in Doc: {e}")
        return False

     # === STEP 5: Output the link
    print(f" View it here: https://docs.google.com/document/d/{doc_id}/edit")

    return f"https://docs.google.com/document/d/{doc_id}/edit"
    
   
