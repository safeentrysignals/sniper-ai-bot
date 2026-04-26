import os
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

TOKEN = os.getenv("BOT_TOKEN")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🤖 Bot is live!")

def main():
    if not TOKEN:
        print("ERROR: BOT_TOKEN is missing")
        return

    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))

    print("Bot starting...")
    app.run_polling()

if __name__ == "__main__":
    main()
