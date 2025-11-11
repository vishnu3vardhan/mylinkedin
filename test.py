import gspread
from google.oauth2.service_account import Credentials

SHEET_NAME = "myconnections"

try:
    creds = Credentials.from_service_account_file(
        "service_account.json",
        scopes=[
             "https://www.googleapis.com/auth/spreadsheets",
             "https://www.googleapis.com/auth/drive",
             "https://www.googleapis.com/auth/drive.file"
        ]
    )
    client = gspread.authorize(creds)
    sheet = client.open(SHEET_NAME).sheet1
    print("✅ Connected successfully!")
    print("First 2 rows:", sheet.get_all_records()[:2])
except Exception as e:
    print("❌ ERROR:", e)
