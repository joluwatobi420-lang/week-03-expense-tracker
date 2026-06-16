import gspread

gc = gspread.service_account(filename="credentials.json")

sheet = gc.open_by_url(
    "https://docs.google.com/spreadsheets/d/YOUR_SHEET_ID/edit"
).sheet1

print("Connected to Expense Tracker")