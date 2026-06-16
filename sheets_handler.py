import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

creds = Credentials.from_service_account_file("credentials.json", scopes=SCOPES)
client = gspread.authorize(creds)

SPREADSHEET_NAME = "Expenses Tracker"
spreadsheet = client.open("Expenses Tracker")
sheet = spreadsheet.get_worksheet(0)

def append_to_sheet(expense_data: dict, raw_text: str):
    """ Appends a new formatted expense row into the Google Sheet."""
    try:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        amount = expense_data.get("amount", 0)
        currency = expense_data.get("currency", "NGN")
        category = expense_data.get("category", "General")
        merchant = expense_data.get("merchant", "Unknown")
        note = expense_data.get("note", raw_text)

        row_to_insert = [timestamp, amount, currency, category, merchant, note]
        
        sheet.append_row(row_to_insert)
        print(f"Successfully logged to sheet: {row_to_insert}")
        
    except Exception as e:
        print(f"Error appending row to Google Sheets: {e}")
        raise e


def get_filtered_expenses() -> list:
    """Fetches all record entries from the worksheet as a list of dictionaries."""
    try:
        all_records = sheet.get_all_records()
        return all_records
    except Exception as e:
        print(f"Error fetching data records from sheet: {e}")
        return []


def delete_last_row() -> str:
    """Deletes the last recorded expense row from the sheet."""
    try:
        all_values = sheet.get_all_values()
        row_count = len(all_values)
        
        if row_count <= 1:
            return "Empty"
            
        sheet.delete_rows(row_count)
        return "Success"
    except Exception as e:
        print(f"Error deleting row from Google Sheets: {e}")
        return "Error"
    
    
def get_expenses_as_csv_string() -> str:
    """
    Fetches all sheet records and converts them into a raw CSV text string
    for the LLM analyst engine to read.
    """
    try:
        records = sheet.get_all_records()
        if not records:
            return "date,amount,currency,category,merchant,note"
            
        # Create the CSV Header line
        csv_lines = ["date,amount,category,merchant,note"]
        
        # Take up to the last 100 entries (to stay safely within context limits)
        for row in records[-100:]:
            date = str(row.get("Timestamp", "")).split(" ")[0] # Just the YYYY-MM-DD
            amount = row.get("amount", 0)
            category = row.get("category", "General")
            merchant = row.get("merchant", "Unknown")
            note = row.get("note", "").replace(",", " ") # Remove commas to keep CSV clean
            
            csv_lines.append(f"{date},{amount},{category},{merchant},{note}")
            
        return "\n".join(csv_lines)
    except Exception as e:
        print(f"Error converting data to CSV format: {e}")
        return "Error fetching data"





    
