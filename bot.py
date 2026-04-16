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

# 🔑 Load environment variables
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# 🔍 DEBUG (will show in Railway logs)
print("TOKEN:", TELEGRAM_TOKEN)
print("OPENAI:", OPENAI_API_KEY)

CHANNEL_ID = -1003787853665

client = OpenAI(api_key=OPENAI_API_KEY)

# 📊 User usage storage (temporary memory)
user_usage = {}

# 🔒 Daily limit (1 per day)
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

# 🔍 Check if user joined channel
async def is_subscribed(user_id, bot):
    try:
        member = await bot.get_chat_member(CHANNEL_ID, user_id)
        return member.status in ["member", "administrator", "creator"]
    except:
        return False

# 🧠 AI evaluation
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

# 👋 Start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Send your writing ✍️\n\nFree: 1 check per day.\nBe honest. Think again."
    )

# 📩 Main handler
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id

    # ❌ Not subscribed
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

    # 🔒 Daily limit
    if not can_use(user_id):
        await update.message.reply_text(
            "⚠️ Daily limit reached.\n\nCome back tomorrow."
        )
        return

    text = update.message.text

    await update.message.reply_text("Checking... ⏳")

    try:
        result = check_writing(text)
        await update.message.reply_text(result)
    except Exception as e:
        print("ERROR:", e)
        await update.message.reply_text("⚠️ Error processing your request.")

# ▶️ Run bot
app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

print("Bot is running...")

app.run_polling()
