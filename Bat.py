import time
import requests
import pandas as pd
from tradingview_ta import TA_Handler, Interval
import pytz
from datetime import datetime

# ===== تنظیمات تلگرام =====
TELEGRAM_TOKEN = "8448021675:AAE0Z4jRdHZKLVXxIBEfpCb9lUbkkxmlW-k"
TELEGRAM_CHAT_ID = "7107618784"

# ===== تنظیمات استراتژی اصلی =====
symbol = "NEARUSDT"
interval = Interval.INTERVAL_5_MINUTES
delta = 0.001
leverage = 20
take_profit_ratio = 0.20
stop_loss_ratio = 0.30

# نگهداری داده‌ها و آخرین سیگنال
df_history = pd.DataFrame()
last_signal_time = None

def send_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    try:
        requests.post(url, data={"chat_id": TELEGRAM_CHAT_ID, "text": message})
    except:
        print("⚠ خطا در ارسال پیام تلگرام")

def get_ohlc(symbol):
    handler = TA_Handler(
        symbol=symbol.replace("USDT",""),
        screener="crypto",
        exchange="",  # خالی می‌گذاریم تا TradingView خودش دیتا بده
        interval=interval
    )
    analysis = handler.get_analysis()
    return {
        "open": float(analysis.indicators["open"]),
        "high": float(analysis.indicators["high"]),
        "low": float(analysis.indicators["low"]),
        "close": float(analysis.indicators["close"]),
        "timestamp": datetime.utcnow()
    }

def main():
    global df_history, last_signal_time
    print("🚀 ربات TradingView با استراتژی اصلی فعال شد")

    while True:
        now = datetime.utcnow()

        # فقط ابتدای هر کندل 5 دقیقه‌ای
        if now.minute % 5 == 0 and now.second < 8:

            try:
                # گرفتن داده زنده
                data = get_ohlc(symbol)
                df_history = pd.concat([df_history, pd.DataFrame([data])])
                df_history = df_history.tail(60)  # نگه داشتن آخرین 60 کندل

                # محاسبه high/low 4 ساعته (48 کندل)
                df_history["high_4h"] = df_history["high"].shift(48)
                df_history["low_4h"] = df_history["low"].shift(48)

                if len(df_history) > 48:
                    last = df_history.iloc[-1]
                    prev = df_history.iloc[-2]

                    # شرایط ورود Long/Short طبق همان استراتژی اصلی
                    long_signal = (last["close"] >= last["low_4h"] + delta) and (prev["close"] < last["low_4h"] + delta)
                    short_signal = (last["close"] <= last["high_4h"] - delta) and (prev["close"] > last["high_4h"] - delta)

                    if long_signal or short_signal:
                        # جلوگیری از ارسال چندباره در همان کندل
                        if last_signal_time != last["timestamp"]:
                            signal_type = "🚀 LONG" if long_signal else "🔻 SHORT"
                            price = round(last["close"], 2)
                            iran_time = datetime.now(pytz.timezone("Asia/Tehran")).strftime("%Y-%m-%d %H:%M:%S")
                            message = f"""
{signal_type} SIGNAL
Symbol: {symbol}
Time (Iran): {iran_time}
Entry Price: {price}
"""
                            send_telegram(message)
                            print(message)
                            last_signal_time = last["timestamp"]

            except Exception as e:
                print("⚠ خطا:", e)

            time.sleep(10)

        time.sleep(1)

if __name__ == "__main__":
    main()
