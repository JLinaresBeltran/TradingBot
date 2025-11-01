"""
Generador de reportes formateados para análisis técnico.
Guarda reportes en archivos y los imprime en consola.
"""

from datetime import datetime
from typing import Dict, Any, List
import os


class Reporter:
    """Generador de reportes de análisis técnico"""

    CONDITION_LABELS_LONG = [
        "Precio sobre EMA 21 y EMA 50",
        "EMA 21 sobre EMA 50",
        "RSI entre 45-65",
        "Precio rebotando BB inferior o rompiendo BB superior",
        "MACD línea sobre señal + histograma creciente verde",
        "Volumen creciente en velas alcistas",
        "Precio sobre VWAP"
    ]

    CONDITION_LABELS_SHORT = [
        "Precio bajo EMA 21 y EMA 50",
        "EMA 21 bajo EMA 50",
        "RSI entre 35-55",
        "Precio rechazando BB superior o rompiendo BB inferior",
        "MACD línea bajo señal + histograma decreciente rojo",
        "Volumen creciente en velas bajistas",
        "Precio bajo VWAP"
    ]

    def __init__(self, reports_dir: str = "reportes"):
        """
        Inicializa el generador de reportes.

        Args:
            reports_dir: Directorio donde guardar los reportes
        """
        self.reports_dir = reports_dir
        os.makedirs(reports_dir, exist_ok=True)

    @staticmethod
    def format_number(value: float, decimals: int = 2) -> str:
        """Formatea un número con decimales específicos"""
        return f"{value:.{decimals}f}"

    @staticmethod
    def format_volume(value: float) -> str:
        """Formatea volumen con separadores de miles"""
        return f"{value:,.0f}"

    @staticmethod
    def format_percentage(value: float) -> str:
        """Formatea porcentaje con signo"""
        sign = "+" if value >= 0 else ""
        return f"{sign}{value:.2f}%"

    def generate_initial_analysis_report(self, data: Dict[str, Any]) -> str:
        """
        Genera reporte de análisis inicial.

        Args:
            data: Diccionario con todos los datos del análisis

        Returns:
            String con el reporte formateado
        """
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        report = f"""=== ANÁLISIS INICIAL ETHUSDT FUTUROS ===
Timestamp: {timestamp}

ℹ️  Fuentes de datos:
  • Precio, EMA, RSI, Bandas de Bollinger, VWAP: FUTUROS
  • MACD, Volumen: SPOT

"""

        for tf_name in ['4h', '1h', '15min']:
            tf_data = data[tf_name]
            report += self._format_timeframe_section(tf_name.upper(), tf_data)

        return report

    def generate_update_report(self, data: Dict[str, Any], update_number: int,
                              time_elapsed: str, changes: Dict[str, Any],
                              timeframes_skipped: list = None) -> str:
        """
        Genera reporte de actualización.

        Args:
            data: Diccionario con datos actuales
            update_number: Número de actualización
            time_elapsed: Tiempo transcurrido desde análisis inicial
            changes: Diccionario con cambios detectados
            timeframes_skipped: Lista de timeframes no actualizados (opcional)

        Returns:
            String con el reporte formateado
        """
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        if timeframes_skipped is None:
            timeframes_skipped = []

        # Verificar si hubo cambios significativos en los timeframes actualizados
        has_changes = any(changes.get(tf, {}).get('has_changes', False)
                         for tf in data.keys())

        if not has_changes:
            report = f"""=== ACTUALIZACIÓN #{update_number} ETHUSDT FUTUROS ===
Timestamp: {timestamp}

Sin cambios significativos detectados.

ESTADO ACTUAL:
4H: LONG {data['4h']['long_count']}/7 | SHORT {data['4h']['short_count']}/7
1H: LONG {data['1h']['long_count']}/7 | SHORT {data['1h']['short_count']}/7
15MIN: LONG {data['15min']['long_count']}/7 | SHORT {data['15min']['short_count']}/7
"""
            return report

        # Reporte con cambios
        report = f"""=== ACTUALIZACIÓN #{update_number} ETHUSDT FUTUROS ===
Timestamp: {timestamp}
Tiempo desde análisis inicial: {time_elapsed}

"""

        # Mostrar timeframes omitidos si los hay
        if timeframes_skipped:
            report += "⏸️  TIMEFRAMES NO ACTUALIZADOS (vela en progreso):\n"
            for tf in timeframes_skipped:
                report += f"  • {tf}\n"
            report += "\n"

        report += """━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
CAMBIOS DETECTADOS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

"""

        # Solo mostrar timeframes actualizados con cambios
        for tf_name in ['4h', '1h', '15min']:
            if tf_name in data:
                tf_changes = changes.get(tf_name, {})
                if tf_changes.get('has_changes', False):
                    report += self._format_changes_section(tf_name.upper(), data[tf_name], tf_changes)

        report += """━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
ESTADO ACTUAL (TIMEFRAMES ACTUALIZADOS)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

"""

        # Solo mostrar timeframes que fueron actualizados
        for tf_name in ['4h', '1h', '15min']:
            if tf_name in data:
                tf_data = data[tf_name]
                candle_time = tf_data['candle_time']
                completion = tf_data['candle_completion']
                evaluations = tf_data['evaluations']

                long_count = evaluations['long_count']
                short_count = evaluations['short_count']

                report += f"""TIMEFRAME {tf_name.upper()}:
Vela: {candle_time} ({completion}% completada)
LONG: {long_count}/7 | SHORT: {short_count}/7

"""
                # Agregar sección de gestión de riesgo si hay señal válida
                if long_count >= 5 and 'sl_tp_long' in evaluations and evaluations['sl_tp_long']:
                    report += self._format_risk_management_section(evaluations['sl_tp_long'], 'LONG')
                elif short_count >= 5 and 'sl_tp_short' in evaluations and evaluations['sl_tp_short']:
                    report += self._format_risk_management_section(evaluations['sl_tp_short'], 'SHORT')

        return report

    def generate_5min_analysis_report(self, data: Dict[str, Any]) -> str:
        """
        Genera reporte de análisis 5 minutos.

        Args:
            data: Diccionario con datos del análisis

        Returns:
            String con el reporte formateado
        """
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        indicators = data['indicators']
        evaluations = data['evaluations']
        momentum = data['momentum']

        # Calcular distancias porcentuales
        dist_ema21 = ((indicators['price'] - indicators['ema21']) / indicators['ema21']) * 100
        dist_ema50 = ((indicators['price'] - indicators['ema50']) / indicators['ema50']) * 100
        dist_bb_upper = ((indicators['bb_upper'] - indicators['price']) / indicators['price']) * 100
        dist_bb_lower = ((indicators['price'] - indicators['bb_lower']) / indicators['price']) * 100
        dist_vwap = ((indicators['price'] - indicators['vwap']) / indicators['vwap']) * 100

        # Movimiento en vela actual
        candle_move = data.get('candle_movement', 0.0)

        report = f"""=== ANÁLISIS 5 MINUTOS - TIMING DE ENTRADA ===
Timestamp: {timestamp}
Vela actual: {data['candle_time']} (EN PROGRESO - {data['candle_completion']}% completada)
Cierre proyectado en: {data['time_remaining']}

ℹ️  Fuentes: Precio/EMA/RSI/BB/VWAP: FUTUROS | MACD/Volumen: SPOT

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PRECIO ACTUAL
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Precio: {self.format_number(indicators['price'])}
Movimiento en vela actual: {self.format_percentage(candle_move)}
Rango vela actual: High {self.format_number(data['candle_high'])} - Low {self.format_number(data['candle_low'])}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
INDICADORES
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

• EMA 21: {self.format_number(indicators['ema21'])} | EMA 50: {self.format_number(indicators['ema50'])}
  Estado: {evaluations['ema_position']}
  Cruce: {evaluations['ema_cross']}
  Distancia precio-EMA21: {self.format_percentage(dist_ema21)}
  Distancia precio-EMA50: {self.format_percentage(dist_ema50)}

• RSI 14: {self.format_number(indicators['rsi'])}
  Estado: {evaluations['rsi_state']}
  Tendencia últimas 3 velas: {data.get('rsi_trend', 'N/A')}

• Bandas de Bollinger:
  Superior: {self.format_number(indicators['bb_upper'])} | Media: {self.format_number(indicators['bb_middle'])} | Inferior: {self.format_number(indicators['bb_lower'])}
  Estado: {evaluations['bb_state']}
  Distancia a banda superior: {self.format_percentage(dist_bb_upper)}
  Distancia a banda inferior: {self.format_percentage(dist_bb_lower)}

• MACD (vela actual en progreso):
  Línea: {self.format_number(indicators['macd_line'], 4)} | Señal: {self.format_number(indicators['macd_signal'], 4)} | Histograma: {self.format_number(indicators['macd_histogram'], 4)}
  Estado Línea: {evaluations['macd_line_state']}
  Estado Histograma: {evaluations['macd_hist_state']}
  Cambio histograma últimas 3 velas: {data.get('macd_trend', 'N/A')}

• Volumen:
  Vela anterior (cerrada): {self.format_volume(indicators['volume']['previous'])} | Cambio: {self.format_percentage(indicators['volume']['change_pct_previous'])}
  Vela actual (en progreso): {self.format_volume(indicators['volume']['current'])} | Cambio: {self.format_percentage(indicators['volume']['change_pct_current'])}
  Volume MA(20): {self.format_volume(indicators['volume']['avg_20'])}
  Estado: {evaluations['volume_state']}

• VWAP: {self.format_number(indicators['vwap'])}
  Estado: {evaluations['vwap_state']}
  Distancia precio-VWAP: {self.format_percentage(dist_vwap)}

• ATR 14: {self.format_number(indicators['atr'], 4)}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
EVALUACIÓN
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

LONG: {evaluations['long_count']}/7 condiciones cumplidas
"""

        for i, condition in enumerate(evaluations['long_conditions']):
            symbol = "✅" if condition else "❌"
            report += f"  {symbol} {self.CONDITION_LABELS_LONG[i]}\n"

        report += f"""
SHORT: {evaluations['short_count']}/7 condiciones cumplidas
"""

        for i, condition in enumerate(evaluations['short_conditions']):
            symbol = "✅" if condition else "❌"
            report += f"  {symbol} {self.CONDITION_LABELS_SHORT[i]}\n"

        # Agregar sección de gestión de riesgo si hay señal válida
        if evaluations['long_count'] >= 5 and 'sl_tp_long' in evaluations and evaluations['sl_tp_long']:
            report += self._format_risk_management_section(evaluations['sl_tp_long'], 'LONG')
        elif evaluations['short_count'] >= 5 and 'sl_tp_short' in evaluations and evaluations['sl_tp_short']:
            report += self._format_risk_management_section(evaluations['sl_tp_short'], 'SHORT')

        report += f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
