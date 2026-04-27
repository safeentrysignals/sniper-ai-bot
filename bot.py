import os
from datetime import datetime
from zoneinfo import ZoneInfo

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

# ==================================================
# ENV
# ==================================================
TOKEN = os.getenv("BOT_TOKEN")

# ==================================================
# SETTINGS
# ==================================================
TIMEZONE = "Africa/Lagos"

# ==================================================
# TIME HELPERS
# ==================================================
def nigeria_now():
    return datetime.now(ZoneInfo(TIMEZONE))

def in_session(hour):
    return (
        8 <= hour < 11 or
        13 <= hour < 16 or
        0 <= hour < 3
    )

# ==================================================
# PAIR DETECTION
# ==================================================
def detect_pair_from_caption(text):
    if not text:
        return "UNKNOWN"

    t = text.upper()

    if "BTC" in t:
        return "BTCUSD"

    if "XAU" in t or "GOLD" in t:
        return "XAUUSD"

    return "UNKNOWN"

# ==================================================
# VISION PLACEHOLDER
# ==================================================
def analyze_chart_image(_image_bytes):
    # Replace later with real AI vision
    return {
        "trend": "bullish",
        "price": 43000,
        "support": 42850,
        "resistance": 43250
    }

# ==================================================
# PATTERN PLACEHOLDER
# ==================================================
def detect_pattern(vision):
    if vision["trend"] == "bullish":
        return "Hammer"
    return "Shooting Star"

# ==================================================
# SIGNAL ENGINE
# ==================================================
def generate_signal(pair, vision, pattern):
    price = float(vision["price"])
    support = float(vision["support"])
    resistance = float(vision["resistance"])

    if pattern in ["Hammer", "Bullish Engulfing"]:
        return {
            "pair": pair,
            "type": "BUY",
            "entry": round(price, 2),
            "sl": round(support - 20, 2),
            "tp1": round(resistance, 2),
            "tp2": round(resistance + 80, 2),
            "pattern": pattern
        }

    return {
        "pair": pair,
        "type": "SELL",
        "entry": round(price, 2),
        "sl": round(resistance + 20, 2),
        "tp1": round(support, 2),
        "tp2": round(support - 80, 2),
        "pattern": pattern
    }

# ==================================================
# COMMANDS
# ==================================================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🤖 SNIPER AI TEST MODE ACTIVE\n\n"
        "Send M15 screenshot of XAUUSD or BTCUSD.\n"
        "Caption example:\nBTCUSD"
    )

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📸 Send chart screenshot with caption:\n"
        "BTCUSD or XAUUSD\n\n"
        "Signals only valid during sniper sessions."
    )

# ==================================================
# PHOTO HANDLER
# ==================================================
async def photo_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):

    now = nigeria_now()
    hour = now.hour

    caption = update.message.caption or ""
    pair = detect_pair_from_caption(caption)

    if pair == "UNKNOWN":
        await update.message.reply_text(
            "⚠️ Add caption:\nBTCUSD or XAUUSD"
        )
        return

    await update.message.reply_text("📊 Screenshot received. Analyzing...")

    # Download image
    photo = update.message.photo[-1]
    file = await context.bot.get_file(photo.file_id)
    image_bytes = await file.download_as_bytearray()

    # AI placeholders
    vision = analyze_chart_image(image_bytes)
    pattern = detect_pattern(vision)
    signal = generate_signal(pair, vision, pattern)

    # Session check
    session_live = in_session(hour)

    if session_live:
        mode = "🟢 LIVE SESSION"
    else:
        mode = "🟡 TEST MODE (outside session)"

    await update.message.reply_text(
        f"🤖 SNIPER AI ANALYSIS\n\n"
        f"{mode}\n\n"
        f"PAIR: {signal['pair']}\n"
        f"TYPE: {signal['type']}\n"
        f"ENTRY: {signal['entry']}\n"
        f"SL: {signal['sl']}\n"
        f"TP1: {signal['tp1']}\n"
        f"TP2: {signal['tp2']}\n"
        f"LOT: 0.01\n\n"
        f"Pattern: {signal['pattern']}"
    )

# ==================================================
# MAIN
# ==================================================
def main():

    if not TOKEN:
        print("ERROR: BOT_TOKEN missing")
        return

    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(MessageHandler(filters.PHOTO, photo_handler))

    print("Sniper AI Test Mode running...")

    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
