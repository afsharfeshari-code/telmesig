import time
import requests
import pandas as pd
from tradingview_ta import TA_Handler, Interval, Exchange
import pytz

# ===== تنظیمات تلگرام =====
TELEGRAM_TOKEN= "8448021675:AAE0Z4jRdHZKLVXxIBEfpCb9lUbkkxmlW-k"          # ← اینو با توکن ربات خودت عوض کن
TELEGRAM_CHAT_ID = "7107618784"     # ← اینو با Chat ID خودت عوض کن

# ===== تنظیمات ربات =====
symbols = ["NEARUSDT"]               # ← ارزهای مورد نظر
interval = Interval.INTERVAL_5_MINUTES
delta = 0.001

def send_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    data = {"chat_id": TELEGRAM_CHAT_ID, "text": message}
    try:
        response = requests.post(url, data=data)
        return response.json()
    except:
        return {"ok": False}

# ===== تست اتصال تلگرام =====
test = send_telegram("ربات با موفقیت وصل شد ✅")
if not test.get("ok", False):
    print("⛔ خطا در اتصال تلگرام، متوقف شد.")
    exit()
print("🚀 ربات آنلاین شد.")

last_signal_time = {symbol: None for symbol in symbols}

def get_data(symbol):
    handler = TA_Handler(
        symbol=symbol.replace("USDT", ""),
        screener="crypto",
        exchange="BINANCE",
        interval=interval
    )
    analysis = handler.get_analysis()
    price = analysis.indicators["close"]
    df = pd.DataFrame([{"close": price}])
    return df

while True:
    for symbol in symbols:
        try:
            df = get_data(symbol)
            last = df.iloc[-1]
            candle_time = pd.Timestamp.now(pytz.timezone("Asia/Tehran"))

            if last_signal_time[symbol] != candle_time:
                long_signal = last["close"] > (last["close"] - delta)
                short_signal = last["close"] < (last["close"] + delta)

                if long_signal or short_signal:
                    signal_type = "🚀 LONG" if long_signal else "🔻 SHORT"
                    price = round(last["close"], 2)
                    time_str = candle_time.strftime('%Y-%m-%d %H:%M:%S')

                    message = f"""
{signal_type} SIGNAL
Symbol: {symbol}
Time (Iran): {time_str}
Entry Price: {price}
"""
                    print(message)
                    send_telegram(message)

                    with open("signals_log.csv", "a") as f:
                        f.write(f"{signal_type},{symbol},{time_str},{price}\n")

                    last_signal_time[symbol] = candle_time

        except Exception as e:
            print(f"⛔ خطا برای {symbol}: {e}")

    time.sleep(60)