MOMENTUM INMEDIATO (últimas 3 velas)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Velas: {momentum['candle_types'][0]} - {momentum['candle_types'][1]} - {momentum['candle_types'][2]}
Tendencia: {momentum['trend']}
Volumen en tendencia: {momentum['volume_trend']}
"""

        return report

    def _format_timeframe_section(self, tf_name: str, data: Dict[str, Any]) -> str:
        """Formatea la sección de un timeframe para el reporte inicial"""

        indicators = data['indicators']
        evaluations = data['evaluations']

        section = f"""━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
TIMEFRAME {tf_name}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Vela actual: {data['candle_time']} (EN PROGRESO - {data['candle_completion']}% completada)

INDICADORES:
• EMA 21: {self.format_number(indicators['ema21'])} | EMA 50: {self.format_number(indicators['ema50'])} | Precio: {self.format_number(indicators['price'])}
  Estado: {evaluations['ema_position']}
  Cruce: {evaluations['ema_cross']}

• RSI 14: {self.format_number(indicators['rsi'])}
  Estado: {evaluations['rsi_state']}

• Bandas de Bollinger:
  Superior: {self.format_number(indicators['bb_upper'])} | Media: {self.format_number(indicators['bb_middle'])} | Inferior: {self.format_number(indicators['bb_lower'])}
  Estado: {evaluations['bb_state']}

