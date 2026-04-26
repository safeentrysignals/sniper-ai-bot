import os
from datetime import datetime
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

TOKEN = os.getenv("BOT_TOKEN")

# ---------- COMMANDS ----------

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🤖 Sniper AI Bot is LIVE\n\nUse /signal to get latest trade setup."
    )

async def signal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    now = datetime.now()
    hour = now.hour
    day = now.weekday()   # Mon=0 ... Sun=6

    # Personal trading sessions (Nigeria time)
    active_session = (
        8 <= hour < 11 or
        13 <= hour < 16 or
        0 <= hour < 3
    )

    if not active_session:
        await update.message.reply_text(
            "⏳ NO TRADE\nOutside your sniper trading hours.\n\n"
            "Sessions:\n"
            "8AM - 11AM\n"
            "1PM - 4PM\n"
            "12AM - 3AM"
        )
        return

    # Weekend = BTC only
    if day >= 5:
        pair = "BTCUSD"
    else:
        pair = "XAUUSD"

    await update.message.reply_text(
        f"🤖 SNIPER AI SIGNAL\n\n"
        f"PAIR: {pair}\n"
        f"STATUS: Session Active\n"
        f"MODE: Awaiting sniper setup\n\n"
        f"⚡ Quality over quantity"
    )

# ---------- MAIN APP ----------

def main():
    if not TOKEN:
        print("ERROR: BOT_TOKEN is missing")
        return

    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("signal", signal))

    print("Bot starting...")

    # stable polling for Railway
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
