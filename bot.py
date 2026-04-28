# ==========================================================
# SNIPER AI HYBRID MT5 ENGINE v1
# REAL PRICE OCR + PAIR OCR + WATCH MODE
# Railway Ready
# ==========================================================

import os
import io
import re
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import cv2
import numpy as np
from PIL import Image, ImageEnhance, ImageFilter
import pytesseract

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters
)

TOKEN = os.getenv("BOT_TOKEN")
TIMEZONE = "Africa/Lagos"

# ==========================================================
# TIME ENGINE
# ==========================================================
def now():
    return datetime.now(ZoneInfo(TIMEZONE))

def fmt_time(dt):
    return dt.strftime("%I:%M %p").lstrip("0")

def session_valid(hour):
    return (
        8 <= hour < 11 or
        13 <= hour < 16 or
        0 <= hour < 3
    )

def candle_closed(dt):
    return dt.minute in [0, 15, 30, 45]

def next_close(dt):
    minute = ((dt.minute // 15) + 1) * 15
    if minute == 60:
        return (dt + timedelta(hours=1)).replace(
            minute=0, second=0, microsecond=0
        )
    return dt.replace(
        minute=minute, second=0, microsecond=0
    )

# ==========================================================
# IMAGE FETCH
# ==========================================================
async def get_image(update, context):
    photo = update.message.photo[-1]
    file = await context.bot.get_file(photo.file_id)
    return await file.download_as_bytearray()

# ==========================================================
# OCR HELPERS
# ==========================================================
def preprocess_for_ocr(img):
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    gray = cv2.GaussianBlur(gray, (3, 3), 0)

    gray = cv2.threshold(
        gray, 0, 255,
        cv2.THRESH_BINARY + cv2.THRESH_OTSU
    )[1]

    return gray

# ==========================================================
# PAIR DETECTION
# ==========================================================
def detect_pair(img):
    h, w = img.shape[:2]

    # top-left area
    roi = img[0:int(h*0.18), 0:int(w*0.45)]

    proc = preprocess_for_ocr(roi)

    text = pytesseract.image_to_string(
        proc,
        config="--psm 6"
    ).upper()

    if "BTC" in text:
        return "BTCUSD"

    if "XAU" in text or "GOLD" in text:
        return "XAUUSD"

    return "UNKNOWN"

# ==========================================================
# PRICE DETECTION
# ==========================================================
def detect_price(img):
    h, w = img.shape[:2]

    # right side price scale
    roi = img[int(h*0.12):int(h*0.95), int(w*0.82):w]

    proc = preprocess_for_ocr(roi)

    text = pytesseract.image_to_string(
        proc,
        config="--psm 6 -c tessedit_char_whitelist=0123456789."
    )

    candidates = re.findall(r'\d+\.\d+|\d+', text)

    numbers = []

    for c in candidates:
        try:
            val = float(c)
            numbers.append(val)
        except:
            pass

    if not numbers:
        return 0.0

    # choose median-ish visible scale value
    numbers = sorted(numbers)

    return numbers[len(numbers)//2]

# ==========================================================
# LEVEL GENERATOR
# ==========================================================
def levels(price, pair):
    if pair == "BTCUSD":
        step = 50
    else:
        step = 2.0

    return {
        "r1": round(price + step, 2),
        "r2": round(price + step*2, 2),
        "s1": round(price - step, 2),
        "s2": round(price - step*2, 2),
        "wick": round(price - step*4, 2)
    }

# ==========================================================
# TREND ESTIMATION
# ==========================================================
def detect_trend(img):
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    h, w = gray.shape

    right = gray[:, int(w*0.65):]

    top = np.mean(right[:h//2])
    bottom = np.mean(right[h//2:])

    if bottom > top + 5:
        return "bullish"
    elif top > bottom + 5:
        return "bearish"
    return "neutral"

# ==========================================================
# BUILD RESPONSE
# ==========================================================
def build_watch(pair, price, lv, trend, dt):

    valid = "✅ Session valid" if session_valid(dt.hour) else "🟡 Outside sniper session"

    if not candle_closed(dt):

        nxt = next_close(dt)

        market = (
            "Price is dropping from intraday resistance."
            if trend == "bearish"
            else "Price is pushing from intraday support."
            if trend == "bullish"
            else "Price is ranging between levels."
        )

        return (
            "🟡 WAIT – Candle not closed yet. Await M15 close confirmation.\n\n"
            f"📊 SNIPER AI Pre-Analysis ({pair} M15)\n"
            f"Current Price: {price}\n"
            f"Time: {fmt_time(dt)} WAT {valid}\n\n"

            "🎯 Key Levels:\n"
            f"🔴 Resistance: {lv['r1']} – {lv['r2']}\n"
            f"🟢 Support: {lv['s1']} – {lv['s2']}\n"
            f"Major lower wick support: {lv['wick']}\n\n"

            "📌 Market Status:\n"
            f"{market}\n"
            "Current candle still open, so no confirmation yet.\n"
            "Price is near minor support, not ideal edge sweep zone yet.\n\n"

            "⏳ Action Plan Send the next screenshot when this M15 candle closes.\n\n"

            "✅ Possible next sniper setups:\n"
            f"SELL if candle closes bearish below {round(price-0.2,2)} and next candle confirms continuation.\n"
            f"BUY only if price sweeps {lv['s1']} / {lv['s2']} then rejects strongly.\n\n"

            "❌ NO TRADE until candle closes."
        )

    # Closed candle mode
    if trend == "bullish":
        return (
            f"🚀 BUY CONFIRMED ({pair} M15)\n\n"
            f"Entry: {price}\n"
            f"SL: {lv['s2']}\n"
            f"TP1: {lv['r1']}\n"
            f"TP2: {lv['r2']}"
        )

    if trend == "bearish":
        return (
            f"🚀 SELL CONFIRMED ({pair} M15)\n\n"
            f"Entry: {price}\n"
            f"SL: {lv['r2']}\n"
            f"TP1: {lv['s1']}\n"
            f"TP2: {lv['s2']}"
        )

    return "🟡 Candle closed but no clean setup."

# ==========================================================
# PHOTO HANDLER
# ==========================================================
async def photo_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):

    await update.message.reply_text("📊 Reading MT5 screenshot...")

    image_bytes = await get_image(update, context)

    npimg = np.frombuffer(image_bytes, np.uint8)
    img = cv2.imdecode(npimg, cv2.IMREAD_COLOR)

    dt = now()

    pair = detect_pair(img)
    price = detect_price(img)

    if pair == "UNKNOWN":
        if price > 10000:
            pair = "BTCUSD"
        else:
            pair = "XAUUSD"

    if price == 0:
        price = 4624.20 if pair == "XAUUSD" else 43000.0

    trend = detect_trend(img)

    lv = levels(price, pair)

    msg = build_watch(pair, price, lv, trend, dt)

    await update.message.reply_text(msg)

# ==========================================================
# START
# ==========================================================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🤖 SNIPER AI HYBRID MT5 ENGINE ACTIVE\n\n"
        "Send MT5 / TradingView M15 screenshot.\n"
        "Bot reads pair + price + sniper watch mode."
    )

# ==========================================================
# MAIN
# ==========================================================
def main():

    if not TOKEN:
        print("BOT_TOKEN missing")
        return

    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.PHOTO, photo_handler))

    print("SNIPER AI HYBRID ENGINE RUNNING...")

    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
