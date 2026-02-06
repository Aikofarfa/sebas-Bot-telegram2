# =============================================================================
# BOT DE SEÑALES SIMPLE - CRUCE DE MEDIAS MÓVILES (Binance + Telegram)
# Versión educativa - SOLO ENVÍA SEÑALES, NO OPERA
# =============================================================================

import ccxt
import pandas as pd
import pandas_ta as ta
import time
from datetime import datetime
from telegram import Bot
from telegram.error import TelegramError

# ────────────────────────────────────────────────
# CONFIGURACIÓN - CAMBIA ESTOS VALORES
# ────────────────────────────────────────────────

TESTNET = False

SYMBOL = "BTC/USDT"
TIMEFRAME = "5m"
CANDLES_TO_LOAD = 100

FAST_MA_PERIOD = 9
SLOW_MA_PERIOD = 21

TELEGRAM_TOKEN = "TU_BOT_TOKEN_AQUÍ"          # ¡cámbialo por el real!
TELEGRAM_CHAT_ID = "8576880914"          # ¡cámbialo por el real!

SLEEP_SECONDS = 60

# ────────────────────────────────────────────────
# NO CAMBIES DE AQUÍ PARA ABAJO
# ────────────────────────────────────────────────

exchange_options = {
    'enableRateLimit': True,
}
exchange = ccxt.binance(exchange_options)

bot = Bot(token=TELEGRAM_TOKEN)

last_signal = None

def enviar_mensaje(texto):
    try:
        bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=texto, parse_mode="Markdown")
        print(f"[Telegram] Mensaje enviado: {texto}")
    except TelegramError as e:
        print(f"Error al enviar mensaje por Telegram: {e}")

def obtener_datos():
    try:
        ohlcv = exchange.fetch_ohlcv(SYMBOL, timeframe=TIMEFRAME, limit=CANDLES_TO_LOAD)
        df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        return df
    except Exception as e:
        print(f"Error al obtener velas: {e}")
        return None

def analizar_mercado(df):
    global last_signal

    if df is None or len(df) < SLOW_MA_PERIOD:
        return None

    df['fast_ma'] = ta.sma(df['close'], length=FAST_MA_PERIOD)
    df['slow_ma'] = ta.sma(df['close'], length=SLOW_MA_PERIOD)

    ultima = df.iloc[-1]
    anterior = df.iloc[-2]

    if (anterior['fast_ma'] <= anterior['slow_ma']) and (ultima['fast_ma'] > ultima['slow_ma']):
        señal = "🟢 COMPRA (cruce alcista)"
        if last_signal != "buy":
            mensaje = (
                f"*{señal}*\n"
                f"Par: `{SYMBOL}`\n"
                f"Temporalidad: {TIMEFRAME}\n"
                f"Precio: {ultima['close']:.2f}\n"
                f"Hora: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            )
            enviar_mensaje(mensaje)
            last_signal = "buy"
        return señal

    elif (anterior['fast_ma'] >= anterior['slow_ma']) and (ultima['fast_ma'] < ultima['slow_ma']):
        señal = "🔴 VENTA (cruce bajista)"
        if last_signal != "sell":
            mensaje = (
                f"*{señal}*\n"
                f"Par: `{SYMBOL}`\n"
                f"Temporalidad: {TIMEFRAME}\n"
                f"Precio: {ultima['close']:.2f}\n"
                f"Hora: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            )
            enviar_mensaje(mensaje)
            last_signal = "sell"
        return señal

    return None

print("Bot de señales iniciado...")
print(f"Par: {SYMBOL} | Temporalidad: {TIMEFRAME} | Chequeo cada {SLEEP_SECONDS} segundos\n")

while True:
    try:
        df = obtener_datos()
        if df is not None:
            señal = analizar_mercado(df)
            if señal:
                print(f"{datetime.now().strftime('%H:%M:%S')} → {señal}")
            else:
                print(f"{datetime.now().strftime('%H:%M:%S')} → Sin señal nueva")
    except Exception as e:
        print(f"Error en bucle principal: {e}")

    # LÍNEA DE PRUEBA TEMPORAL - QUITAR DESPUÉS DE VER EL MENSAJE
    enviar_mensaje("✅ BOT FUNCIONANDO CORRECTAMENTE\nPrueba de conexión exitosa\nHora: " + datetime.now().strftime('%Y-%m-%d %H:%M:%S'))

    time.sleep(60)

