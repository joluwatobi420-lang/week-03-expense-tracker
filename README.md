# AI-Powered Expense Tracker Telegram Bot 
An automated personal finance assistant that extracts structured financial data from unstructured Telegram chat messages using LLMs and logs them directly to a Google Sheets database. It features dynamic mathematical reporting commands and a natural-language AI analytics engine.
---

## Project Demonstration

- **Loom Video Walkthrough:** [Watch the Video Demo Here](YOUR_LOOM_VIDEO_LINK_HERE)- **Live Flow Preview:**

![Expense Tracker Demo](demo.gif)

---

## Features

- **Natural Language Parsing:** Send unstructured statements like `5000 fuel Sarco filling station` or `180000 ps5 banex plaza` and let the Groq LLM isolate transaction parameters automatically.- **Google Sheets Integration:** Seamlessly appends structured timestamps, amounts, currencies, categories, and merchants into a live spreadsheet.- **Analytical Commands:** - `/today` - Summarizes items logged during the current day.  - `/week` - Displays a category breakdown of expenses over the past 7 days.  - `/month` - Compiles a monthly summary with automated category percentage allocations.  - `/cat <category_name>` - Filters specific monthly categories.  - `/undo` - Deletes the last entry row instantly if a mistake occurs.- **Natural Language Queries:** Prepend a question with `?` (e.g., `? how much on fuel this month`) to unlock a conversational data analysis engine that evaluates your sheet data in real-time.- **Testing Guardrails:** Features a custom `--dry-run` utility flag to safely test LLM execution without adding mock rows into production records.

---

## Technical Architecture

- **Language:** Python 3.14- **Interface Pipeline:** `python-telegram-bot` (v20+)- **Inference Engine:** Groq API (`llama-3.1-8b-instant`)- **Database Connection:** Google Sheets & Google Drive APIs via `gspread` & `google-oauth2`

---

## Installation & Local Setup

### 1. Clone the Repository
```bash
git clone [https://github.com/YOUR_GITHUB_USERNAME/week-03-expense-tracker.git](https://github.com/YOUR_GITHUB_USERNAME/week-03-expense-tracker.git)
cd week-03-expense-tracker