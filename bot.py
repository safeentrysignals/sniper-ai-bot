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

def candle_window(now):
    """
    Returns:
    start_minute, end_minute, close_minute
    """

    minute = now.minute

    if 0 <= minute < 15:
        return 0, 14, 15

    if 15 <= minute < 30:
        return 15, 29, 30

    if 30 <= minute < 45:
        return 30, 44, 45

    return 45, 59, 60

def next_close_time(now):
    hour = now.hour
    minute = now.minute

    _, _, close_min = candle_window(now)

    if close_min == 60:
        close_hour = (hour + 1) % 24
        close_min = 0
    else:
        close_hour = hour

    return close_hour, close_min

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
# PLACEHOLDER VISION
# ==================================================
def analyze_chart_image(_image_bytes):
    return {
        "trend": "bullish",
        "price": 43000,
        "support": 42850,
        "resistance": 43250
    }

# ==================================================
# PLACEHOLDER PATTERN
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
        "🤖 SNIPER AI WATCH MODE ACTIVE\n\n"
        "Send M15 screenshot with caption:\n"
        "BTCUSD or XAUUSD"
    )

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📸 Upload M15 chart screenshot.\n"
        "Use caption:\nBTCUSD or XAUUSD\n\n"
        "Bot will analyze current candle and request confirmation screenshot at close."
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

    await update.message.reply_text("📊 Screenshot received. Reading M15 candle...")

    # Download photo
    photo = update.message.photo[-1]
    file = await context.bot.get_file(photo.file_id)
    image_bytes = await file.download_as_bytearray()

    # Analyze placeholders
    vision = analyze_chart_image(image_bytes)
    pattern = detect_pattern(vision)
    signal = generate_signal(pair, vision, pattern)

    # Time window
    start_m, end_m, _ = candle_window(now)
    close_h, close_m = next_close_time(now)

    # Session status
    if in_session(hour):
        session_text = "🟢 LIVE SESSION"
    else:
        session_text = "🟡 Outside sniper session"

    # WATCH MODE (unfinished candle)
    await update.message.reply_text(
        f"🤖 SNIPER AI WATCH MODE\n\n"
        f"{session_text}\n\n"
        f"PAIR: {pair}\n"
        f"Current Candle: {now.hour:02d}:{start_m:02d} - {now.hour:02d}:{end_m:02d}\n\n"
        f"Bias: {signal['type']} Watch\n"
        f"Pattern Forming: {signal['pattern']}\n\n"
        f"Price Watch Level: {signal['entry']}\n"
        f"TP Zone: {signal['tp1']} / {signal['tp2']}\n\n"
        f"⏳ Candle still open.\n"
        f"Send new screenshot at {close_h:02d}:{close_m:02d} for confirmation."
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

    print("Sniper AI Watch Mode running...")

    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
