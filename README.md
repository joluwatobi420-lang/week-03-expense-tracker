# AI-Powered Expense Tracker Bot

An intelligent, conversational financial assistant built over Telegram. This project leverages Large Language Models (LLMs) to perform structured data extraction—transforming messy, natural language inputs into deterministic database rows in real time.
---

## The Core Engineering Focus: NL → JSON

The primary focus of this project isn't just the bot interface—it's the implementation of **structured data extraction**.


Human Text: "1200 fuel at Sarco station"
│
▼ (Groq LLM Pipeline)
JSON Schema: { "amount": 1200, "category": "Transport", 
"description": "fuel at Sarco station" }
│
▼
Google Sheets Database Row Updated

By enforcing a strict JSON schema on unstructured human thoughts with zero user friction, this pipeline acts as a seamless bridge between raw user input and rigid production databases. 
---
## Code Architecture & Features

The application is engineered modularly with a clear separation of concerns across dedicated runtime layers:

- **`parse_expense(user_text)`**: The core AI Extraction Engine. Isolates the incoming string and orchestrates structural JSON schemas via Groq and Llama 3.1.
- **`analyze_expenses(user_query)`**: The In-Context Analytics Engine. Pulls the live Google Sheet dataset, injects it directly into the LLM's context window as a structured payload, and evaluates ad-hoc tracking inquiries.
- **`handle_message()`**: The central router that accurately intercepts chat intent to toggle between logging operations and data analysis.
- **Custom Commands (`/start`, `/week`)**: Built-in macros to streamline user initialization and trigger instant 7-day digest summaries.

---

## Tech Stack

- **Language:** Python-
-  **LLM Orchestration:** Groq Cloud API (`llama-3.1-8b-instant`)
-  **Interface:** `python-telegram-bot` wrapper
-  **Database:** Google Sheets API v4

---

## Setup & Installation

### 1. Clone the Repository
```bash
git clone [https://github.com/joluwatobi420-lang/week-03-expense-tracker.git](https://github.com/joluwatobi420-lang/week-03-expense-tracker.git)
cd week-03-expense-trackerYOUR_GITHUB_USERNAME/week-03-expense-tracker.git)
cd week-03-expense-tracker
