import os
import sys
import json
from datetime import datetime, timedelta
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from groq import Groq
from dotenv import load_dotenv

from sheets_handler import append_to_sheet, get_filtered_expenses, delete_last_row, get_expenses_as_csv_string

load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")


groq_client = Groq(api_key=GROQ_API_KEY)


def parse_expense_with_groq(text: str) -> dict:
    """Calls the Groq LLM dynamically to pull structured JSON fields from raw user text."""
    try:
        system_instruction = (
            "You are a precise expense parsing assistant. Analyze the user's input "
            "and extract: amount (as a number), currency (default to NGN if unclear), "
            "category, merchant, and note. "
            "Your response must be ONLY a valid JSON object. Do not include markdown code blocks like ```json."
        )

        completion = groq_client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": system_instruction},
                {"role": "user", "content": text}
            ],
            temperature=0.1
        )
        raw_json_str = completion.choices[0].message.content.strip()
        
        if raw_json_str.startswith("```"):
            raw_json_str = raw_json_str.strip("```").strip("json").strip()

        expense_data = json.loads(raw_json_str)
        return expense_data
    
    except Exception as e:
        print(f"Error communicating with Groq API: {e}")
        # Secure fallback block structure to prevent system crash
        return {
            "amount": 0,
            "currency": "NGN",
            "category": "error",
            "merchant": "Unknown",
            "note": f"Failed to parse text: '{text}'"
        }
def analyze_expenses_with_ai(user_question: str, csv_data: str) -> str:
    """
    Passes the user's natural language question along with the last 30 days
    of expenses formatted as CSV data to Groq for custom financial analysis.
    """
    try:
        system_instruction = (
            "You are an expense analyst. Given the user's question and their expense data, "
            "answer concisely with specific numbers. Use NGN. Round to nearest naira. "
            "Answer in 1-3 sentences max. No markdown lists unless the user asks for one."
        )

        prompt_payload = (
            f"EXPENSES (CSV):\n{csv_data}\n\n"
            f"QUESTION: {user_question}"
            )
        
        completion = groq_client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": system_instruction},
                {"role": "user", "content": prompt_payload}
            ],
            temperature=0.2
            )
        return completion.choices[0].message.content.strip()
    except Exception as e:
        print(f"Error in AI Analyst engine query: {e}")
        return " I ran into an error pulling your analysis records."    


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/start — Welcome message and instructions."""
    await update.message.reply_text(
        " Welcome to your AI Expense Tracker Bot!\n\n"
        "**Quick Usage Guide:**\n"
        "• To log an expense, type normally: `150000 iPhone XR TkMall` or `4500 lunch`\n"
        "• `/today` — View total and items logged today\n"
        "• `/week` — Check breakdown of the last 7 days\n"
        "• `/month` — Month total with category percentages\n"
        "• `/cat <name>` — Filter specific categories (e.g. `/cat food`)\n"
        "• `/undo` — Remove the last recorded sheet item instantly",
        parse_mode="Markdown"
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Processes incoming normal chat entries, parses via Groq, logs to Sheets."""
    text = update.message.text.strip()
    print(f"INPUT RECEIVED: {text}")

    if text.startswith("?"):
        status_msg = await update.message.reply_text("Analysing your spreadsheet metrics...")

        csv_data = get_expenses_as_csv_string()
        user_question = text.lstrip("?").strip()

        ai_analysis_response = analyze_expenses_with_ai(user_question, csv_data)

        await status_msg.edit_text(ai_analysis_response)
        return
     
    try:
        expense_data = parse_expense_with_groq(text)

        if "--dry-run" in sys.argv:
            print("DRY RUN MODE ACTIVE: Skipping Google Sheets write operation.")
            await  update.message.reply_text(
                f"**[Dry Run Mode] Expenses parsed Successfully**\n\n"
                f"**Amount:** {expense_data.get('currency', 'NGN')} {expense_data.get('amount', 0):,.2f}\n"
                f"**Category:** {expense_data.get('category', 'General').capitalize()}\n"
                f"**Merchant:**{expense_data.get('merchant', 'Unknown')}\n\n"
                f"**Note: This transaction was not saved to your live sheet database.*",
                parse_mode="Markdown"
            )
            return
          
        append_to_sheet(expense_data, text)
          
        amount = expense_data.get("amount", "Unknown")
        currency = expense_data.get("currency", "NGN")
        merchant = expense_data.get("merchant", "Unknown")
        category = expense_data.get("category", "General")

        await update.message.reply_text(
              f" **Expense Recorded Successfully**\n\n"
              f" **Amount:** {currency} {amount:,.2f}\n"
              f" **Category:** {category.capitalize()}\n"
              f" **Merchant:** {merchant}",
              parse_mode="Markdown"
        )
        
    except Exception as e:
        print(f"Error handling message workflow: {e}")
        await update.message.reply_text(" Sorry, I couldn't log that expense. Please try again.")

async def today_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/today — Sum and list of today's expenses."""
    expenses = get_filtered_expenses()
    if not expenses:
        await update.message.reply_text(" No expense records could be found.")
        return
    
    today_str = datetime.now().strftime("%Y-%m-%d")
    today_expenses = []
    total_sum = 0

    for exp in expenses:
        if str(exp.get("Timestamp", "")).startswith(today_str):
            try:
                amt = float(exp.get("amount", 0))
            except:
                amt = 0
            total_sum += amt
            today_expenses.apend(f" {exp.get('currency', 'NGN')} {amt:,.2f} - {exp.get('merchant', 'Unknown')} ({exp.get('category', 'General')})")        

    if not today_expenses:
        await update.message.reply_text("You haven't recorded any expenses today!")
        return

    report = f"** Today's Expenses Summary** \n\n" + "\n".join(today_expenses) + f"\n\n **Total Today:** NGN {total_sum:,.2f}"    
    await update.message.reply_text(report, parse_mode="Markdown")


