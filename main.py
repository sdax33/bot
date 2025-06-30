import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, CallbackQueryHandler
import httpx
import os

TOKEN = os.environ.get("BOT_TOKEN")  # ضعه في بيئة السيرفر أو بدلها بنص مباشر
TWELVE_API_KEY = os.environ.get("TWELVE_API_KEY")  # نفس الشيء

# إعدادات السجل
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# أزرار بدء التشغيل
start_keyboard = InlineKeyboardMarkup([
    [InlineKeyboardButton("🔍 تحليل الذهب", callback_data="analyze")],
])

# أزرار اختيار الإطار الزمني
timeframes_keyboard = InlineKeyboardMarkup([
    [InlineKeyboardButton("1 دقيقة", callback_data="analyze_1min")],
    [InlineKeyboardButton("5 دقائق", callback_data="analyze_5min")],
    [InlineKeyboardButton("15 دقيقة", callback_data="analyze_15min")]
])

# أوامر البداية
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 مرحبًا بك!\nاضغط على الزر أدناه لبدء تحليل الذهب:", reply_markup=start_keyboard)

# التعامل مع الضغط على الأزرار
async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "analyze":
        await query.edit_message_text("اختر الإطار الزمني:", reply_markup=timeframes_keyboard)

    elif query.data.startswith("analyze_"):
        interval = query.data.split("_")[1]  # مثل 5min
        await analyze_gold(query, interval)

# تحليل الذهب باستخدام TwelveData
async def analyze_gold(query, interval):
    symbol = "XAU/USD"
    url = f"https://api.twelvedata.com/time_series?symbol={symbol}&interval={interval}&outputsize=20&apikey={TWELVE_API_KEY}"

    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        data = response.json()

    try:
        candles = data['values']
        current = float(candles[0]['close'])
        ema20 = sum(float(c['close']) for c in candles[:20]) / 20

        # RSI حساب تقريبي
        gains = []
        losses = []
        for i in range(1, 15):
            diff = float(candles[i - 1]['close']) - float(candles[i]['close'])
            if diff > 0:
                gains.append(diff)
            else:
                losses.append(abs(diff))

        avg_gain = sum(gains) / 14 if gains else 0.01
        avg_loss = sum(losses) / 14 if losses else 0.01
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))

        # التوصية
        if rsi > 70 and current > ema20:
            reco = "📉 بيع 🔴"
            reason = "السعر مرتفع جدًا (RSI > 70) ويتجاوز المتوسط - احتمال تصحيح"
        elif rsi < 30 and current < ema20:
            reco = "📈 شراء 🟢"
            reason = "السعر منخفض (RSI < 30) وتحت المتوسط - احتمال ارتداد"
        else:
            reco = "⚪ محايد"
            reason = "السعر في منطقة تذبذب (لا توجد إشارة قوية حاليًا)"

        text = f"""📊 تحليل الذهب (XAU/USD) - {interval}
🔸 السعر الحالي: {current}
📈 EMA20: {round(ema20, 2)}
⚖️ RSI: {round(rsi, 2)}

🧭 التوصية: {reco}
📌 السبب: {reason}
🔹 دخول: {current}"""

        await query.edit_message_text(text)
    except Exception as e:
        await query.edit_message_text("حدث خطأ أثناء جلب البيانات أو تحليلها.")
        logger.error(f"تحليل الذهب فشل: {e}")

# تشغيل البوت
if __name__ == "__main__":
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(handle_callback))

    print("✅ البوت شغال الآن...")
    app.run_polling()