• MACD (vela actual en progreso):
  Línea: {self.format_number(indicators['macd_line'], 4)} | Señal: {self.format_number(indicators['macd_signal'], 4)} | Histograma: {self.format_number(indicators['macd_histogram'], 4)}
  Estado Línea: {evaluations['macd_line_state']}
  Estado Histograma: {evaluations['macd_hist_state']}

• Volumen:
  Vela anterior (cerrada): {self.format_volume(indicators['volume']['previous'])} | Cambio: {self.format_percentage(indicators['volume']['change_pct_previous'])}
  Vela actual (en progreso): {self.format_volume(indicators['volume']['current'])} | Cambio: {self.format_percentage(indicators['volume']['change_pct_current'])}
  Volume MA(20): {self.format_volume(indicators['volume']['avg_20'])}
  Estado: {evaluations['volume_state']}

• VWAP: {self.format_number(indicators['vwap'])} | Precio: {self.format_number(indicators['price'])}
  Estado: {evaluations['vwap_state']}

• ATR 14: {self.format_number(indicators['atr'], 4)}

EVALUACIÓN:
LONG: {evaluations['long_count']}/7 condiciones cumplidas
"""

        for i, condition in enumerate(evaluations['long_conditions']):
            symbol = "✅" if condition else "❌"
            section += f"  {symbol} {self.CONDITION_LABELS_LONG[i]}\n"

        section += f"""
SHORT: {evaluations['short_count']}/7 condiciones cumplidas
"""

        for i, condition in enumerate(evaluations['short_conditions']):
            symbol = "✅" if condition else "❌"
            section += f"  {symbol} {self.CONDITION_LABELS_SHORT[i]}\n"

        # Agregar sección de gestión de riesgo si hay señal válida
        if evaluations['long_count'] >= 5 and 'sl_tp_long' in evaluations and evaluations['sl_tp_long']:
            section += self._format_risk_management_section(evaluations['sl_tp_long'], 'LONG')
        elif evaluations['short_count'] >= 5 and 'sl_tp_short' in evaluations and evaluations['sl_tp_short']:
            section += self._format_risk_management_section(evaluations['sl_tp_short'], 'SHORT')

        section += "\n"

        return section

    def _format_changes_section(self, tf_name: str, current_data: Dict[str, Any],
                               changes: Dict[str, Any]) -> str:
        """Formatea la sección de cambios detectados"""

        section = f"""TIMEFRAME {tf_name}:
