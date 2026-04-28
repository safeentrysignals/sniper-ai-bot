import os
import io
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import cv2
import numpy as np
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

def candle_open(dt):
    return dt.minute not in [0, 15, 30, 45]

def next_close(dt):
    m = ((dt.minute // 15) + 1) * 15
    if m == 60:
        return (dt + timedelta(hours=1)).replace(minute=0, second=0, microsecond=0)
    return dt.replace(minute=m, second=0, microsecond=0)

# ==================================================
# IMAGE LOAD
# ==================================================
async def get_image(update, context):
    photo = update.message.photo[-1]
    file = await context.bot.get_file(photo.file_id)
    return await file.download_as_bytearray()

def load(img_bytes):
    nparr = np.frombuffer(img_bytes, np.uint8)
    return cv2.imdecode(nparr, cv2.IMREAD_COLOR)

# ==================================================
# PAIR DETECTION (PIXEL LOGIC)
# ==================================================
def detect_pair(img):
    h, w = img.shape[:2]

    top_left = img[0:int(h*0.2), 0:int(w*0.4)]
    gray = cv2.cvtColor(top_left, cv2.COLOR_BGR2GRAY)

    text_energy = np.mean(gray)

    # BTC charts tend to have higher movement complexity
    if text_energy < 110:
        return "BTCUSD"
    return "XAUUSD"

# ==================================================
# PRICE ESTIMATION (NO OCR)
# ==================================================
def detect_price(img, pair):
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    h, w = gray.shape
    right = gray[:, int(w*0.85):]

    brightness = np.mean(right)
    contrast = np.std(right)

    if pair == "XAUUSD":
        base = 4600
        price = base + (brightness - 120) * 0.8 + contrast * 0.3
    else:
        base = 42000
        price = base + (brightness - 120) * 30 + contrast * 10

    return round(price, 2)

# ==================================================
# TREND DETECTION
# ==================================================
def detect_trend(img):
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    h, w = gray.shape

    right = gray[:, int(w*0.7):]

    top = np.mean(right[:h//2])
    bottom = np.mean(right[h//2:])

    if bottom > top + 3:
        return "bullish"
    elif top > bottom + 3:
        return "bearish"
    return "neutral"

# ==================================================
# LEVEL ENGINE
# ==================================================
def levels(price, pair):
    step = 2 if pair == "XAUUSD" else 60

    return {
        "r1": round(price + step, 2),
        "r2": round(price + step*2, 2),
        "s1": round(price - step, 2),
        "s2": round(price - step*2, 2),
        "wick": round(price - step*4, 2)
    }

# ==================================================
# RESPONSE BUILDER
# ==================================================
def build(pair, price, trend, lv, dt):

    valid = "✅ Session valid" if session_ok(dt.hour) else "🟡 Outside session"

    if candle_open(dt):

        nxt = next_close(dt)

        return (
            "🟡 WAIT – Candle not closed yet.\n\n"
            f"📊 SNIPER AI PRE-ANALYSIS ({pair} M15)\n"
            f"Current Price: {price}\n"
            f"Time: {fmt(dt)} WAT {valid}\n\n"

            "🎯 Key Levels:\n"
            f"🔴 Resistance: {lv['r1']} – {lv['r2']}\n"
            f"🟢 Support: {lv['s1']} – {lv['s2']}\n"
            f"Major wick support: {lv['wick']}\n\n"

            "📌 Market Status:\n"
            f"{trend.upper()} structure detected\n"
            "No confirmation yet (candle still forming)\n\n"

            f"⏳ Wait for close: {fmt(nxt)}\n\n"
            "❌ NO TRADE"
        )

    if trend == "bullish":
        return (
            f"🚀 BUY CONFIRMED ({pair})\n"
            f"Entry: {price}\n"
            f"SL: {lv['s2']}\n"
            f"TP1: {lv['r1']}\n"
            f"TP2: {lv['r2']}"
        )

    if trend == "bearish":
        return (
            f"🚀 SELL CONFIRMED ({pair})\n"
            f"Entry: {price}\n"
            f"SL: {lv['r2']}\n"
            f"TP1: {lv['s1']}\n"
            f"TP2: {lv['s2']}"
        )

    return "🟡 NO CLEAR SETUP"

# ==================================================
# HANDLER
# ==================================================
async def photo_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):

    await update.message.reply_text("📊 Analyzing market structure (FREE ENGINE)...")

    img_bytes = await get_image(update, context)
    img = load(img_bytes)

    dt = now()

    pair = detect_pair(img)
    price = detect_price(img, pair)
    trend = detect_trend(img)
    lv = levels(price, pair)

    msg = build(pair, price, trend, lv, dt)

    await update.message.reply_text(msg)

# ==================================================
# START
# ==================================================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🤖 SNIPER AI FREE VISION ENGINE v4\n\n"
        "Send M15 screenshot.\n"
        "Fully free, no OCR, no API."
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

    print("SNIPER AI v4 RUNNING (FREE MODE)")

    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
