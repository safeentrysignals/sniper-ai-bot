import os
import io
import re
from datetime import datetime
from zoneinfo import ZoneInfo

import cv2
import numpy as np
import pytesseract

from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters

TOKEN = os.getenv("BOT_TOKEN")
TIMEZONE = "Africa/Lagos"

# ==================================================
# TIME ENGINE
# ==================================================
def now():
    return datetime.now(ZoneInfo(TIMEZONE))

def fmt(dt):
    return dt.strftime("%I:%M %p").lstrip("0")

def session_ok(h):
    return 8 <= h < 11 or 13 <= h < 16 or 0 <= h < 3

# ==================================================
# IMAGE FETCH (ROBUST VERSION)
# ==================================================
async def get_image(update, context):

    try:
        msg = update.message

        if msg.photo:
            file = await context.bot.get_file(msg.photo[-1].file_id)
            return await file.download_as_bytearray()

        if msg.document:
            file = await context.bot.get_file(msg.document.file_id)
            return await file.download_as_bytearray()

        return None

    except Exception as e:
        print("IMAGE FETCH ERROR:", e)
        return None

# ==================================================
# IMAGE LOAD (SAFE)
# ==================================================
def load(img_bytes):

    try:
        if not img_bytes:
            return None

        arr = np.frombuffer(img_bytes, np.uint8)
        img = cv2.imdecode(arr, cv2.IMREAD_COLOR)

        return img

    except Exception as e:
        print("IMAGE LOAD ERROR:", e)
        return None

# ==================================================
# OCR ENGINE (SAFE MODE)
# ==================================================
def extract_text(img):

    try:
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        text = pytesseract.image_to_string(gray)
        return text.upper()

    except Exception as e:
        print("OCR ERROR:", e)
        return ""

# ==================================================
# PAIR DETECTION
# ==================================================
def detect_pair(text):

    if "XAU" in text:
        return "XAUUSD"
    if "BTC" in text:
        return "BTCUSD"

    return "UNKNOWN"

# ==================================================
# PRICE DETECTION
# ==================================================
def detect_price(text):

    try:
        matches = re.findall(r"\d+\.\d+", text)

        for m in matches:
            val = float(m)
            if 1000 < val < 200000:
                return val

        return None

    except:
        return None

# ==================================================
# STRUCTURE ENGINE
# ==================================================
def detect_structure(img):

    try:
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        h, w = gray.shape

        left = np.mean(gray[:, :w//2])
        right = np.mean(gray[:, w//2:])

        delta = right - left

        if delta > 5:
            return "bullish pressure"
        elif delta < -5:
            return "bearish pressure"

        return "sideways / unclear"

    except:
        return "unknown"

# ==================================================
# LEVELS
# ==================================================
def levels(price):

    return {
        "r1": round(price + 2, 2),
        "r2": round(price + 4, 2),
        "s1": round(price - 2, 2),
        "s2": round(price - 4, 2),
    }

# ==================================================
# RESPONSE BUILDER
# ==================================================
def build(pair, price, structure, dt):

    session = "✅ Session valid" if session_ok(dt.hour) else "🟡 Outside session"

    if pair == "UNKNOWN" or price is None:

        return (
            "❌ INSUFFICIENT DATA\n\n"
            "Bot cannot clearly read this chart.\n\n"
            "Fix checklist:\n"
            "- Zoom chart in\n"
            "- Show price scale (right side)\n"
            "- Avoid cropped screenshots\n"
        )

    lv = levels(price)

    return (
        f"📊 SNIPER AI TRUTH ENGINE v10\n\n"
        f"PAIR: {pair}\n"
        f"PRICE: {price}\n"
        f"TIME: {fmt(dt)} WAT {session}\n\n"

        "📌 MARKET STRUCTURE:\n"
        f"{structure}\n\n"

        "🎯 KEY LEVELS:\n"
        f"🔴 {lv['r1']} – {lv['r2']}\n"
        f"🟢 {lv['s1']} – {lv['s2']}\n\n"

        "⚠️ ANALYSIS ONLY — NO FINANCIAL ADVICE"
    )

# ==================================================
# HANDLER (FULL SAFE + DEBUG)
# ==================================================
async def photo_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):

    try:
        print("📸 PHOTO RECEIVED")

        await update.message.reply_text("📊 Processing MT5 screenshot...")

        img_bytes = await get_image(update, context)
        img = load(img_bytes)

        if img is None:
            await update.message.reply_text("❌ Image could not be read")
            return

        text = extract_text(img)

        pair = detect_pair(text)
        price = detect_price(text)
        structure = detect_structure(img)

        dt = now()

        msg = build(pair, price, structure, dt)

        await update.message.reply_text(msg)

    except Exception as e:

        print("HANDLER ERROR:", e)

        await update.message.reply_text(
            "❌ SYSTEM ERROR OCCURRED\n\n"
            f"{str(e)}"
        )

# ==================================================
# START
# ==================================================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    await update.message.reply_text(
        "🤖 SNIPER AI TRUTH ENGINE v10 ACTIVE\n\n"
        "Send MT5 screenshot (photo or file supported)."
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

    # VERY IMPORTANT: handles all image types reliably
    app.add_handler(
        MessageHandler(
            filters.PHOTO | filters.Document.IMAGE,
            photo_handler
        )
    )

    print("SNIPER AI v10 RUNNING")

    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
