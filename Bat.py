import time
from tradingview_ta import TA_Handler, Interval
import requests
from datetime import datetime

# -----------------------------
# تنظیمات ربات تلگرام
# -----------------------------
TELEGRAM_TOKEN = "8448021675:AAE0Z4jRdHZKLVXxIBEfpCb9lUbkkxmlW-k"
CHAT_ID = "7107618784"

# -----------------------------
# تنظیمات استراتژی
# -----------------------------
DELTA = 0.001
LEVERAGE = 20
TARGET_MOVE = 0.10 / LEVERAGE
STOP_MOVE = 0.40 / LEVERAGE

# -----------------------------
# تابع ارسال پیام تلگرام
# -----------------------------
def send_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    data = {"chat_id": CHAT_ID, "text": message}
    try:
        requests.post(url, data=data)
    except Exception as e:
        print("خطا در ارسال پیام تلگرام:", e)

# -----------------------------
# بررسی ورود بر اساس قوانین استراتژی
# -----------------------------
def check_signal(symbol, screener="crypto", exchange="BINANCE"):
    try:
        handler_4h = TA_Handler(
            symbol=symbol,
            screener=screener,
            exchange=exchange,
            interval=Interval.INTERVAL_4_HOURS
        )
        handler_5m = TA_Handler(
            symbol=symbol,
            screener=screener,
            exchange=exchange,
            interval=Interval.INTERVAL_5_MINUTES
        )
        handler_1m = TA_Handler(
            symbol=symbol,
            screener=screener,
            exchange=exchange,
            interval=Interval.INTERVAL_1_MINUTE
        )

        # گرفتن داده‌های کندل
        data_4h = handler_4h.get_analysis().indicators
        data_5m = handler_5m.get_analysis().indicators
        data_1m = handler_1m.get_analysis().indicators

        # high و low کندل 4 ساعته
        high_4h = data_4h.get("high")
        low_4h = data_4h.get("low")
        close_5m = data_5m.get("close")
        close_1m = data_1m.get("close")

        # بررسی کندل هشدار (۵ دقیقه‌ای)
        alert_type = None
        if close_5m >= high_4h * (1 + DELTA):
            alert_type = "above"
        elif close_5m <= low_4h * (1 - DELTA):
            alert_type = "below"

        if not alert_type:
            return None

        # بررسی کندل ورود (۵ دقیقه‌ای)
        entry = None
        if alert_type == "above" and close_5m <= high_4h * (1 - DELTA):
            entry = "SHORT"
        elif alert_type == "below" and close_5m >= low_4h * (1 + DELTA):
            entry = "LONG"

        if not entry:
            return None

        # پیام ورود
        message = f"[{datetime.now()}]\nSymbol: {symbol}\nSignal: {entry}\nTarget: {TARGET_MOVE*LEVERAGE*100:.1f}%\nStop: {STOP_MOVE*LEVERAGE*100:.1f}%"
        return message

    except Exception as e:
        print("خطا در بررسی سیگنال:", e)
        return None

# -----------------------------
# حلقه اصلی برای بررسی دائمی
# -----------------------------
SYMBOLS = ["BTCUSDT", "ETHUSDT"]  # مثال: نمادهایی که میخوای بررسی بشن
CHECK_INTERVAL = 60  # بررسی هر ۶۰ ثانیه

if __name__ == "__main__":
    while True:
        for sym in SYMBOLS:
            msg = check_signal(sym)
            if msg:
                send_telegram(msg)
        time.sleep(CHECK_INTERVAL)