async def week_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/week command handler."""

    status_message = await update.message.reply_text("Fetching and analysing your sheet data...")

    expenses = get_filtered_expenses()
    if not expenses:
        await update.message.edit_text(" No expense records could be found.")
        return

    seven_days_ago = datetime.now() - timedelta(days=7)
    category_totals = {}
    total_sum = 0

    for exp in expenses:
        try: 
            raw_ts = str(exp.get("Timestamp", "")).strip()
            if not raw_ts:
                continue

            clean_ts = raw_ts.split(".")[0]
            try:
                exp_date = datetime.strptime(clean_ts, "%Y-%m-%d %H:%M:%S")
            except ValueError:
                exp_date = datetime.strptime(clean_ts, "%Y-%m-%d")

            if exp_date >= seven_days_ago:
                cat = str(exp.get("category", "Other")).strip().capitalize()
                amt = float(exp.get("amount", 0))

            category_totals[cat] = category_totals.get(cat, 0) + amt
            total_sum += amt
        except Exception as e:
            print(f"Skipping row error in analysis parsing: {e}")
            continue

    if not category_totals:
        await update.message.reply_text(" No expenses recorded in the last 7 days.")
        return

    report = " **Last 7 Days Summary by Category**\n\n"
    for cat, amt in category_totals.items():
        report += f" **{cat}**: NGN {amt:,.2f}\n"
    report += f"\n **Total Last 7 Days:** NGN {total_sum:,.2f}"

    await update.message.reply_text(report, parse_mode="Markdown")

async def month_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/month — Current month summary by category, with percentages."""
    expenses = get_filtered_expenses()
    if not expenses:
        await update.message.reply_text(" No expense records could be found.")
        return

    current_month_str = datetime.now().strftime("%Y-%m")
    category_totals = {}
    total_sum = 0

    for exp in expenses:
        if str(exp.get("Timestamp", "")).startswith(current_month_str):
            try:
                cat = str(exp.get("category", "Other")).strip().capitalize()
                amt = float(exp.get("amount", 0))

                category_totals[cat] = category_totals.get(cat, 0) + amt
                total_sum += amt
            except:
                continue
                
    if total_sum == 0:
        await update.message.reply_text(" No expenses recorded for this month yet.")
        return

    report = f" **{datetime.now().strftime('%B %Y')} Summary**\n\n"
    for cat, amt in category_totals.items():
        percentage = (amt / total_sum) * 100
        report += f" **{cat}**: NGN {amt:,.2f} ({percentage:.1f}%)\n"
    report += f"\n **Total This Month:** NGN {total_sum:,.2f}"

    await update.message.reply_text(report, parse_mode="Markdown")

async def cat_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/cat command handler."""
    if not context.args:
        await update.message.reply_text(" Please specify a category name.\nExample: `/cat food`", parse_mode="Markdown")
        return

    target_cat = context.args[0].strip().lower()
    expenses = get_filtered_expenses()
    current_month_str = datetime.now().strftime("%Y-%m")

    cat_expenses = []
    total_sum = 0

    for exp in expenses:
        if str(exp.get("Timestamp", "")).startswith(current_month_str):
            if str(exp.get("category", "")).strip().lower() == target_cat:
                try:
                    amt = float(exp.get("amount", 0))
                except:
                    amt = 0
                total_sum += amt
                date_only = str(exp.get("Timestamp", "")).split(" ")[0]
                cat_expenses.append(f"• {date_only} | NGN {amt:,.2f} - {exp.get('merchant', 'Unknown')}")
    
    if not cat_expenses:
        await update.message.reply_text(f" No items found under category '{target_cat.capitalize()}' this month.")
        return

    report = f" **Expenses for '{target_cat.capitalize()}' This Month**\n\n" + "\n".join(cat_expenses) + f"\n\n **Subtotal:** NGN {total_sum:,.2f}"
    await update.message.reply_text(report, parse_mode="Markdown")

async def undo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/undo command handler."""
    await update.message.reply_text(" Checking sheet to remove last logged entry...")
    result = delete_last_row()
    if result == "Success":
        await update.message.reply_text(" The last expense entry was successfully deleted from your sheet.")
    elif result == "Empty":
        await update.message.reply_text(" Your sheet is already empty (or only headers remain).")
    else:
        await update.message.reply_text(" Failed to delete row due to an unexpected spreadsheet error.")

def main():
    if "--dry-run" in sys.argv:
        print("Launching Expense Tracker Telegram Bot...    [DRY RUN MODE ENABLED]")
    else:
        print("Launching Expense Tracker Telegram Bot...    [PRODUCTION MODE ENABLED]")  

    application = Application.builder().token(TELEGRAM_BOT_TOKEN).read_timeout(30).write_timeout(30).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("undo", undo))
    application.add_handler(CommandHandler("today", today_command))
    application.add_handler(CommandHandler("week", week_command))
    application.add_handler(CommandHandler("month", month_command))
    application.add_handler(CommandHandler("cat", cat_command))
 
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    application.run_polling()

if __name__ == "__main__":
    main()