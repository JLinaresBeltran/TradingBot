#!/usr/bin/env python3
"""
Script de Análisis Técnico ETHUSDT Futuros Binance
Analiza 7 indicadores técnicos en múltiples timeframes.
"""

import sys
import json
import os
from datetime import datetime, timedelta
import pandas as pd
import numpy as np

from src.binance_client import BinanceClient
from src.indicators import TechnicalIndicators
from src.evaluator import ConditionEvaluator
from src.reporter import Reporter


class TradingAnalysis:
    """Clase principal para análisis técnico"""

    def __init__(self):
        self.client = BinanceClient()
        self.reporter = Reporter()
        self.evaluator = ConditionEvaluator()
        self.state_file = "estado.json"
        self.symbol = "ETHUSDT"

    def load_state(self) -> dict:
        """Carga el estado guardado desde archivo"""
        if not os.path.exists(self.state_file):
            return None

        try:
            with open(self.state_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error cargando estado: {e}")
            return None

    def save_state(self, state: dict):
        """Guarda el estado en archivo"""
        try:
            # Convertir tipos de NumPy a tipos nativos de Python
            def convert_numpy(obj):
                if isinstance(obj, (np.integer, np.int64, np.int32)):
                    return int(obj)
                elif isinstance(obj, (np.floating, np.float64, np.float32)):
                    return float(obj)
                elif isinstance(obj, (np.bool_, bool)):
                    return bool(obj)
                elif isinstance(obj, np.ndarray):
                    return obj.tolist()
                elif isinstance(obj, dict):
                    return {k: convert_numpy(v) for k, v in obj.items()}
                elif isinstance(obj, list):
                    return [convert_numpy(item) for item in obj]
                return obj

            state_converted = convert_numpy(state)
            with open(self.state_file, 'w', encoding='utf-8') as f:
                json.dump(state_converted, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error guardando estado: {e}")

    def get_klines_dataframe(self, interval: str, limit: int = 50, use_spot: bool = False) -> pd.DataFrame:
        """
        Obtiene velas de Binance y las convierte a DataFrame.

        Args:
            interval: Timeframe (4h, 1h, 15m, 5m)
            limit: Número de velas
            use_spot: Si True, obtiene datos de SPOT. Si False, obtiene de FUTUROS (default)

        Returns:
            DataFrame con datos OHLCV
        """
        if use_spot:
            klines = self.client.get_klines_spot(self.symbol, interval, limit)
        else:
            klines = self.client.get_klines(self.symbol, interval, limit)

        df = pd.DataFrame(klines)
        df['datetime'] = pd.to_datetime(df['open_time'], unit='ms')
        df = df[['datetime', 'open', 'high', 'low', 'close', 'volume',
                'open_time', 'close_time']]

        return df

    def analyze_timeframe(self, interval: str, limit: int = 50) -> dict:
        """
        Analiza un timeframe específico.
        MACD y Volumen se calculan con datos de SPOT, el resto con FUTUROS.

        Args:
            interval: Timeframe a analizar
            limit: Número de velas a obtener

        Returns:
            Diccionario con análisis completo
        """
        # Obtener datos de FUTUROS
        df_futures = self.get_klines_dataframe(interval, limit, use_spot=False)

        # Obtener datos de SPOT para MACD y Volumen
        df_spot = self.get_klines_dataframe(interval, limit, use_spot=True)

        # Calcular indicadores (MACD y Volumen usan datos SPOT)
        indicators = TechnicalIndicators.calculate_all_indicators(df_futures, df_spot)

        # Clasificar estados
        ema_position = self.evaluator.classify_ema_position(
            indicators['price'], indicators['ema21'], indicators['ema50']
        )
        ema_cross = self.evaluator.classify_ema_cross(
            indicators['ema21'], indicators['ema50']
        )
        rsi_state = self.evaluator.classify_rsi(indicators['rsi'])
        bb_state = self.evaluator.classify_bollinger_position(
            indicators['price'], indicators['bb_upper'], indicators['bb_lower'], df_futures
        )
        macd_line_state, macd_hist_state = self.evaluator.classify_macd(
            indicators['macd_line'], indicators['macd_signal'],
            indicators['macd_histogram'], indicators['macd_histogram_prev'],
            indicators['macd_histogram_prev2']
        )
        volume_state = self.evaluator.classify_volume(indicators['volume'])
        vwap_state = self.evaluator.classify_vwap_position(
            indicators['price'], indicators['vwap']
        )

        # Evaluar condiciones
        long_conditions, long_count, sl_tp_long = self.evaluator.evaluate_long_conditions(indicators, df_futures)
        short_conditions, short_count, sl_tp_short = self.evaluator.evaluate_short_conditions(indicators, df_futures)

        # Información de la vela actual (usar FUTUROS)
        last_candle = df_futures.iloc[-1]
        candle_completion, time_remaining = self.client.calculate_candle_completion(
            int(last_candle['open_time']), int(last_candle['close_time'])
        )
        candle_time = self.client.format_candle_time(
            int(last_candle['open_time']), int(last_candle['close_time']), interval
        )

        return {
            'indicators': indicators,
            'evaluations': {
                'ema_position': ema_position,
                'ema_cross': ema_cross,
                'rsi_state': rsi_state,
                'bb_state': bb_state,
                'macd_line_state': macd_line_state,
                'macd_hist_state': macd_hist_state,
                'volume_state': volume_state,
                'vwap_state': vwap_state,
                'long_conditions': long_conditions,
                'long_count': long_count,
                'short_conditions': short_conditions,
                'short_count': short_count,
                'sl_tp_long': sl_tp_long,
                'sl_tp_short': sl_tp_short
            },
            'candle_time': candle_time,
            'candle_completion': candle_completion,
            'time_remaining': time_remaining,
            'raw_df': df_futures,  # Para análisis posteriores (usar FUTUROS)
            'candle_open_time': int(last_candle['open_time']),
            'candle_close_time': int(last_candle['close_time'])
        }

    def should_update_timeframe(self, interval: str, state: dict) -> bool:
        """
        Determina si un timeframe debe actualizarse basándose en si su vela se cerró.

        Args:
            interval: Timeframe a verificar (4h, 1h, 15m)
            state: Estado actual con información de última actualización

        Returns:
            True si el timeframe tiene una vela nueva cerrada, False en caso contrario
        """
        tf_key = interval.replace('m', 'min')

        # Si no existe información previa, debe actualizar
        if tf_key not in state.get('timeframes', {}):
            return True

        old_timeframe_state = state['timeframes'][tf_key]

        # Si no tiene timestamp guardado, debe actualizar
        if 'last_candle_close_time' not in old_timeframe_state:
            return True

        # Obtener última vela del timeframe
        df = self.get_klines_dataframe(interval, limit=2)
        last_candle = df.iloc[-1]
        current_close_time = int(last_candle['close_time'])
        saved_close_time = old_timeframe_state['last_candle_close_time']

        # Si el close_time cambió, significa que hay una nueva vela
        return current_close_time != saved_close_time

    def option1_initial_analysis(self):
        """OPCIÓN 1: Análisis Inicial (4h, 1h, 15min)"""
        print("\n🔍 Ejecutando Análisis Inicial...")
        print("Conectando a Binance Futures API...")

        # Verificar conexión
        if not self.client.test_connection():
            print("❌ ERROR: No se pudo conectar a Binance API. Verificar conexión a internet.")
            return

        print("✅ Conexión exitosa")

        try:
            # Analizar los 3 timeframes
            print("\n📊 Analizando timeframes...")

            data = {}
            for interval in ['4h', '1h', '15m']:
                print(f"  Analizando {interval}...")
                tf_key = interval.replace('m', 'min')
                data[tf_key] = self.analyze_timeframe(interval, limit=50)

            # Generar reporte
            print("\n📝 Generando reporte...")
            report = self.reporter.generate_initial_analysis_report(data)

            # Guardar reporte
            filepath = self.reporter.save_report(report, "inicial")
            print(f"✅ Reporte guardado: {filepath}")

            # Mostrar reporte
            print("\n" + "="*60)
            print(report)
            print("="*60)

            # Guardar estado
            state = {
                'analisis_inicial': {
                    'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    'existe': True
                },
                'contador_actualizaciones': 0,
                'ultima_actualizacion': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'timeframes': {}
            }

            for tf_key in ['4h', '1h', '15min']:
                tf_data = data[tf_key]
                indicators = tf_data['indicators']
                evaluations = tf_data['evaluations']

                state['timeframes'][tf_key] = {
                    'precio': indicators['price'],
                    'ema21': indicators['ema21'],
                    'ema50': indicators['ema50'],
                    'rsi': indicators['rsi'],
                    'bb_superior': indicators['bb_upper'],
                    'bb_media': indicators['bb_middle'],
                    'bb_inferior': indicators['bb_lower'],
                    'macd_linea': indicators['macd_line'],
                    'macd_signal': indicators['macd_signal'],
                    'macd_histograma': indicators['macd_histogram'],
                    'volumen': indicators['volume']['current'],
                    'vwap': indicators['vwap'],
                    'atr': indicators['atr'],
                    'long_count': evaluations['long_count'],
                    'short_count': evaluations['short_count'],
                    'long_conditions': evaluations['long_conditions'],
                    'short_conditions': evaluations['short_conditions'],
                    'sl_tp_long': evaluations.get('sl_tp_long'),
                    'sl_tp_short': evaluations.get('sl_tp_short'),
                    'last_candle_open_time': tf_data['candle_open_time'],
                    'last_candle_close_time': tf_data['candle_close_time']
                }

            self.save_state(state)
            print("\n💾 Estado guardado exitosamente")

        except Exception as e:
            print(f"\n❌ ERROR: {str(e)}")
            import traceback
            traceback.print_exc()

    def option2_update_analysis(self):
        """OPCIÓN 2: Actualización 15 Minutos (4h, 1h, 15min)"""
        print("\n🔄 Ejecutando Actualización...")

        # Verificar que existe análisis inicial
        state = self.load_state()

        if not state or not state.get('analisis_inicial', {}).get('existe'):
            print("❌ ERROR: Debe ejecutar primero ANÁLISIS INICIAL (Opción 1)")
            return

        print("✅ Estado anterior cargado")
        print("Conectando a Binance Futures API...")

        # Verificar conexión
        if not self.client.test_connection():
            print("❌ ERROR: No se pudo conectar a Binance API. Verificar conexión a internet.")
            return

        print("✅ Conexión exitosa")

        try:
            # Verificar qué timeframes deben actualizarse
            print("\n🔍 Verificando velas cerradas...")

            timeframes_to_update = []
            timeframes_skipped = []

            for interval in ['4h', '1h', '15m']:
                if self.should_update_timeframe(interval, state):
                    timeframes_to_update.append(interval)
                    tf_key = interval.replace('m', 'min')
                    print(f"  ✅ {interval}: Nueva vela cerrada - se actualizará")
                else:
                    timeframes_skipped.append(interval)
                    tf_key = interval.replace('m', 'min')
                    print(f"  ⏸️  {interval}: Vela en progreso - no se actualizará")

            # Si no hay timeframes para actualizar, salir
            if not timeframes_to_update:
                print("\n⚠️  No hay timeframes con velas cerradas para actualizar.")
                print("Ejecute esta opción cuando al menos una vela se haya cerrado.")
                return

            # Analizar solo timeframes que necesitan actualización
            print(f"\n📊 Analizando {len(timeframes_to_update)} timeframe(s)...")

            data = {}
            changes = {}

            for interval in timeframes_to_update:
                print(f"  Analizando {interval}...")
                tf_key = interval.replace('m', 'min')
                data[tf_key] = self.analyze_timeframe(interval, limit=50)

                # Detectar cambios
                old_state = state['timeframes'].get(tf_key, {})
                new_state = {
                    'precio': data[tf_key]['indicators']['price'],
                    'ema21': data[tf_key]['indicators']['ema21'],
                    'ema50': data[tf_key]['indicators']['ema50'],
                    'rsi': data[tf_key]['indicators']['rsi'],
                    'macd_histograma': data[tf_key]['indicators']['macd_histogram'],
                    'long_count': data[tf_key]['evaluations']['long_count'],
                    'short_count': data[tf_key]['evaluations']['short_count'],
                    'long_conditions': data[tf_key]['evaluations']['long_conditions'],
                    'short_conditions': data[tf_key]['evaluations']['short_conditions']
                }

                changes[tf_key] = self.evaluator.detect_changes(old_state, new_state, tf_key)
                changes[tf_key]['old_long_count'] = old_state.get('long_count', 0)
                changes[tf_key]['old_short_count'] = old_state.get('short_count', 0)

            # Calcular tiempo transcurrido
            initial_time = datetime.strptime(
                state['analisis_inicial']['timestamp'], "%Y-%m-%d %H:%M:%S"
            )
            elapsed = datetime.now() - initial_time
            hours = int(elapsed.total_seconds() // 3600)
            minutes = int((elapsed.total_seconds() % 3600) // 60)
            time_elapsed = f"{hours} horas {minutes} minutos"

            # Incrementar contador
            state['contador_actualizaciones'] += 1
            update_number = state['contador_actualizaciones']

            # Generar reporte
            print("\n📝 Generando reporte...")
            report = self.reporter.generate_update_report(
                data, update_number, time_elapsed, changes, timeframes_skipped
            )

            # Guardar reporte
            filepath = self.reporter.save_report(report, "actualizacion", update_number)
            print(f"✅ Reporte guardado: {filepath}")

            # Mostrar reporte
            print("\n" + "="*60)
            print(report)
            print("="*60)

            # Actualizar estado solo para timeframes actualizados
            state['ultima_actualizacion'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            for interval in timeframes_to_update:
                tf_key = interval.replace('m', 'min')
                tf_data = data[tf_key]
                indicators = tf_data['indicators']
                evaluations = tf_data['evaluations']

                state['timeframes'][tf_key] = {
                    'precio': indicators['price'],
                    'ema21': indicators['ema21'],
                    'ema50': indicators['ema50'],
                    'rsi': indicators['rsi'],
                    'bb_superior': indicators['bb_upper'],
                    'bb_media': indicators['bb_middle'],
                    'bb_inferior': indicators['bb_lower'],
                    'macd_linea': indicators['macd_line'],
                    'macd_signal': indicators['macd_signal'],
                    'macd_histograma': indicators['macd_histogram'],
                    'volumen': indicators['volume']['current'],
                    'vwap': indicators['vwap'],
                    'atr': indicators['atr'],
                    'long_count': evaluations['long_count'],
                    'short_count': evaluations['short_count'],
                    'long_conditions': evaluations['long_conditions'],
                    'short_conditions': evaluations['short_conditions'],
                    'sl_tp_long': evaluations.get('sl_tp_long'),
                    'sl_tp_short': evaluations.get('sl_tp_short'),
                    'last_candle_open_time': tf_data['candle_open_time'],
                    'last_candle_close_time': tf_data['candle_close_time']
                }

            self.save_state(state)
            print("\n💾 Estado actualizado exitosamente")

        except Exception as e:
            print(f"\n❌ ERROR: {str(e)}")
            import traceback
            traceback.print_exc()

    def option3_5min_analysis(self):
        """OPCIÓN 3: Análisis 5 Minutos (timing de entrada)"""
        print("\n⚡ Ejecutando Análisis 5 Minutos...")
        print("Conectando a Binance Futures API...")

        # Verificar conexión
        if not self.client.test_connection():
            print("❌ ERROR: No se pudo conectar a Binance API. Verificar conexión a internet.")
            return

        print("✅ Conexión exitosa")

        try:
            # Analizar 5 minutos
            print("\n📊 Analizando timeframe 5 minutos...")

            analysis = self.analyze_timeframe('5m', limit=50)
            df = analysis['raw_df']

            # Análisis adicional para 5 minutos
            last_candles_analysis = TechnicalIndicators.analyze_last_candles(df, 3)

            # Calcular movimiento en vela actual
            current_candle = df.iloc[-1]
            candle_movement = ((current_candle['close'] - current_candle['open']) /
                             current_candle['open']) * 100

            # Tendencia RSI últimas 3 velas
            rsi_series = TechnicalIndicators.calculate_rsi(df, 14)
            rsi_last_3 = rsi_series.iloc[-4:-1]
            if len(rsi_last_3) >= 2:
                if rsi_last_3.iloc[-1] > rsi_last_3.iloc[0]:
                    rsi_trend = "subiendo"
                elif rsi_last_3.iloc[-1] < rsi_last_3.iloc[0]:
                    rsi_trend = "bajando"
                else:
                    rsi_trend = "lateral"
            else:
                rsi_trend = "N/A"

            # Tendencia MACD histograma
            macd_hist = analysis['indicators']['macd_histogram']
            macd_hist_prev = analysis['indicators']['macd_histogram_prev']
            macd_hist_prev2 = analysis['indicators']['macd_histogram_prev2']

            if abs(macd_hist) > abs(macd_hist_prev) and abs(macd_hist_prev) > abs(macd_hist_prev2):
                macd_trend = "creciendo"
            elif abs(macd_hist) < abs(macd_hist_prev) and abs(macd_hist_prev) < abs(macd_hist_prev2):
                macd_trend = "decreciendo"
            else:
                macd_trend = "estable"

            # Formatear tiempo restante
            minutes_remaining = analysis['time_remaining'] // 60
            seconds_remaining = analysis['time_remaining'] % 60
            time_remaining_str = f"{minutes_remaining} minutos {seconds_remaining} segundos"

            # Preparar datos para reporte
            report_data = {
                'candle_time': analysis['candle_time'],
                'candle_completion': analysis['candle_completion'],
                'time_remaining': time_remaining_str,
                'candle_movement': candle_movement,
                'candle_high': current_candle['high'],
                'candle_low': current_candle['low'],
                'indicators': analysis['indicators'],
                'evaluations': analysis['evaluations'],
                'momentum': last_candles_analysis,
                'rsi_trend': rsi_trend,
                'macd_trend': macd_trend
            }

            # Generar reporte
            print("\n📝 Generando reporte...")
            report = self.reporter.generate_5min_analysis_report(report_data)

            # Guardar reporte
            filepath = self.reporter.save_report(report, "5min")
            print(f"✅ Reporte guardado: {filepath}")

            # Mostrar reporte
            print("\n" + "="*60)
            print(report)
            print("="*60)

        except Exception as e:
            print(f"\n❌ ERROR: {str(e)}")
            import traceback
            traceback.print_exc()

    def show_menu(self):
        """Muestra el menú principal"""
        print("\n" + "="*50)
        print("=== ANÁLISIS TÉCNICO ETHUSDT FUTUROS ===")
        print("="*50)
        print("\nSeleccione una opción:")
        print("\n1. ANÁLISIS INICIAL (4h, 1h, 15min)")
        print("2. ACTUALIZACIÓN 15 MINUTOS (4h, 1h, 15min)")
        print("3. ANÁLISIS 5 MINUTOS (timing de entrada)")
        print("4. Salir")
        print()

    def run(self):
        """Ejecuta el programa principal"""
        while True:
            self.show_menu()

            try:
                choice = input("Opción: ").strip()

                if choice == '1':
                    self.option1_initial_analysis()
                elif choice == '2':
                    self.option2_update_analysis()
                elif choice == '3':
                    self.option3_5min_analysis()
                elif choice == '4':
                    print("\n👋 Saliendo del programa...")
                    sys.exit(0)
                else:
                    print("\n❌ Opción inválida. Por favor seleccione 1, 2, 3 o 4.")

            except KeyboardInterrupt:
                print("\n\n👋 Programa interrumpido por el usuario.")
                sys.exit(0)
            except Exception as e:
                print(f"\n❌ Error inesperado: {str(e)}")


def main():
    """Función principal"""
    analysis = TradingAnalysis()
    analysis.run()


if __name__ == "__main__":
    main()
