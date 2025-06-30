from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, CallbackQueryHandler

import os

BOT_TOKEN = os.getenv("8169888968:AAFnPEROaUT3wdf4nZjJgy7BuAAwcV7JVXo")

# أمر /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[InlineKeyboardButton("ابدأ التحليل 🔍", callback_data="analyze")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("مرحباً 👋\nاضغط الزر لتحليل الذهب", reply_markup=reply_markup)

# عند الضغط على الزر
async def analyze_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    # هنا تقدر تضيف التحليل الحقيقي لاحقًا
    await query.edit_message_text("📊 تحليل الذهب قيد التنفيذ... (نموذج تجريبي)")

if __name__ == '__main__':
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(analyze_callback))

    print("Bot is running...")
    app.run_polling()
