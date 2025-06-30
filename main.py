import os
import requests
import pandas as pd
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CallbackQueryHandler, ContextTypes, MessageHandler, filters

BOT_TOKEN = os.getenv("BOT_TOKEN")
TD_API_KEY = os.getenv("TD_API_KEY")

intervals = {"5min": "5 دقائق", "15min": "15 دقيقة", "1h": "1 ساعة"}

async def welcome_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[InlineKeyboardButton("ابدأ التحليل 📊", callback_data="select_interval")]]
    await update.message.reply_text("👋 أهلاً! اضغط الزر للبدء.", reply_markup=InlineKeyboardMarkup(keyboard))

async def handle_callbacks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data == "select_interval":
        keyboard = [[InlineKeyboardButton(name, callback_data=key)] for key, name in intervals.items()]
        await query.edit_message_text("🕒 اختر الإطار الزمني:", reply_markup=InlineKeyboardMarkup(keyboard))
    elif query.data in intervals:
        await query.edit_message_text(f"📡 جاري تحليل الذهب لإطار {intervals[query.data]}...")
        await analyze_gold(query, query.data)

async def analyze_gold(query, interval):
    try:
        url = f"https://api.twelvedata.com/time_series?symbol=XAU/USD&interval={interval}&apikey={TD_API_KEY}&outputsize=50&format=JSON"
        res = requests.get(url)
        data = res.json()
        if "values" not in data:
            raise Exception("لم أتمكن من جلب بيانات السوق.")
        df = pd.DataFrame(data["values"])
        df["close"] = df["close"].astype(float)
        df = df.sort_values(by="datetime")
        close = df.iloc[-1]["close"]
        ema20 = df["close"].ewm(span=20).mean().iloc[-1]
        rsi = calc_rsi(df["close"])
        macd_line, signal = calc_macd(df["close"])
        exp = []

        exp.append(f"🔸 السعر الحالي: {close:.2f}")
        exp.append(f"📈 EMA20: {ema20:.2f}")
        exp.append(f"⚖️ RSI: {rsi:.2f}")
        exp.append(f"📊 MACD: {macd_line:.4f}, Signal: {signal:.4f}\n")

        decision = "انتظار ⚪"
        if close > ema20 and rsi < 70 and macd_line > signal:
            decision = "شراء 🟢"
            stop = round(ema20, 2)
            target = round(close + (close - ema20), 2)
            exp += [
                "✅ السعر أعلى EMA20 → اتجاه صاعد.",
                "✅ RSI أقل من 70 → لا يوجد تشبع شراء.",
                "✅ MACD فوق الإشارة → تقاطع إيجابي.",
                f"🔻 وقف خسارة: {stop}",
                f"🎯 الهدف: {target}"
            ]
        elif close < ema20 and rsi > 30 and macd_line < signal:
            decision = "بيع 🔴"
            stop = round(ema20, 2)
            target = round(close - (ema20 - close), 2)
            exp += [
                "⚠️ السعر أقل من EMA20 → اتجاه هابط.",
                "⚠️ RSI أكبر من 30 → لا يوجد تشبع بيع.",
                "⚠️ MACD تحت الإشارة → تقاطع سلبي.",
                f"🔻 وقف خسارة: {stop}",
                f"🎯 الهدف: {target}"
            ]
        else:
            exp += [
                "ℹ️ الوضع غير واضح:",
                ("- السعر قريب من EMA20 أو RSI أو MACD لا يعطي توصية واضحة."),
                "📌 التوصية: الانتظار حتى تتضح المؤشرات."
            ]

        message = f"📊 تحليل الذهب ({intervals[interval]})\n\n" + "\n".join(exp) + f"\n\n🧭 التوصية النهائية: {decision}"
        await query.message.reply_text(message)
    except Exception as e:
        await query.message.reply_text(f"⚠️ خطأ أثناء التحليل: {e}")

def calc_rsi(series, period=14):
    delta = series.diff().dropna()
    gain = delta.where(delta > 0, 0).rolling(period).mean()
    loss = -delta.where(delta < 0, 0).rolling(period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs)).iloc[-1]

def calc_macd(series, fast=12, slow=26, signal_period=9):
    exp1 = series.ewm(span=fast).mean()
    exp2 = series.ewm(span=slow).mean()
    macd = exp1 - exp2
    signal = macd.ewm(span=signal_period).mean()
    return macd.iloc[-1], signal.iloc[-1]

if __name__ == "__main__":
    if not (BOT_TOKEN and TD_API_KEY):
        raise Exception("❗ تأكد من BOT_TOKEN وTD_API_KEY في البيئة.")
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, welcome_message))
    app.add_handler(CallbackQueryHandler(handle_callbacks))
    print("✅ البوت شغال الآن...")
    app.run_polling()
