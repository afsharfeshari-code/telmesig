import time
import requests
import pandas as pd
import pytz
from binance.client import Client

# ===== تنظیمات تلگرام =====
TELEGRAM_TOKEN = "8448021675:AAE0Z4jRdHZKLVXxIBEfpCb9lUbkkxmlW-k"
TELEGRAM_CHAT_ID = "7107618784"  # آیدی خودت یا ربات

# ===== تنظیمات ربات =====
symbols = ["NEARUSDT"]  # ارزهای مورد نظر
interval = Client.KLINE_INTERVAL_5MINUTE
delta = 0.001

client = Client()

def send_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    data = {"chat_id": TELEGRAM_CHAT_ID, "text": message}
    try:
        response = requests.post(url, data=data)
        return response.json()
    except:
        return {"ok": False}

# تست تلگرام
test = send_telegram("ربات با موفقیت وصل شد ✅")
if not test.get("ok", False):
    print("⛔ خطا در اتصال تلگرام، متوقف شد.")
    exit()
print("🚀 ربات آنلاین شد.")

last_signal_time = {symbol: None for symbol in symbols}

def get_data(symbol):
    klines = client.get_klines(symbol=symbol, interval=interval, limit=200)
    df = pd.DataFrame(klines, columns=[
        'open_time','open','high','low','close','volume',
        'close_time','qav','num_trades',
        'taker_base_vol','taker_quote_vol','ignore'
    ])
    df['open_time'] = pd.to_datetime(df['open_time'], unit='ms', utc=True)
    df['open_time'] = df['open_time'].dt.tz_convert('Asia/Tehran')
    df.set_index('open_time', inplace=True)
    df[['open','high','low','close']] = df[['open','high','low','close']].astype(float)
    return df

while True:
    for symbol in symbols:
        try:
            df = get_data(symbol)
            df['high_4h'] = df['high'].shift(48)
            df['low_4h'] = df['low'].shift(48)

            last = df.iloc[-1]
            prev = df.iloc[-2]
            candle_time = df.index[-1]

            if last_signal_time[symbol] != candle_time:

                long_signal = (last['close'] >= last['low_4h'] + delta) and (prev['close'] < last['low_4h'] + delta)
                short_signal = (last['close'] <= last['high_4h'] - delta) and (prev['close'] > last['high_4h'] - delta)

                if long_signal or short_signal:
                    signal_type = "🚀 LONG" if long_signal else "🔻 SHORT"
                    price = round(last['close'], 2)
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