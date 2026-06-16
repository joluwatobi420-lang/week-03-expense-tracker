import json
import requests
from pydantic import BaseModel, ValidationError
from typing import Optional


# =========================
# DATA MODEL
# =========================
class Expense(BaseModel):
    amount: float
    currency: str
    category: str
    merchant: Optional[str] = None
    note: Optional[str] = None


# =========================
# SYSTEM PROMPT
# =========================
SYSTEM_PROMPT = """
You are an expense parser for a personal finance bot used in Nigeria.

Parse user input into STRICT JSON only.

Required fields:
- amount: number
- currency: NGN by default unless another currency is explicitly mentioned
- category: one of [food, transport, fuel, groceries, utilities, rent,
entertainment, health, shopping, family, work, other]
- merchant: string or null
- note: string or null

Rules:
- Output ONLY valid JSON
- No markdown
- No ``` blocks
- category must be a string
- merchant must be null if unknown
- note must be null if absent
"""


# =========================
# CALL LLM
# =========================
def call_llm(text):
    url = "http://localhost:11434/api/generate"

    payload = {
        "model": "llama3.2:3b",
        "prompt": SYSTEM_PROMPT + "\n\nUser input: " + text,
        "stream": False
    }

    response = requests.post(url, json=payload)

    if response.status_code != 200:
        raise Exception(response.text)

    raw = response.json()["response"]

    # clean possible markdown
    raw = raw.replace("```json", "").replace("```", "").strip()

    return raw


# =========================
# PARSE EXPENSE
# =========================
def parse_expense(text):
    raw = call_llm(text)

    print("\nINPUT:", text)
    print("RAW:", raw)

    try:
        data = json.loads(raw)
        expense = Expense(**data)
        return expense.model_dump()

    except Exception as e:
        print("ERROR:", e)
        return None