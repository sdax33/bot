import os
import requests
import pandas as pd
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CallbackQueryHandler, ContextTypes, MessageHandler, filters

BOT_TOKEN = os.getenv("BOT_TOKEN")
TD_API_KEY = os.getenv("TD_API_KEY")

# قائمة الفترات الزمنية المتاحة
intervals = {
    "1min": "1 دقيقة",
    "15min": "15 دقيقة",
    "1h": "1 ساعة"
}

# واجهة البداية بزر
async def welcome_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[InlineKeyboardButton("ابدأ التحليل 📊", callback_data="select_interval")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("👋 مرحباً بك! اضغط على الزر للبدء.", reply_markup=reply_markup)

# اختيار الإطار الزمني
async def handle_callbacks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "select_interval":
        keyboard = [[InlineKeyboardButton(name, callback_data=key)] for key, name in intervals.items()]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text("🕒 اختر الإطار الزمني (الشمعة):", reply_markup=reply_markup)

    elif query.data in intervals:
        await query.edit_message_text(f"📡 جاري التحليل لـ {intervals[query.data]} ...")
        await analyze_gold(query, query.data)

# التحليل الفعلي
async def analyze_gold(query, interval="15min"):
    try:
        url = f"https://api.twelvedata.com/time_series?symbol=XAU/USD&interval={interval}&apikey={TD_API_KEY}&outputsize=30&format=JSON"
        res = requests.get(url)
        data = res.json()

        if "values" not in data:
            await query.edit_message_text("❌ لم يتم جلب بيانات السوق.")
            return

        df = pd.DataFrame(data["values"])
        df["close"] = df["close"].astype(float)
        df = df.sort_values(by="datetime")

        close_price = df.iloc[-1]["close"]
        ema = df["close"].ewm(span=20).mean().iloc[-1]
        rsi = calculate_rsi(df["close"])

        if close_price > ema and rsi < 70:
            decision = "شراء 🟢"
            stop = round(ema, 2)
            target = round(close_price + (close_price - ema), 2)
        elif close_price < ema and rsi > 30:
            decision = "بيع 🔴"
            stop = round(ema, 2)
            target = round(close_price - (ema - close_price), 2)
        else:
            decision = "محايد ⚪"
            stop = target = None

        msg = f"""📊 تحليل الذهب (XAU/USD) - إطار: {intervals[interval]}

🔸 السعر الحالي: {close_price:.2f}
📈 EMA20: {ema:.2f}
⚖️ RSI: {rsi:.2f}

🧭 التوصية: {decision}
🔹 دخول: {close_price:.2f}
{"🔻 وقف خسارة: " + str(stop) if stop else ""}
{"🎯 هدف: " + str(target) if target else ""}
        """

        await query.message.reply_text(msg)
    except Exception as e:
        await query.message.reply_text(f"⚠️ حصل خطأ أثناء التحليل: {e}")

def calculate_rsi(series, period=14):
    delta = series.diff().dropna()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs)).iloc[-1]

if __name__ == "__main__":
    if not BOT_TOKEN or not TD_API_KEY:
        raise Exception("❗ تأكد من وجود BOT_TOKEN وTD_API_KEY في متغيرات البيئة.")

    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, welcome_message))
    app.add_handler(CallbackQueryHandler(handle_callbacks))

    print("✅ البوت شغال الآن...")
    app.run_polling()
