import os
import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    MessageHandler,
    CommandHandler,
    filters,
    ContextTypes,
)
from openai import OpenAI

# 🔑 Load from Railway variables
TELEGRAM_TOKEN = os.getenv("8750167234:AAFYcRpk0KiX2MvyJf0QloRxHgFhks5Umlk")
OPENAI_API_KEY = os.getenv("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")

CHANNEL_USERNAME = "@multilevelnks"

client = OpenAI(api_key=OPENAI_API_KEY)

user_usage = {}

def can_use(user_id):
    today = datetime.date.today()

    if user_id not in user_usage:
        user_usage[user_id] = {"date": today, "count": 0}

    if user_usage[user_id]["date"] != today:
        user_usage[user_id] = {"date": today, "count": 0}

    if user_usage[user_id]["count"] >= 1:
        return False

    user_usage[user_id]["count"] += 1
    return True

async def is_subscribed(user_id, bot):
    try:
        member = await bot.get_chat_member(CHANNEL_USERNAME, user_id)
        return member.status in ["member", "administrator", "creator"]
    except:
        return False

def check_writing(text):
    prompt = f"""
You are a STRICT IELTS examiner.

You MUST be harsh and realistic.
Do NOT overestimate.

Band descriptors:
Band 5 = frequent errors, limited vocabulary
Band 6 = some errors but understandable
Band 7 = strong control, few errors

Output:

Band Score:

Task Achievement:
...

Coherence:
...

Vocabulary:
...

Grammar:
...

Mistakes (max 3):

Improved Version:

Text:
{text}
"""

    response = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[{"role": "user", "content": prompt}]
    )

    return response.choices[0].message.content

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Send your writing ✍️\n\nFree: 1 check per day."
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id

    if not await is_subscribed(user_id, context.bot):
        keyboard = [
            [InlineKeyboardButton("Join Channel", url="https://t.me/multilevelnks")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.message.reply_text(
            "🚫 Join the channel first.",
            reply_markup=reply_markup
        )
        return

    if not can_use(user_id):
        await update.message.reply_text(
            "⚠️ Daily limit reached."
        )
        return

    text = update.message.text

    await update.message.reply_text("Checking... ⏳")

    result = check_writing(text)

    await update.message.reply_text(result)

app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

app.run_polling()