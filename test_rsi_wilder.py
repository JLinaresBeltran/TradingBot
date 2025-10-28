"""
Script para probar la corrección del RSI usando método de Wilder.
Compara el RSI calculado con el método correcto (EMA de Wilder).
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))

from src.binance_client import BinanceClient
from src.indicators import TechnicalIndicators
import pandas as pd

def calculate_rsi_sma(df: pd.DataFrame, period: int = 14) -> pd.Series:
    """Cálculo RSI con SMA (método anterior - INCORRECTO)"""
    delta = df['close'].diff()
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)
    avg_gain = gain.rolling(window=period).mean()
    avg_loss = loss.rolling(window=period).mean()
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

def main():
    print("=== PRUEBA DE RSI - MÉTODO DE WILDER ===\n")

    # Obtener datos de ETHUSDT
    client = BinanceClient()
    klines = client.get_klines('ETHUSDT', '1h', limit=100)

    df = pd.DataFrame(klines)

    print(f"Total de velas obtenidas: {len(df)}")
    print(f"Precio actual (última vela): {df['close'].iloc[-1]:.2f}\n")

    # Calcular RSI con método anterior (SMA)
    rsi_sma = calculate_rsi_sma(df, 14)

    # Calcular RSI con método correcto (Wilder EMA)
    rsi_wilder = TechnicalIndicators.calculate_rsi(df, 14)

    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print("COMPARACIÓN DE MÉTODOS")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n")

    # Últimos 5 valores
    print("Últimas 5 velas:\n")
    print(f"{'Vela':<10} {'Precio':<10} {'RSI SMA':<12} {'RSI Wilder':<12} {'Diferencia':<12}")
    print("-" * 60)

    for i in range(-5, 0):
        precio = df['close'].iloc[i]
        rsi_s = rsi_sma.iloc[i]
        rsi_w = rsi_wilder.iloc[i]
        diff = rsi_w - rsi_s

        print(f"{i+5:<10} {precio:<10.2f} {rsi_s:<12.2f} {rsi_w:<12.2f} {diff:+.2f}")

    print("\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print("VALORES ACTUALES (última vela)")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n")

    rsi_sma_current = rsi_sma.iloc[-1]
    rsi_wilder_current = rsi_wilder.iloc[-1]
    diferencia = rsi_wilder_current - rsi_sma_current

    print(f"RSI con SMA (método anterior):     {rsi_sma_current:.4f}")
    print(f"RSI con Wilder EMA (método nuevo): {rsi_wilder_current:.4f}")
    print(f"Diferencia:                        {diferencia:+.4f}")

    print("\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print("INTERPRETACIÓN")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n")

    print("✅ RSI corregido para usar método de Wilder (EMA suavizada)")
    print("   Este es el método estándar usado por:")
    print("   • TradingView")
    print("   • Binance")
    print("   • MetaTrader")
    print("   • Indicador RSI original de J. Welles Wilder\n")

    if abs(diferencia) > 1:
        print(f"⚠️  Diferencia significativa: {abs(diferencia):.2f} puntos")
        print("   El método de Wilder es más suave y preciso\n")
    else:
        print(f"ℹ️  Diferencia mínima: {abs(diferencia):.2f} puntos")
        print("   Ambos métodos dan resultados similares en este momento\n")

    # Comparar interpretación
    def interpret_rsi(rsi_value):
        if rsi_value >= 70:
            return "Sobrecompra"
        elif rsi_value <= 30:
            return "Sobreventa"
        elif 45 <= rsi_value <= 65:
            return "Momentum alcista sin sobrecompra"
        else:
            return "Neutral"

    interp_sma = interpret_rsi(rsi_sma_current)
    interp_wilder = interpret_rsi(rsi_wilder_current)

    print(f"Interpretación SMA:    {interp_sma}")
    print(f"Interpretación Wilder: {interp_wilder}")

    if interp_sma != interp_wilder:
        print("\n⚠️  IMPORTANTE: La interpretación cambió con el método correcto")
    else:
        print("\n✅ La interpretación se mantiene igual")

if __name__ == "__main__":
    main()
