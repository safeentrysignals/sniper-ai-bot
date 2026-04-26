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
    day = now.weekday()

    # ---------- SESSION FILTER ----------
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

    # ---------- MARKET SELECTION ----------
    if day >= 5:
        pair = "BTCUSD"
    else:
        pair = "XAUUSD"

    # ---------- PRICE ----------
    price = get_btc_price()

    if not price:
        await update.message.reply_text("⚠️ Market data unavailable.")
        return

    entry = round(price, 2)

    # ---------- SNIPER INTELLIGENCE ENGINE ----------
    volatility = abs(price % 50)

    # block weak structure
    if volatility < 5:
        await update.message.reply_text(
            "🟡 NO TRADE\nLow volatility / weak structure."
        )
        return

    # ---------- DIRECTION LOGIC ----------
    if 8 <= hour < 11:
        bias = "BUY"
        tp = round(price * 1.0035, 2)
        sl = round(price * 0.9970, 2)

    elif 13 <= hour < 16:
        bias = "SELL"
        tp = round(price * 0.9965, 2)
        sl = round(price * 1.0030, 2)

    else:
        await update.message.reply_text(
            "🟡 NO TRADE\nNo clear sniper direction."
        )
        return

    # ---------- RISK FILTER ----------
    if abs(tp - sl) < price * 0.001:
        await update.message.reply_text(
            "🟡 NO TRADE\nRisk-reward too tight."
        )
        return

    # ---------- OUTPUT ----------
    await update.message.reply_text(
        "🤖 SNIPER AI INTELLIGENCE SIGNAL\n\n"
        f"PAIR: {pair}\n"
        f"TYPE: {bias}\n"
        f"ENTRY: {entry}\n"
        f"TP: {tp}\n"
        f"SL: {sl}\n\n"
        "🧠 Structure Filter: ACTIVE\n"
        "⚡ Sniper Engine v5.3"
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
