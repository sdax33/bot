import os
import requests
import pandas as pd
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, CallbackQueryHandler

BOT_TOKEN = os.getenv("BOT_TOKEN")
TD_API_KEY = os.getenv("TD_API_KEY")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[InlineKeyboardButton("ابدأ التحليل 🔍", callback_data="analyze")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("👋 أهلاً! اضغط الزر لتحليل الذهب.", reply_markup=reply_markup)

async def analyze_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    url = f"https://api.twelvedata.com/time_series?symbol=XAU/USD&interval=15min&apikey={TD_API_KEY}&outputsize=20&format=JSON"
    
    try:
        res = requests.get(url)
        data = res.json()

        if "values" not in data:
            await query.edit_message_text("❌ خطأ في جلب البيانات من TwelveData.")
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

        msg = f"""📊 تحليل الذهب (XAU/USD) - 15 دقيقة

🔸 السعر الحالي: {close_price:.2f}
📈 EMA20: {ema:.2f}
⚖️ RSI: {rsi:.2f}

🧭 التوصية: {decision}
🔹 دخول: {close_price:.2f}
{"🔻 وقف: " + str(stop) if stop else ""}
{"🎯 هدف: " + str(target) if target else ""}
        """

        await query.edit_message_text(msg)
    except Exception as e:
        await query.edit_message_text(f"⚠️ حصل خطأ: {e}")

def calculate_rsi(series, period=14):
    delta = series.diff().dropna()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs)).iloc[-1]

if __name__ == "__main__":
    if not BOT_TOKEN or not TD_API_KEY:
        raise Exception("❗ تأكد من وجود BOT_TOKEN وTD_API_KEY في البيئة.")

    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(analyze_callback))
    
    print("✅ البوت شغال الآن...")
    app.run_polling()
