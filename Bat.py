import time
import requests
import pandas as pd
from tradingview_ta import TA_Handler, Interval
import pytz
from datetime import datetime
import os

# ===== تنظیمات تلگرام =====
TELEGRAM_TOKEN = "8448021675:AAE0Z4jRdHZKLVXxIBEfpCb9lUbkkxmlW-k"
TELEGRAM_CHAT_ID = "7107618784"

symbols = ["NEARUSDT"]
interval = Interval.INTERVAL_5_MINUTES
delta = 0.001

def send_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    data = {"chat_id": TELEGRAM_CHAT_ID, "text": message}
    requests.post(url, data=data)

def get_ohlc(symbol):
    handler = TA_Handler(
        symbol=symbol.replace("USDT",""),
        screener="crypto",
        exchange="BINANCE",
        interval=interval
    )
    analysis = handler.get_analysis()

    return {
        "open": analysis.indicators["open"],
        "high": analysis.indicators["high"],
        "low": analysis.indicators["low"],
        "close": analysis.indicators["close"],
    }

send_telegram("ربات استراتژی اصلی فعال شد ✅")

while True:
    now = datetime.utcnow()

    # فقط ابتدای هر کندل 5 دقیقه‌ای
    if now.minute % 5 == 0 and now.second < 8:

        for symbol in symbols:

            try:
                data = get_ohlc(symbol)

                if os.path.exists("history.csv"):
                    df = pd.read_csv("history.csv")
                else:
                    df = pd.DataFrame()

                df = pd.concat([df, pd.DataFrame([data])])
                df = df.tail(60)

                df["high_4h"] = df["high"].shift(48)
                df["low_4h"] = df["low"].shift(48)

                if len(df) > 48:

                    last = df.iloc[-1]
                    prev = df.iloc[-2]

                    long_signal = (
                        last["close"] >= last["low_4h"] + delta and
                        prev["close"] < last["low_4h"] + delta
                    )

                    short_signal = (
                        last["close"] <= last["high_4h"] - delta and
                        prev["close"] > last["high_4h"] - delta
                    )

                    if long_signal or short_signal:

                        signal_type = "🚀 LONG" if long_signal else "🔻 SHORT"
                        price = round(last["close"], 2)

                        iran_time = datetime.now(
                            pytz.timezone("Asia/Tehran")
                        ).strftime("%Y-%m-%d %H:%M:%S")

                        message = f"""
{signal_type} SIGNAL
Symbol: {symbol}
Time (Iran): {iran_time}
Entry Price: {price}
"""

                        send_telegram(message)

                df.to_csv("history.csv", index=False)

            except Exception as e:
                print("خطا:", e)

        time.sleep(10)

    time.sleep(1)
