# SNIPER AI BOT (Production Starter Architecture)
# Telegram + Screenshot Input + Vision Stub + Pattern Engine + Claude Stub + Signal Output

import os
import io
import requests
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
# ENV VARIABLES
# ==================================================
TOKEN = os.getenv("BOT_TOKEN")
CLAUDE_API_KEY = os.getenv("CLAUDE_API_KEY")   # optional for later use

# ==================================================
# SETTINGS
# ==================================================
TIMEZONE = "Africa/Lagos"

# ==================================================
# HELPERS
# ==================================================

def nigeria_now():
    return datetime.now(ZoneInfo(TIMEZONE))

def in_session(hour):
    return (
        8 <= hour < 11 or
        13 <= hour < 16 or
        0 <= hour < 3
    )

def detect_pair_from_caption(text):
    if not text:
        return "UNKNOWN"

    text = text.upper()

    if "BTC" in text:
        return "BTCUSD"

    if "XAU" in text or "GOLD" in text:
        return "XAUUSD"

    return "UNKNOWN"

# ==================================================
# VISION LAYER (STUB FOR NOW)
# Replace later with GPT-4o Vision API
# ==================================================

def analyze_chart_image(image_bytes):
    """
    Placeholder chart analysis.
    Replace later with real vision API call.
    """

    return {
        "trend": "bullish",
        "price": 43000,
        "support": 42850,
        "resistance": 43250,
        "confidence": 0.72
    }

# ==================================================
# PATTERN ENGINE (RULE LOGIC)
# Replace later with YOLO/OpenCV detector
# ==================================================

def detect_candlestick_pattern(vision):
    trend = vision["trend"]

    if trend == "bullish":
        return "Hammer"

    return "Shooting Star"

# ==================================================
# SNIPER RULE ENGINE
# ==================================================

def generate_signal(pair, vision, pattern, hour):
    if not in_session(hour):
        return {
            "status": "NO TRADE",
            "reason": "Outside sniper session"
        }

    price = float(vision["price"])
    support = float(vision["support"])
    resistance = float(vision["resistance"])

    # BUY LOGIC
    if pattern in ["Hammer", "Bullish Engulfing"]:

        entry = round(price, 2)
        sl = round(support - 20, 2)
        tp1 = round(resistance, 2)
        tp2 = round(resistance + 80, 2)

        return {
            "status": "SIGNAL",
            "pair": pair,
            "type": "BUY",
            "entry": entry,
            "sl": sl,
            "tp1": tp1,
            "tp2": tp2,
            "pattern": pattern
        }

    # SELL LOGIC
    if pattern in ["Shooting Star", "Bearish Engulfing"]:

        entry = round(price, 2)
        sl = round(resistance + 20, 2)
        tp1 = round(support, 2)
        tp2 = round(support - 80, 2)

        return {
            "status": "SIGNAL",
            "pair": pair,
            "type": "SELL",
            "entry": entry,
            "sl": sl,
            "tp1": tp1,
            "tp2": tp2,
            "pattern": pattern
        }

    return {
        "status": "NO TRADE",
        "reason": "No valid candle confirmation"
    }

# ==================================================
# CLAUDE CONFIRMATION LAYER (OPTIONAL STUB)
# ==================================================

def claude_confirm(signal_data):
    """
    Later connect Claude API.
    For now auto-confirm.
    """
    return True

# ==================================================
# TELEGRAM COMMANDS
# ==================================================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🤖 SNIPER AI ONLINE\n\n"
        "Send M15 screenshot of XAUUSD or BTCUSD.\n"
        "Caption example:\nBTCUSD"
    )

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📸 Send screenshot of M15 chart.\n\n"
        "Supported pairs:\n"
        "- BTCUSD\n"
        "- XAUUSD"
    )

# ==================================================
# PHOTO HANDLER
# ==================================================

async def photo_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):

    now = nigeria_now()
    hour = now.hour

    if not update.message.photo:
        return

    await update.message.reply_text("📊 Screenshot received. Analyzing...")

    # pair from caption
    caption = update.message.caption or ""
    pair = detect_pair_from_caption(caption)

    if pair == "UNKNOWN":
        await update.message.reply_text(
            "⚠️ Add caption:\nBTCUSD or XAUUSD"
        )
        return

    # download highest quality photo
    photo = update.message.photo[-1]
    file = await context.bot.get_file(photo.file_id)

    image_bytes = await file.download_as_bytearray()

    # Step 1: Vision
    vision = analyze_chart_image(image_bytes)

    # Step 2: Pattern
    pattern = detect_candlestick_pattern(vision)

    # Step 3: Sniper Rules
    result = generate_signal(pair, vision, pattern, hour)

    # Step 4: Claude Confirm
    if result["status"] == "SIGNAL":
        approved = claude_confirm(result)

        if approved:
            await update.message.reply_text(
                f"🤖 SNIPER AI SIGNAL\n\n"
                f"PAIR: {result['pair']}\n"
                f"TYPE: {result['type']}\n"
                f"ENTRY: {result['entry']}\n"
                f"SL: {result['sl']}\n"
                f"TP1: {result['tp1']}\n"
                f"TP2: {result['tp2']}\n"
                f"LOT: 0.01\n\n"
                f"Pattern: {result['pattern']}\n"
                f"⚡ Claude Confirmed"
            )
            return

    await update.message.reply_text(
        f"⏳ NO TRADE\n{result.get('reason', 'Filtered setup')}"
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

    print("Sniper AI running...")

    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
