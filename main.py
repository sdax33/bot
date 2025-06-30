import logging
import os
import httpx
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, CallbackQueryHandler

# 📌 إعداد مفاتيح البيئة
BOT_TOKEN = os.getenv("BOT_TOKEN")
TWELVE_API_KEY = os.getenv("TD_API_KEY")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

# 🎯 إعداد السجل
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ✅ قائمة الأزرار الرئيسية
start_keyboard = InlineKeyboardMarkup([
    [InlineKeyboardButton("🔍 تحليل الذهب", callback_data="analyze")]
])

# ✅ أزرار اختيار الإطار الزمني
timeframes_keyboard = InlineKeyboardMarkup([
    [InlineKeyboardButton("1 دقيقة", callback_data="analyze_1min")],
    [InlineKeyboardButton("5 دقائق", callback_data="analyze_5min")],
    [InlineKeyboardButton("15 دقيقة", callback_data="analyze_15min")]
])

# ⏱ أمر /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 مرحبًا بك!\nاضغط على الزر لبدء تحليل الذهب:",
        reply_markup=start_keyboard
    )

# 🧠 تحليل عبر الذكاء الاصطناعي
async def explain_with_ai(prompt: str):
    try:
        async with httpx.AsyncClient() as client:
            res = await client.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "openai/gpt-3.5-turbo",
                    "messages": [
                        {"role": "system", "content": "أنت خبير تحليلات فنية مالية، اشرح بلغة بسيطة للمستخدم ما الذي يحدث في السوق ولماذا نشتري أو نبيع أو ننتظر."},
                        {"role": "user", "content": prompt}
                    ]
                }
            )
            data = res.json()
            return data['choices'][0]['message']['content']
    except Exception as e:
        return "❌ فشل الذكاء الاصطناعي في توليد التفسير."

# 📥 التعامل مع الضغط على الأزرار
async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "analyze":
        await query.edit_message_text("📊 اختر الإطار الزمني:", reply_markup=timeframes_keyboard)

    elif query.data.startswith("analyze_"):
        interval = query.data.split("_")[1]
        await analyze_gold(query, interval)

# 📈 تحليل الذهب باستخدام TwelveData + AI
async def analyze_gold(query, interval):
    symbol = "XAU/USD"
    url = f"https://api.twelvedata.com/time_series?symbol={symbol}&interval={interval}&outputsize=20&apikey={TWELVE_API_KEY}"

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url)
            data = response.json()

        candles = data['values']
        current = float(candles[0]['close'])
        ema20 = sum(float(c['close']) for c in candles[:20]) / 20

        # RSI تقريبي
        gains, losses = [], []
        for i in range(1, 15):
            diff = float(candles[i - 1]['close']) - float(candles[i]['close'])
            (gains if diff > 0 else losses).append(abs(diff))

        avg_gain = sum(gains) / 14 if gains else 0.01
        avg_loss = sum(losses) / 14 if losses else 0.01
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))

        # توصية منطقية
        if rsi > 70 and current > ema20:
            reco = "📉 بيع 🔴"
            reason = "RSI مرتفع والسعر فوق EMA20"
        elif rsi < 30 and current < ema20:
            reco = "📈 شراء 🟢"
            reason = "RSI منخفض والسعر تحت EMA20"
        else:
            reco = "⚪ محايد"
            reason = "لا توجد إشارة قوية"

        # تحليل من AI
        prompt = f"سعر الذهب الحالي {current}, RSI = {rsi:.2f}, EMA20 = {ema20:.2f}. ما هو التحليل الفني والتوصية؟"
        ai_text = await explain_with_ai(prompt)

        result = f"""📊 تحليل الذهب (XAU/USD) - {interval}
🔸 السعر الحالي: {current}
📈 EMA20: {round(ema20, 2)}
⚖️ RSI: {round(rsi, 2)}

🧭 التوصية: {reco}
📌 السبب: {reason}
🔹 دخول: {current}

🧠 تحليل AI:
{ai_text}
"""
        await query.edit_message_text(result)

    except Exception as e:
        logger.error(f"خطأ في التحليل: {e}")
        await query.edit_message_text("❌ حدث خطأ أثناء تحليل البيانات.")

# 🚀 بدء تشغيل البوت
if __name__ == "__main__":
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(handle_callback))

    print("✅ البوت شغال الآن...")
    app.run_polling()
