import os
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

TOKEN = os.getenv("BOT_TOKEN")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    async def signal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📊 SNIPER SIGNAL\n\n"
        "PAIR: XAUUSD\n"
        "TYPE: BUY\n"
        "ENTRY: 3300\n"
        "TP: 3310\n"
        "SL: 3290"
    )
    await update.message.reply_text("🤖 Bot is live!")

def main():
    if not TOKEN:
        print("ERROR: BOT_TOKEN is missing")
        return

    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("signal", signal))
    print("Bot starting...")
    app.run_polling()

if __name__ == "__main__":
    main()
