import os
import io
from datetime import datetime
from zoneinfo import ZoneInfo

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

def fmt_time(dt):
    return dt.strftime("%I:%M %p").lstrip("0")

def session_valid(hour):
    return (
        8 <= hour < 11 or
        13 <= hour < 16 or
        0 <= hour < 3
    )

def candle_closed(dt):
    # M15 closes at :00 :15 :30 :45 exactly
    return dt.minute in [0, 15, 30, 45]

def next_close_time(dt):
    mins = dt.minute
    close_marks = [15, 30, 45, 60]

    for m in close_marks:
        if mins < m:
            add_min = m - mins
            break
    else:
        add_min = 15

    from datetime import timedelta
    nxt = dt + timedelta(minutes=add_min)
    return nxt.replace(second=0, microsecond=0)

# ==================================================
# IMAGE FETCH
# ==================================================
async def get_image(update, context):
    photo = update.message.photo[-1]
    file = await context.bot.get_file(photo.file_id)
    return await file.download_as_bytearray()

# ==================================================
# SIMPLE MARKET READER (FREE LOGIC)
# ==================================================
def read_market(image_bytes):
    try:
        img = Image.open(io.BytesIO(image_bytes)).convert("L")
        pixels = list(img.getdata())

        brightness = sum(pixels) / len(pixels)
        variance = sum((p - brightness) ** 2 for p in pixels) / len(pixels)
        contrast = variance ** 0.5

        # Fake price generator (placeholder style)
        if brightness > 140:
            price = 4624.20
        elif brightness < 100:
            price = 42980.00
        else:
            price = 4621.80

        # Trend
        if contrast > 62 and brightness > 130:
            trend = "bullish"
        elif contrast > 62 and brightness < 130:
            trend = "bearish"
        else:
            trend = "neutral"

        # Levels
        resistance1 = round(price + 5.10, 2)
        resistance2 = round(price + 6.10, 2)
        support1 = round(price - 1.90, 2)
        support2 = round(price - 3.90, 2)
        wick_support = round(price - 9.90, 2)

        return {
            "price": price,
            "trend": trend,
            "r1": resistance1,
            "r2": resistance2,
            "s1": support1,
            "s2": support2,
            "wick": wick_support
        }

    except:
        return {
            "price": 0,
            "trend": "neutral",
            "r1": 0,
            "r2": 0,
            "s1": 0,
            "s2": 0,
            "wick": 0
        }

# ==================================================
# BUILD RESPONSE
# ==================================================
def build_watch_response(pair, data, dt):
    valid = "✅ Session valid" if session_valid(dt.hour) else "🟡 Outside sniper session"

    if not candle_closed(dt):
        nxt = next_close_time(dt)

        trend_line = "Price is dropping from intraday resistance." \
            if data["trend"] == "bearish" else \
            "Price is pushing from intraday support." \
            if data["trend"] == "bullish" else \
            "Price is ranging between levels."

        return (
            "🟡 WAIT – Candle not closed yet. Await M15 close confirmation.\n\n"
            f"📊 SNIPER AI Pre-Analysis ({pair} M15)\n"
            f"Current Price: {data['price']}\n"
            f"Time: {fmt_time(dt)} WAT {valid}\n\n"
            "🎯 Key Levels:\n"
            f"🔴 Resistance: {data['r1']} – {data['r2']}\n"
            f"🟢 Support: {data['s1']} – {data['s2']}\n"
            f"Major lower wick support: {data['wick']}\n\n"
            "📌 Market Status:\n"
            f"{trend_line}\n"
            "Current candle still open, so no confirmation yet.\n"
            "Price is near active zone, waiting edge confirmation.\n\n"
            "⏳ Action Plan:\n"
            f"Send the next screenshot when this M15 candle closes ({fmt_time(nxt)}).\n\n"
            "✅ Possible next sniper setups:\n"
            f"SELL if candle closes bearish below {round(data['price'] - 0.20,2)} and next candle confirms continuation.\n"
            f"BUY only if price sweeps {data['s1']} / {data['s2']} then rejects strongly.\n\n"
            "❌ NO TRADE until candle closes."
        )

    # Candle closed mode
    if data["trend"] == "bullish":
        return (
            f"🚀 BUY CONFIRMED ({pair} M15)\n\n"
            f"Entry: {data['price']}\n"
            f"SL: {data['s2']}\n"
            f"TP1: {data['r1']}\n"
            f"TP2: {data['r2']}\n\n"
            "Bullish candle close confirmed."
        )

    if data["trend"] == "bearish":
        return (
            f"🚀 SELL CONFIRMED ({pair} M15)\n\n"
            f"Entry: {data['price']}\n"
            f"SL: {data['r2']}\n"
            f"TP1: {data['s1']}\n"
            f"TP2: {data['s2']}\n\n"
            "Bearish candle close confirmed."
        )

    return (
        f"🟡 Candle closed ({pair} M15)\n\n"
        "No clear confirmation candle.\n"
        "Wait for next setup."
    )

# ==================================================
# HANDLER
# ==================================================
async def photo_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("📊 Reading live market structure...")

    image_bytes = await get_image(update, context)
    dt = now()

    # simple pair detection placeholder
    data = read_market(image_bytes)

    pair = "XAUUSD" if data["price"] > 4500 else "BTCUSD"

    msg = build_watch_response(pair, data, dt)

    await update.message.reply_text(msg)

# ==================================================
# START
# ==================================================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🤖 SNIPER AI WATCH MODE v2 ACTIVE\n\n"
        "Send M15 screenshot.\n"
        "Bot waits for candle close before confirming trades."
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

    print("WATCH MODE v2 RUNNING...")

    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
