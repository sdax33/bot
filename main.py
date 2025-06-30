import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, CallbackQueryHandler

# نحصل على التوكن من متغير البيئة
BOT_TOKEN = os.getenv("BOT_TOKEN")

# دالة تنفيذ أمر /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[InlineKeyboardButton("ابدأ التحليل 🔍", callback_data="analyze")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "مرحبًا بك في بوت تحليل الذهب 🟡\nاضغط الزر لتحليل السوق.",
        reply_markup=reply_markup
    )

# دالة تنفيذ التحليل (بشكل تجريبي الآن)
async def analyze_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    # تحليل تجريبي – لاحقًا نضيف التحليل الحقيقي
    await query.edit_message_text("📊 تحليل الذهب قيد التنفيذ...\n(هذا نموذج تجريبي، التحليل الحقيقي سيتم إضافته لاحقًا).")

# تشغيل البوت
if __name__ == '__main__':
    if BOT_TOKEN is None:
        raise ValueError("❌ لم يتم العثور على التوكن. تأكد من إضافة BOT_TOKEN إلى المتغيرات في Render.")

    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(analyze_callback))

    print("✅ البوت شغال الآن...")
    app.run_polling()
