import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, CallbackQueryHandler

# 🛡️ نحصل على التوكن من متغير بيئة
BOT_TOKEN = os.getenv("BOT_TOKEN")

# ✅ دالة الأمر /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[InlineKeyboardButton("ابدأ التحليل 🔍", callback_data="analyze")]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        "👋 أهلاً بك في بوت تحليل الذهب 🟡\nاضغط الزر أدناه لتحليل السوق.",
        reply_markup=reply_markup
    )

# ✅ دالة عند الضغط على الزر
async def analyze_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query

    # ضروري ترد على الضغط بسرعة حتى لو بدون محتوى
    try:
        await query.answer()
    except Exception as e:
        print(f"❗ خطأ في الرد على الزر: {e}")

    # تحليل مبدئي – يمكنك تعديله لاحقاً
    await query.edit_message_text(
        text="📊 تحليل الذهب قيد التنفيذ...\n\n"
             "🔍 الإطار الزمني: 15 دقيقة\n"
             "🟢 التوصية: شراء (تجريبية)\n"
             "✅ المنطقة: 2310 - 2312\n"
             "🎯 الهدف: 2320\n"
             "🛑 وقف الخسارة: 2305\n"
             "📌 ملاحظة: يعتمد على نموذج شمعة بن بار + تقاطع RSI"
    )

# ✅ بدء التشغيل
if __name__ == '__main__':
    if not BOT_TOKEN:
        raise ValueError("❌ التوكن غير موجود! تأكد من أنك أضفت BOT_TOKEN في Railway.")

    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(analyze_callback))

    print("✅ البوت شغال الآن...")
    app.run_polling()
