import os
import io
import re
from datetime import datetime, timedelta
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
# IMAGE LOADER
# ==================================================
async def get_image(update, context):
    photo = update.message.photo[-1]
    file = await context.bot.get_file(photo.file_id)
    return await file.download_as_bytearray()

def load(img_bytes):
    arr = np.frombuffer(img_bytes, np.uint8)
    return cv2.imdecode(arr, cv2.IMREAD_COLOR)

# ==================================================
# OCR ENGINE (REAL DATA ONLY)
# ==================================================
def extract_text(img):
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    return pytesseract.image_to_string(gray).upper()

# ==================================================
# SAFE PAIR DETECTION
# ==================================================
def detect_pair(text):
    if "XAU" in text:
        return "XAUUSD"
    if "BTC" in text:
        return "BTCUSD"
    return "UNKNOWN"

# ==================================================
# SAFE PRICE EXTRACTION
# ==================================================
def detect_price(text):

    matches = re.findall(r"\d+\.\d+", text)

    if not matches:
        return None

    # take most reasonable number (avoid garbage OCR)
    for m in matches:
        val = float(m)
        if 1000 < val < 100000:
            return val

    return None

# ==================================================
# STRUCTURE ENGINE (NO SIGNAL PROMISES)
# ==================================================
def detect_structure(img):

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

# ==================================================
# LEVELS (ONLY IF PRICE EXISTS)
# ==================================================
def levels(price):

    return {
        "r1": round(price + 2, 2),
        "r2": round(price + 4, 2),
        "s1": round(price - 2, 2),
        "s2": round(price - 4, 2),
    }

# ==================================================
# RESPONSE BUILDER (NO FAKE SIGNALS)
# ==================================================
def build(pair, price, structure, dt):

    session = "✅ Session valid" if session_ok(dt.hour) else "🟡 Outside session"

    if pair == "UNKNOWN" or price is None:

        return (
            "❌ INSUFFICIENT DATA\n\n"
            "Bot could not reliably read:\n"
            "- Pair (XAUUSD / BTCUSD)\n"
            "- Price level\n\n"
            "📌 Solution:\n"
            "Send clearer MT5 screenshot (zoomed chart + visible price scale)."
        )

    lv = levels(price)

    return (
        f"📊 SNIPER AI TRUTH ENGINE v8\n\n"
        f"PAIR: {pair}\n"
        f"PRICE: {price}\n"
        f"TIME: {fmt(dt)} WAT {session}\n\n"

        "📌 MARKET STRUCTURE:\n"
        f"{structure}\n\n"

        "🎯 KEY LEVELS:\n"
        f"🔴 Resistance: {lv['r1']} – {lv['r2']}\n"
        f"🟢 Support: {lv['s1']} – {lv['s2']}\n\n"

        "⚠️ NOTE:\n"
        "This is analysis only. No trade signal is guaranteed.\n"
    )

# ==================================================
# HANDLER
# ==================================================
async def photo_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):

    await update.message.reply_text("📊 Reading MT5 screenshot (TRUTH MODE)...")

    img = load(await get_image(update, context))
    text = extract_text(img)

    pair = detect_pair(text)
    price = detect_price(text)
    structure = detect_structure(img)

    dt = now()

    msg = build(pair, price, structure, dt)

    await update.message.reply_text(msg)

# ==================================================
# START
# ==================================================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    await update.message.reply_text(
        "🤖 SNIPER AI TRUTH ENGINE v8 ACTIVE\n\n"
        "Send MT5 screenshot.\n"
        "This version only gives REAL readable analysis — no fake signals."
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

    print("TRUTH ENGINE RUNNING")

    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