Vela actual: {current_data['candle_time']} (EN PROGRESO - {current_data['candle_completion']}% completada)
Precio: {self.format_number(current_data['indicators']['price'])}

"""

        # Mostrar cambios en indicadores
        if changes['indicator_changes']:
            section += "INDICADORES ACTUALIZADOS:\n"
            for change in changes['indicator_changes']:
                section += f"• {change['name']}: {self.format_number(change['old'])} → {self.format_number(change['new'])}\n"
            section += "\n"

        # Mostrar cambios en evaluación
        section += "EVALUACIÓN ACTUALIZADA:\n"

        if changes['long_count_change']:
            old_count = changes.get('old_long_count', 0)
            new_count = current_data['evaluations']['long_count']
            section += f"LONG: {new_count}/7 (antes: {old_count}/7)\n"

            if changes['condition_changes']['long']:
                section += "  Cambios:\n"
                for cond_change in changes['condition_changes']['long']:
                    idx = cond_change['index']
                    old_val = cond_change['old']
                    new_val = cond_change['new']
                    arrow = "✅→❌" if old_val and not new_val else "❌→✅"
                    section += f"  {arrow} {self.CONDITION_LABELS_LONG[idx]}\n"
            section += "\n"

        if changes['short_count_change']:
            old_count = changes.get('old_short_count', 0)
            new_count = current_data['evaluations']['short_count']
            section += f"SHORT: {new_count}/7 (antes: {old_count}/7)\n"

            if changes['condition_changes']['short']:
                section += "  Cambios:\n"
                for cond_change in changes['condition_changes']['short']:
                    idx = cond_change['index']
                    old_val = cond_change['old']
                    new_val = cond_change['new']
                    arrow = "✅→❌" if old_val and not new_val else "❌→✅"
                    section += f"  {arrow} {self.CONDITION_LABELS_SHORT[idx]}\n"
            section += "\n"

        return section

    def _format_risk_management_section(self, sl_tp: Dict[str, Any], direction: str) -> str:
        """
        Formatea la sección de gestión de riesgo con niveles de SL/TP.

        Args:
            sl_tp: Diccionario con niveles de SL/TP calculados
            direction: 'LONG' o 'SHORT'

        Returns:
            String con la sección formateada
        """
        section = f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
GESTIÓN DE RIESGO - SEÑAL {direction}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Basado en ATR (14): {self.format_number(sl_tp['atr_value'], 4)}
"""

        # Mostrar si se aplicó límite de seguridad
        if sl_tp['limite_aplicado']:
            section += f"⚠️  Límite aplicado: {sl_tp['limite_aplicado']}\n"
            section += f"   (SL base calculado: {self.format_number(sl_tp['sl_base_pct'], 2)}% → ajustado a {self.format_number(sl_tp['sl_pct'], 2)}%)\n\n"

        section += f"""Stop Loss:     {self.format_number(sl_tp['sl'])}  ({self.format_number(sl_tp['sl_pct'], 2)}%)
Take Profit 1: {self.format_number(sl_tp['tp1'])}  ({self.format_number(sl_tp['tp1_pct'], 2)}%) - Cerrar 70% posición
Take Profit 2: {self.format_number(sl_tp['tp2'])}  ({self.format_number(sl_tp['tp2_pct'], 2)}%) - Cerrar 30% posición

Risk/Reward Ratios:
• TP1: 1:{self.format_number(sl_tp['risk_reward_tp1'], 2)}
• TP2: 1:{self.format_number(sl_tp['risk_reward_tp2'], 2)}
"""

        return section

    def save_report(self, report: str, report_type: str, update_number: int = None) -> str:
        """
        Guarda el reporte en un archivo.

        Args:
            report: Contenido del reporte
            report_type: Tipo de reporte ("inicial", "actualizacion", "5min")
            update_number: Número de actualización (solo para tipo "actualizacion")

        Returns:
            Ruta del archivo guardado
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        if report_type == "inicial":
            filename = f"analisis_inicial_{timestamp}.txt"
        elif report_type == "actualizacion":
            filename = f"actualizacion_{update_number}_{timestamp}.txt"
        elif report_type == "5min":
            filename = f"analisis_5min_{timestamp}.txt"
        else:
            filename = f"reporte_{timestamp}.txt"

        filepath = os.path.join(self.reports_dir, filename)

        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(report)

        return filepath
