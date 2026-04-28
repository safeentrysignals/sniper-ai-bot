import os
import base64
import json
from datetime import datetime
from zoneinfo import ZoneInfo

import requests
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters

TOKEN = os.getenv("BOT_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

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
# 🧠 SAFE VISION AI ENGINE (FIXED)
# ==================================================
def vision_ai(image_bytes):

    if not OPENAI_API_KEY:
        return {
            "pair": "UNKNOWN",
            "trend": "neutral",
            "pattern": "no_api_key",
            "support": 0,
            "resistance": 0,
            "confidence": 0.2
        }

    base64_img = base64.b64encode(image_bytes).decode("utf-8")

    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": "gpt-4o",
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": """
You are a professional trading analyst.

Analyze this M15 chart and return ONLY valid JSON:

{
  "pair": "BTCUSD or XAUUSD",
  "trend": "bullish or bearish or neutral",
  "pattern": "candlestick pattern",
  "support": number,
  "resistance": number,
  "confidence": number between 0 and 1
}
"""
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/png;base64,{base64_img}"
                        }
                    }
                ]
            }
        ],
        "temperature": 0.2
    }

    try:
        res = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers=headers,
            json=payload,
            timeout=30
        )

        data = res.json()

        # ===========================
        # HARD ERROR HANDLING
        # ===========================
        if "error" in data:
            return {
                "pair": "UNKNOWN",
                "trend": "neutral",
                "pattern": f"openai_error: {data['error'].get('message', 'unknown')}",
                "support": 0,
                "resistance": 0,
                "confidence": 0.3
            }

        if "choices" not in data:
            return {
                "pair": "UNKNOWN",
                "trend": "neutral",
                "pattern": "no_choices_returned",
                "support": 0,
                "resistance": 0,
                "confidence": 0.3
            }

        content = data["choices"][0]["message"]["content"]

        # CLEAN RESPONSE
        content = content.strip().replace("```json", "").replace("```", "")

        return json.loads(content)

    except Exception as e:

        print("VISION ERROR:", str(e))

        return {
            "pair": "UNKNOWN",
            "trend": "neutral",
            "pattern": f"exception: {str(e)}",
            "support": 0,
            "resistance": 0,
            "confidence": 0.3
        }

# ==================================================
# SIGNAL ENGINE
# ==================================================
def signal_engine(v):

    if not v.get("support") or not v.get("resistance"):
        return None

    price = (v["support"] + v["resistance"]) / 2

    if v["trend"] == "bullish":
        return {
            "type": "BUY",
            "entry": price,
            "sl": v["support"],
            "tp1": v["resistance"],
            "tp2": v["resistance"] + (price * 0.002)
        }

    if v["trend"] == "bearish":
        return {
            "type": "SELL",
            "entry": price,
            "sl": v["resistance"],
            "tp1": v["support"],
            "tp2": v["support"] - (price * 0.002)
        }

    return None

# ==================================================
# HANDLER
# ==================================================
async def photo_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):

    image_bytes = await get_image(update, context)

    await update.message.reply_text("📊 Sending to AI Vision Brain...")

    v = vision_ai(image_bytes)

    signal = signal_engine(v)

    session = "LIVE" if in_session(now().hour) else "TEST MODE"

    if not signal:
        await update.message.reply_text(
            f"❌ NO TRADE\n\n"
            f"Pattern: {v.get('pattern')}\n"
            f"Confidence: {v.get('confidence')}"
        )
        return

    await update.message.reply_text(
        "🤖 SNIPER AI VISION ENGINE v5\n\n"
        f"PAIR: {v.get('pair')}\n"
        f"TYPE: {signal['type']}\n"
        f"PATTERN: {v.get('pattern')}\n"
        f"CONFIDENCE: {v.get('confidence')}\n\n"
        f"ENTRY: {signal['entry']}\n"
        f"SL: {signal['sl']}\n"
        f"TP1: {signal['tp1']}\n"
        f"TP2: {signal['tp2']}\n\n"
        f"SESSION: {session}\n"
        "🧠 GPT-4o Vision Active"
    )

# ==================================================
# START COMMAND
# ==================================================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    await update.message.reply_text(
        "🤖 SNIPER AI VISION ENGINE ACTIVE\n\n"
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

    print("Sniper AI Vision Engine Running...")

    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
