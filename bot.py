import os
import io
from datetime import datetime
from zoneinfo import ZoneInfo

import numpy as np
from PIL import Image

from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters

TOKEN = os.getenv("BOT_TOKEN")

TIMEZONE = "Africa/Lagos"

# ==================================================
# TIME ENGINE
# ==================================================
def now():
    return datetime.now(ZoneInfo(TIMEZONE))

def in_session(hour):
    return (
        8 <= hour < 11 or
        13 <= hour < 16 or
        0 <= hour < 3
    )

# ==================================================
# IMAGE FETCH
# ==================================================
async def get_image(update, context):
    photo = update.message.photo[-1]
    file = await context.bot.get_file(photo.file_id)
    return await file.download_as_bytearray()

# ==================================================
# 🧠 FREE VISION ENGINE (NO AI - RULE BASED)
# ==================================================
def analyze_chart(image_bytes):

    try:
        image = Image.open(io.BytesIO(image_bytes)).convert("L")
        img = np.array(image)

        brightness = np.mean(img)
        contrast = np.std(img)

        # fake "trend logic"
        if brightness > 140 and contrast > 60:
            trend = "bullish"
        elif brightness < 120 and contrast > 60:
            trend = "bearish"
        else:
            trend = "neutral"

        # fake pattern detection
        if contrast > 80:
            pattern = "engulfing"
        elif contrast > 50:
            pattern = "hammer"
        else:
            pattern = "doji"

        return {
            "trend": trend,
            "pattern": pattern,
            "confidence": min(0.85, contrast / 120)
        }

    except Exception as e:
        return {
            "trend": "neutral",
            "pattern": "error",
            "confidence": 0.3
        }

# ==================================================
# SIGNAL ENGINE
# ==================================================
def signal_engine(v):

    price = 100  # fake baseline (we don’t have live feed)

    if v["trend"] == "bullish":
        return {
            "type": "BUY",
            "entry": price,
            "sl": price - 10,
            "tp1": price + 15,
            "tp2": price + 25
        }

    if v["trend"] == "bearish":
        return {
            "type": "SELL",
            "entry": price,
            "sl": price + 10,
            "tp1": price - 15,
            "tp2": price - 25
        }

    return None

# ==================================================
# HANDLER
# ==================================================
async def photo_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):

    image_bytes = await get_image(update, context)

    await update.message.reply_text("📊 Analyzing chart (FREE MODE)...")

    v = analyze_chart(image_bytes)

    signal = signal_engine(v)

    session = "LIVE" if in_session(now().hour) else "TEST MODE"

    if not signal:

        await update.message.reply_text(
            f"❌ NO TRADE\n\n"
            f"Pattern: {v['pattern']}\n"
            f"Trend: {v['trend']}\n"
            f"Confidence: {round(v['confidence'],2)}"
        )
        return

    await update.message.reply_text(
        "🤖 SNIPER AI FREE VISION ENGINE\n\n"
        f"TYPE: {signal['type']}\n"
        f"PATTERN: {v['pattern']}\n"
        f"TREND: {v['trend']}\n"
        f"CONFIDENCE: {round(v['confidence'],2)}\n\n"
        f"ENTRY: {signal['entry']}\n"
        f"SL: {signal['sl']}\n"
        f"TP1: {signal['tp1']}\n"
        f"TP2: {signal['tp2']}\n\n"
        f"SESSION: {session}\n"
        "⚡ FREE MODE ACTIVE"
    )

# ==================================================
# START COMMAND
# ==================================================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    await update.message.reply_text(
        "🤖 SNIPER AI FREE VISION BOT ACTIVE\n\n"
        "Send M15 chart screenshot.\nNo API required."
    )

# ==================================================
# MAIN
# ==================================================
def main():

    if not TOKEN:
        print("BOT TOKEN missing")
        return

    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.PHOTO, photo_handler))

    print("FREE SNIPER AI RUNNING...")

    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
