import pandas as pd
from tradingview_ta import TA_Handler, Interval, Exchange
import time
import requests

# -----------------------------
# تنظیمات ربات تلگرام
# -----------------------------
TELEGRAM_TOKEN = "8448021675:AAE0Z4jRdHZKLVXxIBEfpCb9lUbkkxmlW-k"
CHAT_ID = "7107618784"

def send_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    data = {"chat_id": CHAT_ID, "text": message}
    try:
        requests.post(url, data=data, timeout=10)
    except Exception as e:
        print("Telegram error:", e)

# -----------------------------
# تنظیمات استراتژی
# -----------------------------
DELTA = 0.001
LEVERAGE = 20
TARGET_MOVE = 0.10 / LEVERAGE
STOP_MOVE = 0.40 / LEVERAGE

# فقط NEARUSDT
symbol = "NEARUSDT"

handler = TA_Handler(
    symbol=symbol,
    exchange="BINANCE",
    screener="CRYPTO",
    interval=Interval.INTERVAL_5_MINUTES  # برای بررسی اولیه
)

active_trade = None

def check_alert(close_5m, high_4h, low_4h):
    if close_5m >= high_4h * (1 + DELTA):
        return 'above'
    elif close_5m <= low_4h * (1 - DELTA):
        return 'below'
    return None

def check_entry(close_5m, high_4h, low_4h, alert_type):
    if alert_type == 'above' and close_5m <= high_4h * (1 - DELTA):
        return 'SHORT'
    elif alert_type == 'below' and close_5m >= low_4h * (1 + DELTA):
        return 'LONG'
    return None

# -----------------------------
# حلقه اصلی آنلاین
# -----------------------------
while True:
    try:
        # گرفتن دیتا 4h و 5m و 1m
        data_4h = TA_Handler(symbol=symbol, exchange="BINANCE",
                             screener="CRYPTO", interval=Interval.INTERVAL_4_HOURS).get_analysis().indicators
        data_5m = handler.get_analysis().indicators
        data_1m = TA_Handler(symbol=symbol, exchange="BINANCE",
                             screener="CRYPTO", interval=Interval.INTERVAL_1_MINUTE).get_analysis().indicators

        high_4h = data_4h["high"]
        low_4h = data_4h["low"]
        close_5m = data_5m["close"]
        close_1m = data_1m["close"]
        high_1m = data_1m["high"]
        low_1m = data_1m["low"]

        # بررسی هشدار و ورود
        alert_type = check_alert(close_5m, high_4h, low_4h)
        if alert_type and not active_trade:
            entry_signal = check_entry(close_5m, high_4h, low_4h, alert_type)
            if entry_signal:
                active_trade = {"direction": entry_signal, "entry_price": close_5m}
                send_telegram(f"🚀 سیگنال ورود {entry_signal} برای {symbol} در قیمت {close_5m}")
        
        # بررسی خروج با 1m
        if active_trade:
            if active_trade['direction'] == "LONG":
                if high_1m >= active_trade['entry_price']*(1+TARGET_MOVE):
                    send_telegram(f"✅ LONG بسته شد با سود. قیمت خروج: {active_trade['entry_price']*(1+TARGET_MOVE)}")
                    active_trade = None
                elif low_1m <= active_trade['entry_price']*(1-STOP_MOVE):
                    send_telegram(f"❌ LONG بسته شد با ضرر. قیمت خروج: {active_trade['entry_price']*(1-STOP_MOVE)}")
                    active_trade = None
            elif active_trade['direction'] == "SHORT":
                if low_1m <= active_trade['entry_price']*(1-TARGET_MOVE):
                    send_telegram(f"✅ SHORT بسته شد با سود. قیمت خروج: {active_trade['entry_price']*(1-TARGET_MOVE)}")
                    active_trade = None
                elif high_1m >= active_trade['entry_price']*(1+STOP_MOVE):
                    send_telegram(f"❌ SHORT بسته شد با ضرر. قیمت خروج: {active_trade['entry_price']*(1+STOP_MOVE)}")
                    active_trade = None

        time.sleep(60)  # هر دقیقه بررسی میشه

    except Exception as e:
        print("خطا:", e)
        time.sleep(60)
