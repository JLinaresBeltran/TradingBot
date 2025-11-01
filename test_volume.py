#!/usr/bin/env python3
"""
Script para probar cálculo de Volumen y comparar con valores de TradingView
"""

import pandas as pd
from src.binance_client import BinanceClient
from src.indicators import TechnicalIndicators

def main():
    print("=== TEST DE CÁLCULO VOLUMEN ===\n")

    client = BinanceClient()

    # Probar con datos SPOT de 4H (usado para volumen en el reporte)
    print("1. Obteniendo datos SPOT 4H...")
    klines_spot = client.get_klines_spot("ETHUSDT", "4h", 200)
    df_spot = pd.DataFrame(klines_spot)
    df_spot['datetime'] = pd.to_datetime(df_spot['open_time'], unit='ms')

    print(f"   Total velas SPOT: {len(df_spot)}")

    # Mostrar últimas 10 velas con volumen
    print("\n2. Últimas 10 velas SPOT con volumen:")
    print("-" * 100)
    for i in range(-10, 0):
        timestamp = df_spot.iloc[i]['datetime']
        close_price = df_spot.iloc[i]['close']
        volume = df_spot.iloc[i]['volume']
        print(f"Vela {i:3d}: {timestamp} | Cierre: {close_price:8.2f} | Volumen: {volume:,.0f}")

    # Calcular volumen usando la función actual
    print("\n3. Cálculo usando analyze_volume con use_closed_candle=True:")
    print("-" * 100)
    volume_analysis = TechnicalIndicators.analyze_volume(df_spot, lookback=5, use_closed_candle=True)

    print(f"Volumen actual (vela -2): {volume_analysis['current']:,.0f}")
    print(f"Promedio 5 velas: {volume_analysis['avg_5']:,.0f}")
    print(f"Cambio %: {volume_analysis['change_pct']:.2f}%")

    # Calcular manualmente para verificar
    print("\n4. Cálculo MANUAL del promedio:")
    print("-" * 100)

    # La función usa: df['volume'].iloc[-lookback-2:-2].mean()
    # Con lookback=5, esto es: df['volume'].iloc[-7:-2].mean()
    # Esto toma las velas desde -7 hasta -3 (5 velas)

    print("Velas usadas para promedio según el código actual (iloc[-7:-2]):")
    volumes_used = []
    for i in range(-7, -2):
        timestamp = df_spot.iloc[i]['datetime']
        volume = df_spot.iloc[i]['volume']
        volumes_used.append(volume)
        print(f"  Vela {i}: {timestamp} | Volumen: {volume:,.0f}")

    avg_manual = sum(volumes_used) / len(volumes_used)
    print(f"\nPromedio calculado manualmente: {avg_manual:,.2f}")

    # Calcular el promedio que TradingView probablemente usa
    # (últimas 5 velas CERRADAS excluyendo la vela actual que está en progreso)
    print("\n5. Cálculo que probablemente usa TradingView:")
    print("-" * 100)
    print("Últimas 5 velas CERRADAS (excluyendo la vela en progreso -1):")
    print("Velas desde -6 hasta -2:")

    volumes_tv = []
    for i in range(-6, -1):
        timestamp = df_spot.iloc[i]['datetime']
        volume = df_spot.iloc[i]['volume']
        volumes_tv.append(volume)
        print(f"  Vela {i}: {timestamp} | Volumen: {volume:,.0f}")

    avg_tv = sum(volumes_tv) / len(volumes_tv)
    print(f"\nPromedio TradingView: {avg_tv:,.2f}")

    # Intentar encontrar qué velas dan 66,786
    print("\n6. Intentando encontrar qué velas dan promedio de 66,786:")
    print("-" * 100)

    # Probar diferentes combinaciones
    print("Opción A - Últimas 5 velas cerradas excluyendo la actual (-6 a -3):")
    volumes_a = []
    for i in range(-6, -2):
        volume = df_spot.iloc[i]['volume']
        volumes_a.append(volume)
        print(f"  Vela {i}: {volume:,.0f}")
    avg_a = sum(volumes_a) / len(volumes_a)
    print(f"Promedio: {avg_a:,.2f}")

    print("\nOpción B - Velas -7 a -3:")
    volumes_b = []
    for i in range(-7, -3):
        volume = df_spot.iloc[i]['volume']
        volumes_b.append(volume)
        print(f"  Vela {i}: {volume:,.0f}")
    avg_b = sum(volumes_b) / len(volumes_b)
    print(f"Promedio: {avg_b:,.2f}")

    print("\nOpción C - Velas -6 a -2 excluyendo -2:")
    volumes_c = []
    for i in range(-6, -2):
        volume = df_spot.iloc[i]['volume']
        volumes_c.append(volume)
        print(f"  Vela {i}: {volume:,.0f}")
    avg_c = sum(volumes_c) / len(volumes_c)
    print(f"Promedio: {avg_c:,.2f}")

    # Comparación
    print("\n7. COMPARACIÓN FINAL:")
    print("=" * 100)
    print(f"Volumen actual (vela en progreso): {df_spot.iloc[-1]['volume']:,.0f}")
    print(f"Volumen actual (última cerrada): {df_spot.iloc[-2]['volume']:,.0f}")
    print(f"\nPromedio en el REPORTE: 80,977")
    print(f"Promedio calculado por el código: {volume_analysis['avg_5']:,.2f}")
    print(f"Promedio esperado (TradingView): 66,786")
    print(f"Promedio si usamos velas -6 a -2: {avg_tv:,.2f}")
    print(f"Promedio si usamos velas -7 a -3 (DEBERÍA SER ESTE): {avg_b:,.2f}")

    # Ahora probar con FUTUROS
    print("\n\n" + "="*100)
    print("COMPARANDO VOLUMEN FUTUROS VS SPOT")
    print("="*100)

    print("\n8. Obteniendo datos FUTUROS 4H...")
    klines_futures = client.get_klines("ETHUSDT", "4h", 200)
    df_futures = pd.DataFrame(klines_futures)
    df_futures['datetime'] = pd.to_datetime(df_futures['open_time'], unit='ms')

    print(f"   Total velas FUTUROS: {len(df_futures)}")

    # Mostrar últimas 10 velas con volumen
    print("\n9. Últimas 10 velas FUTUROS con volumen:")
    print("-" * 100)
    for i in range(-10, 0):
        timestamp = df_futures.iloc[i]['datetime']
        close_price = df_futures.iloc[i]['close']
        volume = df_futures.iloc[i]['volume']
        print(f"Vela {i:3d}: {timestamp} | Cierre: {close_price:8.2f} | Volumen: {volume:,.0f}")

    # Calcular promedio MA5 con FUTUROS (como lo haría TradingView)
    print("\n10. Cálculo Volume MA(5) con FUTUROS (últimas 5 velas cerradas incluyendo -2):")
    print("-" * 100)
    volumes_futures_ma = []
    for i in range(-6, -1):
        timestamp = df_futures.iloc[i]['datetime']
        volume = df_futures.iloc[i]['volume']
        volumes_futures_ma.append(volume)
        print(f"  Vela {i}: {timestamp} | Volumen: {volume:,.0f}")

    avg_futures_ma = sum(volumes_futures_ma) / len(volumes_futures_ma)
    print(f"\nPromedio Volume MA(5) FUTUROS: {avg_futures_ma:,.2f}")

    # Calcular excluyendo la última cerrada
    print("\n11. Si excluimos la vela -2 (últimas 4 velas cerradas + vela en progreso):")
    print("-" * 100)
    volumes_futures_no_last = []
    for i in range(-6, -2):
        timestamp = df_futures.iloc[i]['datetime']
        volume = df_futures.iloc[i]['volume']
        volumes_futures_no_last.append(volume)
        print(f"  Vela {i}: {timestamp} | Volumen: {volume:,.0f}")

    # Agregar vela en progreso
    vol_in_progress = df_futures.iloc[-1]['volume']
    print(f"  Vela -1 (en progreso): {df_futures.iloc[-1]['datetime']} | Volumen: {vol_in_progress:,.0f}")
    volumes_futures_no_last.append(vol_in_progress)

    avg_futures_no_last = sum(volumes_futures_no_last) / len(volumes_futures_no_last)
    print(f"\nPromedio: {avg_futures_no_last:,.2f}")

    print("\n12. RESUMEN FINAL:")
    print("="*100)
    print(f"Promedio en el REPORTE (SPOT, velas -6 a -2): 80,977")
    print(f"Promedio TradingView esperado: 66,786")
    print(f"Promedio FUTUROS (velas -6 a -1): {avg_futures_ma:,.2f}")
    print(f"Promedio FUTUROS (velas -6 a -3 + vela en progreso): {avg_futures_no_last:,.2f}")

if __name__ == "__main__":
    main()
