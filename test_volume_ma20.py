#!/usr/bin/env python3
"""
Script para verificar Volume MA(20) en datos SPOT
"""

import pandas as pd
from src.binance_client import BinanceClient

def main():
    print("=== TEST DE VOLUME MA(20) ===\n")

    client = BinanceClient()

    # Obtener datos SPOT de 4H
    print("Obteniendo datos SPOT 4H...")
    klines_spot = client.get_klines_spot("ETHUSDT", "4h", 200)
    df_spot = pd.DataFrame(klines_spot)
    df_spot['datetime'] = pd.to_datetime(df_spot['open_time'], unit='ms')

    print(f"Total velas SPOT: {len(df_spot)}\n")

    # Mostrar últimas velas
    print("Últimas 25 velas SPOT:")
    print("-" * 100)
    for i in range(-25, 0):
        timestamp = df_spot.iloc[i]['datetime']
        volume = df_spot.iloc[i]['volume']
        print(f"Vela {i:3d}: {timestamp} | Volumen: {volume:,.0f}")

    # Calcular Volume MA(20) excluyendo la vela en progreso
    print("\n\nVolume MA(20) - últimas 20 velas CERRADAS (excluyendo vela en progreso -1):")
    print("-" * 100)
    volumes_ma20 = []
    for i in range(-21, -1):
        timestamp = df_spot.iloc[i]['datetime']
        volume = df_spot.iloc[i]['volume']
        volumes_ma20.append(volume)
        print(f"Vela {i:3d}: {timestamp} | Volumen: {volume:,.0f}")

    avg_ma20 = sum(volumes_ma20) / len(volumes_ma20)
    print(f"\nPromedio Volume MA(20): {avg_ma20:,.2f}")

    # Calcular excluyendo la última vela cerrada también
    print("\n\nVolume MA(20) - 20 velas anteriores a la última cerrada:")
    print("-" * 100)
    volumes_ma20_prev = []
    for i in range(-22, -2):
        timestamp = df_spot.iloc[i]['datetime']
        volume = df_spot.iloc[i]['volume']
        volumes_ma20_prev.append(volume)

    avg_ma20_prev = sum(volumes_ma20_prev) / len(volumes_ma20_prev)
    print(f"Promedio Volume MA(20) excluyendo última cerrada: {avg_ma20_prev:,.2f}")

    # Info de velas actuales
    print("\n\nVELAS ACTUALES:")
    print("="*100)
    print(f"Vela -2 (última cerrada): {df_spot.iloc[-2]['datetime']} | Volumen: {df_spot.iloc[-2]['volume']:,.0f}")
    print(f"Vela -1 (en progreso): {df_spot.iloc[-1]['datetime']} | Volumen: {df_spot.iloc[-1]['volume']:,.0f}")

    print("\n\nCOMPARACIÓN:")
    print("="*100)
    print(f"Volume MA(20) esperado (TradingView): 66,786")
    print(f"Volume MA(20) calculado (velas -21 a -1): {avg_ma20:,.2f}")
    print(f"Volume MA(20) calculado (velas -22 a -2): {avg_ma20_prev:,.2f}")

if __name__ == "__main__":
    main()
