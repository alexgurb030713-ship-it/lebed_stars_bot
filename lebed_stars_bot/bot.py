import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

BOT_TOKEN = "8552008796:AAHNDC_Xe6wUvHoE6HwO8DkU00hmhRI3EHU"
WEB_APP_URL = "https://lebed-stars-bot.onrender.com"

logging.basicConfig(level=logging.INFO)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("⭐ Открыть LEBED stars", web_app=WebAppInfo(url=WEB_APP_URL))]
    ])
    await update.message.reply_text(
        "🔥 **Добро пожаловать в LEBED stars!**\n\nОткрывайте кейсы и собирайте предметы!",
        reply_markup=keyboard,
        parse_mode="Markdown"
    )

def get_bot_application():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    return app