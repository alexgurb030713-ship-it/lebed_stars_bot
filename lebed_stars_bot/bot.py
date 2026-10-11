import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# Замените на ваш токен от @BotFather
BOT_TOKEN = "8552008796:AAHNDC_Xe6wUvHoE6HwO8DkU00hmhRI3EHU"

# Ваша ссылка с Render (или локальная ссылка для тестов)
WEB_APP_URL = "https://lebed-stars-bot.onrender.com"

logging.basicConfig(level=logging.INFO)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("⭐ Открыть LEBED stars", web_app=WebAppInfo(url=WEB_APP_URL))]
    ])
    await update.message.reply_text(
        "🔥 Добро пожаловать в **LEBED stars**!\n\n"
        "Открывайте ежедневные кейсы, выбивайте ценные предметы и поднимайтесь в топ лидеров по звёздам!",
        reply_markup=keyboard,
        parse_mode="Markdown"
    )

if __name__ == "__main__":
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    print("Бот запущен...")
    app.run_polling()