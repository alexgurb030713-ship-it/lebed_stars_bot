import logging
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# ⚠️ ВСТАВЬТЕ СЮДА ВАШ ТОКЕН ОТ @BotFather (без пробелов)
BOT_TOKEN = "8552008796:AAHNDC_Xe6wUvHoE6HwO8DkU00hmhRI3EHU"

# ⚠️ ВСТАВЬТЕ ССЫЛКУ С RENDER (без / на конце)
WEB_APP_URL = "https://lebed-stars-bot.onrender.com"

logging.basicConfig(level=logging.INFO)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("⭐ Открыть LEBED stars", web_app=WebAppInfo(url=WEB_APP_URL))]
    ])
    await update.message.reply_text(
        "🔥 **Добро пожаловать в LEBED stars!**\n\n"
        "Открывайте кейсы, собирайте предметы и поднимайтесь в топ!",
        reply_markup=keyboard,
        parse_mode="Markdown"
    )

async def run_bot():
    if BOT_TOKEN == "8552008796:AAHNDC_Xe6wUvHoE6HwO8DkU00hmhRI3EHU":
        print("❌ ОШИБКА: Вы не заменили BOT_TOKEN в bot.py!")
        return

    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    
    print("🤖 Попытка запуска Telegram бота...")
    try:
        await app.initialize()
        await app.start()
        await app.updater.start_polling(drop_pending_updates=True)
        print("✅ Telegram бот успешно запущен и слушает команды!")
    except Exception as e:
        print(f"❌ Ошибка при запуске бота: {e}")