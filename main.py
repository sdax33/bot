import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, CallbackQueryHandler
from twelvedata import TDClient
import pandas as pd

# التوكنات من المتغيرات
BOT_TOKEN = os.getenv("BOT_TOKEN")
TD_API_KEY = os.getenv("TD_API_KEY")

# إعداد عميل TwelveData
td = TDClient(apikey=TD_API_KEY)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[InlineKeyboardButton("ابدأ التحليل 🔍", callback_data="analyze")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "👋 أهلا في بوت تحليل الذهب 🟡\nاضغط الزر لتحليل سوق الذهب الآن.",
        reply_markup=reply_markup
    )

async def analyze_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    try:
        await query.answer()
    except Exception as e:
        print(f"⚠️ لم نتمكن من الرد على الزر: {e}")

    # نجيب بيانات الشمعة الأخيرة لـ 15 دقيقة
    try:
        ts = td.time_series(
            symbol="XAU/USD",
            interval="15min",
            outputsize=5
        ).with_rsi(time_period=14).with_ema(time_period=20).as_pandas()
    except Exception as e:
        await query.edit_message_text(f"⚠️ خطأ في سحب البيانات من API: {e}")
        return

    # ننظف البيانات
    df = ts.copy().dropna().tail(3)  # الشموع الثلاث الأخيرة
    last = df.iloc[-1]

    close = float(last["close"])
    rsi = float(last["RSI"])
    ema = float(last["EMA_20"])

    # منطق التوصية البسيط
    if close > ema and rsi < 70:
        decision = "شراء 🟢"
        entry = close
        stop = round(ema, 2)
        target = round(close + (close - ema), 2)
    elif close < ema and rsi > 30:
        decision = "بيع 🔴"
        entry = close
        stop = round(ema, 2)
        target = round(close - (ema - close), 2)
    else:
        decision = "محايد ⚪"
        entry = close
        stop = target = None

    # الرد للمستخدم
    msg = f"""📊 تحليل الذهب (XAU/USD) - إطار 15 دقيقة

🔸 السعر الحالي: {close}
📈 EMA(20): {ema:.2f}
⚖️ RSI(14): {rsi:.1f}

🧭 التوصية: {decision}
🔹 دخول: {entry}
{"🔻 وقف الخسارة: "+str(stop) if stop else ""}
{"🎯 الهدف: "+str(target) if target else ""}

📌 سبب: السعر {'أعلى' if decision.startswith('شراء') else 'أقل' if decision.startswith('بيع') else 'قريب من'} المتوسط المتحرك وRSI {'غير تشبع' if decision!='محايد' else ''}
"""

    await query.edit_message_text(msg)

if __name__ == "__main__":
    if not BOT_TOKEN or not TD_API_KEY:
        raise ValueError("❗ تأكد من وجود BOT_TOKEN وTD_API_KEY في المتغيرات البيئية")

    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(analyze_callback))

    print("✅ البوت شغال الآن...")
    app.run_polling()
