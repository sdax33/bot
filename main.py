import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, CallbackQueryHandler
import httpx
import os

TOKEN = os.environ.get("BOT_TOKEN")
TWELVE_API_KEY = os.environ.get("TD_API_KEY")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

start_keyboard = InlineKeyboardMarkup([
    [InlineKeyboardButton("🔍 تحليل الذهب", callback_data="analyze")],
])

timeframes_keyboard = InlineKeyboardMarkup([
    [InlineKeyboardButton("1 دقيقة", callback_data="analyze_1min")],
    [InlineKeyboardButton("5 دقائق", callback_data="analyze_5min")],
    [InlineKeyboardButton("15 دقيقة", callback_data="analyze_15min")],
])

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 مرحبًا بك!\nاضغط على الزر أدناه لبدء تحليل الذهب:", 
        reply_markup=start_keyboard
    )

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "analyze":
        await query.edit_message_text("اختر الإطار الزمني:", reply_markup=timeframes_keyboard)
    elif query.data.startswith("analyze_"):
        interval = query.data.split("_")[1]
        await analyze_gold(query, interval)

async def analyze_gold(query, interval):
    symbol = "XAU/USD"
    url = f"https://api.twelvedata.com/time_series?symbol={symbol}&interval={interval}&outputsize=30&apikey={TWELVE_API_KEY}"

    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        data = response.json()

    try:
        candles = data['values']
        closes = [float(c['close']) for c in candles[::-1]]  # قديم -> جديد
        highs = [float(c['high']) for c in candles[::-1]]
        lows = [float(c['low']) for c in candles[::-1]]

        # حساب EMA20
        def ema(values, period=20):
            ema_values = []
            k = 2 / (period + 1)
            ema_values.append(sum(values[:period]) / period)  # متوسط بسيط لأول EMA
            for price in values[period:]:
                ema_today = (price - ema_values[-1]) * k + ema_values[-1]
                ema_values.append(ema_today)
            return ema_values[-1]

        ema20 = ema(closes)

        # حساب RSI (14 فترة)
        def rsi(values, period=14):
            gains = []
            losses = []
            for i in range(1, len(values)):
                delta = values[i] - values[i-1]
                if delta > 0:
                    gains.append(delta)
                    losses.append(0)
                else:
                    gains.append(0)
                    losses.append(abs(delta))
            avg_gain = sum(gains[:period]) / period
            avg_loss = sum(losses[:period]) / period
            rs = avg_gain / avg_loss if avg_loss != 0 else 0
            rsi_val = 100 - (100 / (1 + rs))
            return rsi_val

        rsi_val = rsi(closes)

        current = closes[-1]

        # تحليل نموذج شمعة (شمعة الأخيرة)
        last_candle = candles[0]
        open_price = float(last_candle['open'])
        close_price = float(last_candle['close'])
        high_price = float(last_candle['high'])
        low_price = float(last_candle['low'])

        candle_body = abs(close_price - open_price)
        candle_range = high_price - low_price
        candle_upper_shadow = high_price - max(open_price, close_price)
        candle_lower_shadow = min(open_price, close_price) - low_price

        # مثال بسيط لنموذج الابتلاع (Engulfing)
        candle_pattern = "لا يوجد نموذج مميز"
        if close_price > open_price and candle_body > candle_upper_shadow + candle_lower_shadow:
            candle_pattern = "شمعة صعود قوية (Bullish Engulfing محتمل)"
        elif open_price > close_price and candle_body > candle_upper_shadow + candle_lower_shadow:
            candle_pattern = "شمعة هبوط قوية (Bearish Engulfing محتمل)"

        # تحليل التوصية بناءً على EMA و RSI و نموذج الشمعة
        if rsi_val > 70 and current > ema20:
            reco = "📉 بيع 🔴"
            reason = "السعر مرتفع جداً والـ RSI فوق 70، مع إشارة إلى تشبع الشراء."
        elif rsi_val < 30 and current < ema20:
            reco = "📈 شراء 🟢"
            reason = "السعر منخفض جداً والـ RSI تحت 30، مع احتمال ارتداد."
        elif candle_pattern.startswith("شمعة صعود"):
            reco = "📈 شراء 🟢"
            reason = "نموذج شمعة صعود قوية يشير إلى احتمال استمرار الارتفاع."
        elif candle_pattern.startswith("شمعة هبوط"):
            reco = "📉 بيع 🔴"
            reason = "نموذج شمعة هبوط قوية يشير إلى احتمال تراجع السعر."
        else:
            reco = "⚪ محايد"
            reason = "السعر في منطقة تذبذب أو لا توجد إشارة واضحة حالياً."

        text = f"""📊 تحليل الذهب (XAU/USD) - {interval}
🔸 السعر الحالي: {round(current, 2)}
📈 EMA20: {round(ema20, 2)}
⚖️ RSI: {round(rsi_val, 2)}

🧭 التوصية: {reco}
📌 السبب: {reason}
🔹 دخول: {round(current, 2)}
🔎 نموذج الشمعة: {candle_pattern}
"""

        await query.edit_message_text(text)
    except Exception as e:
        await query.edit_message_text("حدث خطأ أثناء جلب البيانات أو تحليلها.")
        logger.error(f"تحليل الذهب فشل: {e}")

if __name__ == "__main__":
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(handle_callback))

    print("✅ البوت شغال الآن...")
    app.run_polling()
