# =============================================================================
# BOT DE SIMULACIÓN DE TRADES - CRUCE DE MEDIAS MÓVILES (Binance + Telegram)
# Usa datos reales, simula trades virtuales, envía notificaciones a Telegram
# =============================================================================

import ccxt
import pandas as pd
import pandas_ta as ta
import time
from datetime import datetime
from telegram import Bot
from telegram.error import TelegramError

# ────────────────────────────────────────────────
# CONFIGURACIÓN - AJUSTADA PARA MEJOR RELACIÓN RIESGO/RECOMPENSA
# ────────────────────────────────────────────────

# Binance (datos reales públicos)
TESTNET = False

# Par y temporalidad
SYMBOL = "BTC/USDT"
TIMEFRAME = "5m"          # 5 minutos para trades cortos \~10-15 min
CANDLES_TO_LOAD = 100     # Velas para análisis

# Estrategia: cruce de medias + simulación
FAST_MA_PERIOD = 9
SLOW_MA_PERIOD = 21
INITIAL_BALANCE = 1000.0  # USDT inicial virtual
STOP_LOSS = 0.015         # 1.5% pérdida máxima por trade
TAKE_PROFIT = 0.03        # 3% ganancia objetivo (relación 1:2)

# Telegram
TELEGRAM_TOKEN = "TU_BOT_TOKEN_AQUÍ"
TELEGRAM_CHAT_ID = "TU_CHAT_ID_AQUÍ"

# Intervalo de chequeo (segundos)
SLEEP_SECONDS = 60

# ────────────────────────────────────────────────
# NO CAMBIES DE AQUÍ PARA ABAJO
# ────────────────────────────────────────────────

# Inicializar Binance
exchange_options = {
    'enableRateLimit': True,
}
exchange = ccxt.binance(exchange_options)

# Inicializar Telegram
bot = Bot(token=TELEGRAM_TOKEN)

# Variables de simulación
balance = INITIAL_BALANCE
position = 0.0  # Cantidad de BTC
entry_price = 0.0
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
    global balance, position, entry_price, last_signal

    if df is None or len(df) < SLOW_MA_PERIOD:
        return None

    # Calcular medias móviles
    df['fast_ma'] = ta.sma(df['close'], length=FAST_MA_PERIOD)
    df['slow_ma'] = ta.sma(df['close'], length=SLOW_MA_PERIOD)

    ultima = df.iloc[-1]
    anterior = df.iloc[-2]
    current_price = ultima['close']

    señal = None

    # Verificar Stop Loss y Take Profit si hay posición abierta
    if position > 0:
        change = (current_price - entry_price) / entry_price
        if change <= -STOP_LOSS:
            new_balance = position * current_price
            pnl = new_balance - (position * entry_price)
            balance = new_balance
            position = 0.0
            señal = f"🚫 **STOP LOSS ACTIVADO** (-1.5%)\n" \
                    f"Vendido {position:.6f} BTC a {current_price:.2f} USDT\n" \
                    f"Pérdida: {pnl:.2f} USDT\n" \
                    f"Balance actual: {balance:.2f} USDT"
            last_signal = "sell"
        elif change >= TAKE_PROFIT:
            new_balance = position * current_price
            pnl = new_balance - (position * entry_price)
            balance = new_balance
            position = 0.0
            señal = f"🎯 **TAKE PROFIT ACTIVADO** (+3%)\n" \
                    f"Vendido {position:.6f} BTC a {current_price:.2f} USDT\n" \
                    f"Ganancia: {pnl:.2f} USDT\n" \
                    f"Balance actual: {balance:.2f} USDT"
            last_signal = "sell"

    # Señal de compra (solo si no hay posición abierta)
    if position == 0:
        if (anterior['fast_ma'] <= anterior['slow_ma']) and (ultima['fast_ma'] > ultima['slow_ma']) and last_signal != "buy":
            amount_to_buy = balance / current_price
            position = amount_to_buy
            entry_price = current_price
            balance = 0.0
            sl_price = entry_price * (1 - STOP_LOSS)
            tp_price = entry_price * (1 + TAKE_PROFIT)
            señal = f"🟢 **COMPRA SIMULADA**\n" \
                    f"Comprado {amount_to_buy:.6f} BTC a {current_price:.2f} USDT\n" \
                    f"Stop Loss: {sl_price:.2f} USDT\n" \
                    f"Take Profit: {tp_price:.2f} USDT\n" \
                    f"Valor actual portfolio: {position * current_price:.2f} USDT"
            last_signal = "buy"

    # Señal de venta manual (cruce bajista)
    elif (anterior['fast_ma'] >= anterior['slow_ma']) and (ultima['fast_ma'] < ultima['slow_ma']) and position > 0 and last_signal != "sell":
        new_balance = position * current_price
        pnl = new_balance - (position * entry_price)
        balance = new_balance
        position = 0.0
        señal = f"🔴 **VENTA SIMULADA** (cruce bajista)\n" \
                f"Vendido {position:.6f} BTC a {current_price:.2f} USDT\n" \
                f"Resultado: {pnl:.2f} USDT\n" \
                f"Balance actual: {balance:.2f} USDT"
        last_signal = "sell"

    if señal:
        mensaje = (
            f"{señal}\n"
            f"Par: `{SYMBOL}`\n"
            f"Temporalidad: {TIMEFRAME}\n"
            f"Hora: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        )
        enviar_mensaje(mensaje)

    return señal

# Inicio
print("Bot de simulación iniciado con datos reales...")
print(f"Balance inicial: {INITIAL_BALANCE} USDT | SL: {STOP_LOSS*100}% | TP: {TAKE_PROFIT*100}%")

# Mensaje inicial de confirmación (puedes comentarlo después)
enviar_mensaje(
    "✅ **Bot de simulación iniciado**\n"
    f"Datos reales de Binance ({SYMBOL} {TIMEFRAME})\n"
    f"Balance virtual: {INITIAL_BALANCE} USDT\n"
    f"SL: {STOP_LOSS*100}% | TP: {TAKE_PROFIT*100}%\n"
    "Esperando señales..."
)

while True:
    try:
        df = obtener_datos()
        if df is not None:
            señal = analizar_mercado(df)
            if señal:
                print(f"{datetime.now().strftime('%H:%M:%S')} → {señal}")
            else:
                current_price = df.iloc[-1]['close'] if not df.empty else 0
                portfolio_value = balance + (position * current_price)
                print(f"{datetime.now().strftime('%H:%M:%S')} → Sin señal nueva | Portfolio: {portfolio_value:.2f} USDT")
    except Exception as e:
        print(f"Error en bucle principal: {e}")

    time.sleep(60)

