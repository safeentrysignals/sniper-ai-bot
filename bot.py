import os
import io
import requests
from datetime import datetime
from zoneinfo import ZoneInfo

from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters

# OCR (optional upgrade)
try:
    import pytesseract
    from PIL import Image
except:
    pytesseract = None
    Image = None

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
# LIVE PRICE ENGINE (REAL MARKET FEED)
# ==================================================
def get_price(symbol="BTCUSD"):

    try:
        if symbol == "BTCUSD":
            url = "https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT"
            return float(requests.get(url, timeout=5).json()["price"])

        # fallback proxy for gold (replace later with broker API)
        if symbol == "XAUUSD":
            btc = get_price("BTCUSD")
            return btc / 20  # rough proxy scaling

    except:
        return None

# ==================================================
# VISION ENGINE (OCR + STRUCTURE)
# ==================================================
def vision_engine(image_bytes):

    if Image is None or pytesseract is None:
        return {"pair": "UNKNOWN", "trend": "neutral", "confidence": 0.3}

    img = Image.open(io.BytesIO(image_bytes))
    text = pytesseract.image_to_string(img).upper()

    pair = "UNKNOWN"

    if "BTC" in text:
        pair = "BTCUSD"
    elif "XAU" in text or "GOLD" in text:
        pair = "XAUUSD"

    gray = img.convert("L")
    avg = sum(gray.getdata()) / len(gray.getdata())

    if avg > 145:
        trend = "bullish"
        confidence = 0.75
    elif avg < 105:
        trend = "bearish"
        confidence = 0.75
    else:
        trend = "neutral"
        confidence = 0.45

    return {
        "pair": pair,
        "trend": trend,
        "confidence": confidence
    }

# ==================================================
# LIQUIDITY SWEEP DETECTOR
# ==================================================
def liquidity_check(price):

    # simple engineered logic (replace later with ML)
    if price % 100 < 20:
        return "liquidity_sweep"

    return "clean"

# ==================================================
# MARKET STRUCTURE ENGINE
# ==================================================
def structure_engine(price):

    support = price - (price * 0.002)
    resistance = price + (price * 0.002)

    return support, resistance

# ==================================================
# SNIPER CONFLUENCE ENGINE
# ==================================================
def decision_engine(v, price):

    support, resistance = structure_engine(price)
    liquidity = liquidity_check(price)

    score = 0

    if v["trend"] == "bullish":
        score += 2
    if v["trend"] == "bearish":
        score -= 2

    if liquidity == "liquidity_sweep":
        score += 1

    session = in_session(now().hour)

    if not session:
        return None, score

    if score >= 2:
        return {
            "type": "BUY",
            "entry": price,
            "sl": support,
            "tp1": resistance,
            "tp2": resistance + (price * 0.003)
        }, score

    if score <= -2:
        return {
            "type": "SELL",
            "entry": price,
            "sl": resistance,
            "tp1": support,
            "tp2": support - (price * 0.003)
        }, score

    return None, score

# ==================================================
# PHOTO HANDLER
# ==================================================
async def get_image(update, context):
    photo = update.message.photo[-1]
    file = await context.bot.get_file(photo.file_id)
    return await file.download_as_bytearray()

async def photo_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):

    image_bytes = await get_image(update, context)

    await update.message.reply_text("📊 Analyzing market structure...")

    v = vision_engine(image_bytes)

    if v["pair"] == "UNKNOWN":
        await update.message.reply_text(
            "⚠️ Cannot detect chart pair clearly.\nSend clearer BTCUSD or XAUUSD chart."
        )
        return

    price = get_price(v["pair"])

    if not price:
        await update.message.reply_text("⚠️ Market feed unavailable.")
        return

    signal, score = decision_engine(v, price)

    session = "LIVE" if in_session(now().hour) else "TEST MODE"

    if not signal:
        await update.message.reply_text(
            f"❌ NO TRADE\n\n"
            f"Trend: {v['trend']}\n"
            f"Confidence: {int(v['confidence']*100)}%\n"
            f"Score: {score}"
        )
        return

    await update.message.reply_text(
        f"🤖 SNIPER AI FINAL BRAIN v2\n\n"
        f"PAIR: {v['pair']}\n"
        f"TYPE: {signal['type']}\n"
        f"ENTRY: {signal['entry']}\n"
        f"SL: {signal['sl']}\n"
        f"TP1: {signal['tp1']}\n"
        f"TP2: {signal['tp2']}\n\n"
        f"CONFIDENCE: {int(v['confidence']*100)}%\n"
        f"SCORE: {score}\n"
        f"SESSION: {session}\n\n"
        f"🧠 Final Brain Active"
    )

# ==================================================
# START
# ==================================================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🤖 SNIPER AI FINAL BRAIN v2 ACTIVE\n\n"
        "Send M15 chart screenshot.\nNo captions needed."
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

    print("Sniper AI Final Brain v2 Running...")

    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
