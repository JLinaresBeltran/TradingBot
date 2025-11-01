#!/usr/bin/env python3
"""
Script para probar cálculo de MACD y comparar con valores de TradingView
"""

import pandas as pd
from src.binance_client import BinanceClient
from src.indicators import TechnicalIndicators

def main():
    print("=== TEST DE CÁLCULO MACD ===\n")

    client = BinanceClient()

    # Probar con datos SPOT de 4H
    print("1. Obteniendo datos SPOT 4H...")
    klines_spot = client.get_klines_spot("ETHUSDT", "4h", 200)
    df_spot = pd.DataFrame(klines_spot)
    df_spot['datetime'] = pd.to_datetime(df_spot['open_time'], unit='ms')

    print(f"   Total velas SPOT: {len(df_spot)}")

    # Calcular MACD
    macd_result = TechnicalIndicators.calculate_macd(df_spot, 12, 26, 9)

    # Mostrar últimas 5 velas
    print("\n2. Últimas 5 velas SPOT y sus valores MACD:")
    print("-" * 100)
    for i in range(-5, 0):
        timestamp = df_spot.iloc[i]['datetime']
        close_price = df_spot.iloc[i]['close']
        macd_line = macd_result['macd'].iloc[i]
        signal_line = macd_result['signal'].iloc[i]
        histogram = macd_result['histogram'].iloc[i]

        print(f"Vela {i}: {timestamp}")
        print(f"  Precio cierre: {close_price:.2f}")
        print(f"  MACD línea: {macd_line:.4f}")
        print(f"  Señal: {signal_line:.4f}")
        print(f"  Histograma: {histogram:.4f}")
        print()

    # Ahora probar con datos FUTUROS
    print("\n3. Obteniendo datos FUTUROS 4H...")
    klines_futures = client.get_klines("ETHUSDT", "4h", 200)
    df_futures = pd.DataFrame(klines_futures)
    df_futures['datetime'] = pd.to_datetime(df_futures['open_time'], unit='ms')

    print(f"   Total velas FUTUROS: {len(df_futures)}")

    # Calcular MACD
    macd_result_futures = TechnicalIndicators.calculate_macd(df_futures, 12, 26, 9)

    # Mostrar últimas 5 velas
    print("\n4. Últimas 5 velas FUTUROS y sus valores MACD:")
    print("-" * 100)
    for i in range(-5, 0):
        timestamp = df_futures.iloc[i]['datetime']
        close_price = df_futures.iloc[i]['close']
        macd_line = macd_result_futures['macd'].iloc[i]
        signal_line = macd_result_futures['signal'].iloc[i]
        histogram = macd_result_futures['histogram'].iloc[i]

        print(f"Vela {i}: {timestamp}")
        print(f"  Precio cierre: {close_price:.2f}")
        print(f"  MACD línea: {macd_line:.4f}")
        print(f"  Señal: {signal_line:.4f}")
        print(f"  Histograma: {histogram:.4f}")
        print()

    # Comparación
    print("\n5. COMPARACIÓN:")
    print("-" * 100)
    print("VALORES EN EL REPORTE (usando SPOT con índice -2):")
    print(f"  MACD línea: {macd_result['macd'].iloc[-2]:.4f}")
    print(f"  Señal: {macd_result['signal'].iloc[-2]:.4f}")
    print(f"  Histograma: {macd_result['histogram'].iloc[-2]:.4f}")

    print("\nVALORES USANDO ÚLTIMA VELA CERRADA SPOT (índice -1):")
    print(f"  MACD línea: {macd_result['macd'].iloc[-1]:.4f}")
    print(f"  Señal: {macd_result['signal'].iloc[-1]:.4f}")
    print(f"  Histograma: {macd_result['histogram'].iloc[-1]:.4f}")

    print("\nVALORES USANDO ÚLTIMA VELA FUTUROS (índice -1):")
    print(f"  MACD línea: {macd_result_futures['macd'].iloc[-1]:.4f}")
    print(f"  Señal: {macd_result_futures['signal'].iloc[-1]:.4f}")
    print(f"  Histograma: {macd_result_futures['histogram'].iloc[-1]:.4f}")

    print("\nVALORES EN TU GRÁFICO:")
    print(f"  MACD línea: -37.70")
    print(f"  Señal: -15.00")
    print(f"  Histograma: -22.69")

    print("\n" + "="*100)

    # Probar con 1H también
    print("\n6. PROBANDO CON TIMEFRAME 1H:")
    print("-" * 100)
    klines_1h = client.get_klines("ETHUSDT", "1h", 200)
    df_1h = pd.DataFrame(klines_1h)
    df_1h['datetime'] = pd.to_datetime(df_1h['open_time'], unit='ms')

    macd_result_1h = TechnicalIndicators.calculate_macd(df_1h, 12, 26, 9)

    print("\nÚltimas 3 velas 1H FUTUROS:")
    for i in range(-3, 0):
        timestamp = df_1h.iloc[i]['datetime']
        close_price = df_1h.iloc[i]['close']
        macd_line = macd_result_1h['macd'].iloc[i]
        signal_line = macd_result_1h['signal'].iloc[i]
        histogram = macd_result_1h['histogram'].iloc[i]

        print(f"\nVela {i}: {timestamp}")
        print(f"  Precio cierre: {close_price:.2f}")
        print(f"  MACD línea: {macd_line:.4f}")
        print(f"  Señal: {signal_line:.4f}")
        print(f"  Histograma: {histogram:.4f}")

if __name__ == "__main__":
    main()
