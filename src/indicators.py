"""
Cálculo de indicadores técnicos para análisis de trading.
Utiliza pandas_ta para los cálculos base.
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, List


class TechnicalIndicators:
    """Clase para calcular indicadores técnicos"""

    @staticmethod
    def calculate_ema(df: pd.DataFrame, period: int) -> pd.Series:
        """
        Calcula EMA (Exponential Moving Average).

        Args:
            df: DataFrame con columna 'close'
            period: Período para EMA

        Returns:
            Series con valores EMA
        """
        return df['close'].ewm(span=period, adjust=False).mean()

    @staticmethod
    def calculate_rsi(df: pd.DataFrame, period: int = 14) -> pd.Series:
        """
        Calcula RSI (Relative Strength Index) usando el método de Wilder.
        Este método usa EMA suavizada (smoothed) en lugar de SMA.

        Args:
            df: DataFrame con columna 'close'
            period: Período para RSI (default 14)

        Returns:
            Series con valores RSI
        """
        delta = df['close'].diff()

        gain = delta.where(delta > 0, 0)
        loss = -delta.where(delta < 0, 0)

        # Método de Wilder: usa EMA suavizada
        # Primer valor: promedio simple de los primeros 'period' valores
        # Valores siguientes: (prev_avg * (period-1) + current_value) / period
        # Esto es equivalente a EMA con alpha = 1/period
        avg_gain = gain.ewm(alpha=1/period, adjust=False).mean()
        avg_loss = loss.ewm(alpha=1/period, adjust=False).mean()

        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))

        return rsi

    @staticmethod
    def calculate_bollinger_bands(df: pd.DataFrame, period: int = 20, std_dev: float = 2.0) -> Dict[str, pd.Series]:
        """
        Calcula Bandas de Bollinger.

        Args:
            df: DataFrame con columna 'close'
            period: Período para SMA (default 20)
            std_dev: Número de desviaciones estándar (default 2.0)

        Returns:
            Diccionario con 'upper', 'middle', 'lower'
        """
        middle = df['close'].rolling(window=period).mean()
        std = df['close'].rolling(window=period).std()

        upper = middle + (std * std_dev)
        lower = middle - (std * std_dev)

        return {
            'upper': upper,
            'middle': middle,
            'lower': lower
        }

    @staticmethod
    def calculate_macd(df: pd.DataFrame, fast: int = 12, slow: int = 26, signal: int = 9) -> Dict[str, pd.Series]:
        """
        Calcula MACD (Moving Average Convergence Divergence).

        Args:
            df: DataFrame con columna 'close'
            fast: Período EMA rápida (default 12)
            slow: Período EMA lenta (default 26)
            signal: Período para línea de señal (default 9)

        Returns:
            Diccionario con 'macd', 'signal', 'histogram'
        """
        ema_fast = df['close'].ewm(span=fast, adjust=False).mean()
        ema_slow = df['close'].ewm(span=slow, adjust=False).mean()

        macd_line = ema_fast - ema_slow
        signal_line = macd_line.ewm(span=signal, adjust=False).mean()
        histogram = macd_line - signal_line

        return {
            'macd': macd_line,
            'signal': signal_line,
            'histogram': histogram
        }

    @staticmethod
    def calculate_atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
        """
        Calcula ATR (Average True Range) usando el método de Wilder.

        Args:
            df: DataFrame con columnas 'high', 'low', 'close'
            period: Período para ATR (default 14)

        Returns:
            Series con valores ATR
        """
        high = df['high']
        low = df['low']
        close = df['close']

        # True Range components
        tr1 = high - low
        tr2 = abs(high - close.shift(1))
        tr3 = abs(low - close.shift(1))

        # True Range es el máximo de los tres
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)

        # ATR es la media móvil del True Range usando método de Wilder
        # Wilder usa EMA suavizada con alpha = 1/period
        atr = tr.ewm(alpha=1/period, adjust=False).mean()

        return atr

    @staticmethod
    def calculate_sl_tp_with_atr(price: float, atr: float, direction: str = 'LONG') -> Dict[str, Any]:
        """
        Calcula Stop Loss y Take Profit basados en ATR con reglas de seguridad.

        Lógica:
        1. Calcula SL base: (ATR * 2.0) / Precio * 100 = Porcentaje_SL_Base
        2. Aplica reglas de seguridad (límites 1.5% - 3.0%)
        3. Calcula TPs con ratios fijos: TP1 = SL * 1.5, TP2 = SL * 2.25

        Args:
            price: Precio actual
            atr: Valor ATR actual
            direction: 'LONG' o 'SHORT'

        Returns:
            Diccionario con niveles de precio, porcentajes y risk/reward
        """
        # Paso 1: Calcular porcentaje SL base
        sl_base_distance = atr * 2.0
        porcentaje_sl_base = (sl_base_distance / price) * 100

        # Paso 2: Aplicar reglas de seguridad
        limite_aplicado = None
        if porcentaje_sl_base > 3.0:
            porcentaje_sl_final = 3.0
            limite_aplicado = "MÁXIMO (3.0%)"
        elif porcentaje_sl_base < 1.5:
            porcentaje_sl_final = 1.5
            limite_aplicado = "MÍNIMO (1.5%)"
        else:
            porcentaje_sl_final = porcentaje_sl_base
            limite_aplicado = None

        # Paso 3: Calcular porcentajes de TPs con ratios fijos
        porcentaje_tp1 = porcentaje_sl_final * 1.5
        porcentaje_tp2 = porcentaje_sl_final * 2.25

        # Paso 4: Convertir a precios concretos
        if direction == 'LONG':
            sl = price - (price * porcentaje_sl_final / 100)
            tp1 = price + (price * porcentaje_tp1 / 100)
            tp2 = price + (price * porcentaje_tp2 / 100)
        else:  # SHORT
            sl = price + (price * porcentaje_sl_final / 100)
            tp1 = price - (price * porcentaje_tp1 / 100)
            tp2 = price - (price * porcentaje_tp2 / 100)

        return {
            'sl': sl,
            'tp1': tp1,
            'tp2': tp2,
            'sl_pct': porcentaje_sl_final,
            'tp1_pct': porcentaje_tp1,
            'tp2_pct': porcentaje_tp2,
            'sl_base_pct': porcentaje_sl_base,
            'limite_aplicado': limite_aplicado,
            'risk_reward_tp1': 1.5,
            'risk_reward_tp2': 2.25,
            'atr_value': atr
        }

    @staticmethod
    def calculate_vwap(df: pd.DataFrame) -> pd.Series:
        """
        Calcula VWAP (Volume Weighted Average Price) de sesión.
        VWAP se reinicia al inicio de cada sesión (00:00 UTC) según estándar de Binance.

        Args:
            df: DataFrame con columnas 'high', 'low', 'close', 'volume', 'datetime'

        Returns:
            Series con valores VWAP
        """
        from datetime import datetime, timezone

        # Obtener inicio del día actual en UTC (00:00:00)
        now_utc = datetime.now(timezone.utc)
        start_of_day_utc = now_utc.replace(hour=0, minute=0, second=0, microsecond=0)
        start_timestamp_ms = int(start_of_day_utc.timestamp() * 1000)

        # Filtrar solo las velas desde 00:00 UTC de hoy
        # Asumiendo que df tiene columna 'open_time' con timestamps en ms
        if 'open_time' in df.columns:
            df_today = df[df['open_time'] >= start_timestamp_ms].copy()
        elif 'datetime' in df.columns:
            # Si tiene datetime, convertir a timezone-aware si es naive
            if df['datetime'].dt.tz is None:
                # Es timezone-naive, convertir start_of_day a naive también
                start_of_day_naive = start_of_day_utc.replace(tzinfo=None)
                df_today = df[df['datetime'] >= start_of_day_naive].copy()
            else:
                # Es timezone-aware, usar como está
                df_today = df[df['datetime'] >= start_of_day_utc].copy()
        else:
            # Si no hay columna de tiempo, usar todos los datos (fallback)
            df_today = df.copy()

        # Si no hay datos del día actual, retornar NaN
        if len(df_today) == 0:
            return pd.Series([float('nan')] * len(df), index=df.index)

        # Calcular VWAP solo para datos del día actual
        typical_price = (df_today['high'] + df_today['low'] + df_today['close']) / 3
        cumsum_tp_volume = (typical_price * df_today['volume']).cumsum()
        cumsum_volume = df_today['volume'].cumsum()

        vwap_today = cumsum_tp_volume / cumsum_volume

        # Crear serie completa con NaN para datos anteriores al día actual
        vwap_full = pd.Series([float('nan')] * len(df), index=df.index)
        vwap_full.loc[df_today.index] = vwap_today.values

        # Para las velas del día actual, forward fill desde la primera vela
        # Para retornar el último valor válido
        vwap_full = vwap_full.ffill()

        return vwap_full

    @staticmethod
    def analyze_volume(df: pd.DataFrame, lookback: int = 5, use_closed_candle: bool = False) -> Dict[str, Any]:
        """
        Analiza el volumen actual y de la vela anterior comparado con el promedio.

        Args:
            df: DataFrame con columnas 'volume', 'close', 'open'
            lookback: Número de velas para calcular promedio
            use_closed_candle: Si True, usa la penúltima vela (última cerrada) en lugar de la última (en progreso)

        Returns:
            Diccionario con análisis de volumen
        """
        # Volumen de la vela actual (última, puede estar en progreso)
        current_volume = df['volume'].iloc[-1]

        # Volumen de la vela anterior (penúltima, cerrada)
        previous_volume = df['volume'].iloc[-2]

        # Calcular Volume MA(20) - excluyendo la vela actual
        # Usamos las 20 velas anteriores a la vela actual (desde -21 hasta -1, excluyendo -1)
        avg_volume_20 = df['volume'].iloc[-21:-1].mean() if len(df) >= 21 else df['volume'].iloc[:-1].mean()

        # Calcular cambios porcentuales
        volume_change_current = ((current_volume - avg_volume_20) / avg_volume_20) * 100 if avg_volume_20 > 0 else 0
        volume_change_previous = ((previous_volume - avg_volume_20) / avg_volume_20) * 100 if avg_volume_20 > 0 else 0

        # Analizar si las últimas velas son alcistas o bajistas (excluyendo la actual)
        recent_candles = []
        start_index = -lookback - 1  # -6 para lookback=5
        end_index = -1  # Hasta -1 (excluyendo la actual)

        for i in range(start_index, end_index):
            if abs(i) <= len(df):
                is_bullish = df['close'].iloc[i] > df['open'].iloc[i]
                recent_candles.append(is_bullish)

        bullish_count = sum(recent_candles)
        bearish_count = len(recent_candles) - bullish_count

        return {
            'current': current_volume,
            'previous': previous_volume,
            'avg_20': avg_volume_20,
            'change_pct_current': volume_change_current,
            'change_pct_previous': volume_change_previous,
            'bullish_candles': bullish_count,
            'bearish_candles': bearish_count,
            'total_candles': len(recent_candles)
        }

    @staticmethod
    def get_candle_type(df: pd.DataFrame, index: int = -1) -> str:
        """
        Determina si una vela es alcista o bajista.

        Args:
            df: DataFrame con columnas 'open', 'close'
            index: Índice de la vela (default -1, última vela)

        Returns:
            'Alcista' o 'Bajista'
        """
        close = df['close'].iloc[index]
        open_price = df['open'].iloc[index]

        return 'Alcista' if close > open_price else 'Bajista'

    @staticmethod
    def analyze_last_candles(df: pd.DataFrame, count: int = 3) -> Dict[str, Any]:
        """
        Analiza las últimas N velas cerradas para determinar tendencia inmediata.

        Args:
            df: DataFrame con datos OHLCV
            count: Número de velas a analizar (default 3)

        Returns:
            Diccionario con análisis de momentum
        """
        # Excluir la última vela (en progreso)
        last_closed = df.iloc[-count-1:-1]

        candle_types = []
        volumes = []
        avg_volume = df['volume'].iloc[-21:-1].mean() if len(df) >= 21 else df['volume'].mean()

        for i in range(len(last_closed)):
            row = last_closed.iloc[i]
            is_bullish = row['close'] > row['open']
            candle_types.append('Alcista' if is_bullish else 'Bajista')

            volume_vs_avg = row['volume'] > avg_volume
            volumes.append(volume_vs_avg)

        # Determinar tendencia
        bullish_count = candle_types.count('Alcista')
        bearish_count = candle_types.count('Bajista')

        volume_increasing = sum(volumes) >= 2

        if bullish_count == count and volume_increasing:
            trend = "Fuertemente alcista"
        elif bullish_count >= 2:
            trend = "Alcista"
        elif bearish_count == count and volume_increasing:
            trend = "Fuertemente bajista"
        elif bearish_count >= 2:
            trend = "Bajista"
        else:
            trend = "Lateral"

        volume_trend = "Creciente" if volume_increasing else "Decreciente" if sum(volumes) == 0 else "Estable"

        return {
            'candle_types': candle_types,
            'trend': trend,
            'volume_trend': volume_trend,
            'bullish_count': bullish_count,
            'bearish_count': bearish_count
        }

    @staticmethod
    def calculate_all_indicators(df: pd.DataFrame, df_spot: pd.DataFrame = None) -> Dict[str, Any]:
        """
        Calcula todos los indicadores necesarios.

        Args:
            df: DataFrame con datos OHLCV de FUTUROS
            df_spot: DataFrame opcional con datos OHLCV de SPOT (para MACD y Volumen)

        Returns:
            Diccionario con todos los indicadores calculados
        """
        # Validar que tenemos suficientes datos
        if len(df) < 50:
            raise ValueError("No hay suficientes datos para calcular indicadores")

        if df_spot is not None and len(df_spot) < 50:
            raise ValueError("No hay suficientes datos SPOT para calcular indicadores")

        # Precio actual (última vela) - Usa datos de FUTUROS
        current_price = df['close'].iloc[-1]

        # EMAs - Usa datos de FUTUROS
        ema21 = TechnicalIndicators.calculate_ema(df, 21)
        ema50 = TechnicalIndicators.calculate_ema(df, 50)

        # RSI - Usa datos de FUTUROS
        rsi = TechnicalIndicators.calculate_rsi(df, 14)

        # Bollinger Bands - Usa datos de FUTUROS
        bb = TechnicalIndicators.calculate_bollinger_bands(df, 20, 2.0)

        # VWAP - Usa datos de FUTUROS
        vwap = TechnicalIndicators.calculate_vwap(df)

        # ATR - Usa datos de FUTUROS
        atr = TechnicalIndicators.calculate_atr(df, 14)

        # MACD - Usa datos de SPOT si están disponibles, sino FUTUROS
        source_df_macd = df_spot if df_spot is not None else df
        macd = TechnicalIndicators.calculate_macd(source_df_macd, 12, 26, 9)

        # Usar siempre la última vela (vela actual en progreso) para MACD en tiempo real
        macd_index = -1

        # Volumen - Usa datos de SPOT si están disponibles, sino FUTUROS
        source_df_volume = df_spot if df_spot is not None else df
        # Para volumen, si usamos SPOT, necesitamos usar penúltima vela (cerrada)
        volume_analysis = TechnicalIndicators.analyze_volume(source_df_volume, 20, use_closed_candle=(df_spot is not None))

        return {
            'price': current_price,
            'ema21': ema21.iloc[-1],
            'ema50': ema50.iloc[-1],
            'rsi': rsi.iloc[-1],
            'bb_upper': bb['upper'].iloc[-1],
            'bb_middle': bb['middle'].iloc[-1],
            'bb_lower': bb['lower'].iloc[-1],
            'macd_line': macd['macd'].iloc[macd_index],
            'macd_signal': macd['signal'].iloc[macd_index],
            'macd_histogram': macd['histogram'].iloc[macd_index],
            'macd_histogram_prev': macd['histogram'].iloc[macd_index - 1] if len(macd['histogram']) >= abs(macd_index) + 1 else 0,
            'macd_histogram_prev2': macd['histogram'].iloc[macd_index - 2] if len(macd['histogram']) >= abs(macd_index) + 2 else 0,
            'vwap': vwap.iloc[-1],
            'volume': volume_analysis,
            'atr': atr.iloc[-1]
        }
