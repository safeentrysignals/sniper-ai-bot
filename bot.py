import os
import requests
from datetime import datetime
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

TOKEN = os.getenv("BOT_TOKEN")

# ---------- LIVE PRICE ENGINE ----------

def get_btc_price():
    try:
        url = "https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT"
        data = requests.get(url, timeout=5).json()
        return float(data["price"])
    except:
        return None

# ---------- COMMANDS ----------

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🤖 Sniper AI Bot is LIVE\n\nUse /signal to get latest trade setup."
    )

async def signal(update: Update, context: ContextTypes.DEFAULT_TYPE):

    now = datetime.now()
    hour = now.hour
    day = now.weekday()   # Mon=0 ... Sun=6

    # Trading sessions (Nigeria time)
    active_session = (
        8 <= hour < 11 or
        13 <= hour < 16 or
        0 <= hour < 3
    )

    if not active_session:
        await update.message.reply_text(
            "⏳ NO TRADE\nOutside sniper trading hours.\n\n"
            "Sessions:\n"
            "8AM - 11AM\n"
            "1PM - 4PM\n"
            "12AM - 3AM"
        )
        return

    # Get live price
    price = get_btc_price()

    if not price:
        await update.message.reply_text("⚠️ Market data unavailable.")
        return

    # Weekend = BTC only
    if day >= 5:
        pair = "BTCUSD"
    else:
        pair = "XAUUSD (live BTC mode)"

    entry = round(price, 2)
    tp = round(price * 1.002, 2)
    sl = round(price * 0.998, 2)

    await update.message.reply_text(
        "🤖 SNIPER AI SIGNAL\n\n"
        f"PAIR: {pair}\n"
        f"ENTRY: {entry}\n"
        f"TP: {tp}\n"
        f"SL: {sl}\n\n"
        "⚡ Live Market Mode Active"
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

    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
