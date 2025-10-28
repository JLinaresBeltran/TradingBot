"""
Evaluador de condiciones LONG y SHORT según criterios específicos.
Compara estados entre actualizaciones para detectar cambios.
"""

from typing import Dict, Any, List, Tuple
import pandas as pd


class ConditionEvaluator:
    """Evaluador de condiciones de trading"""

    @staticmethod
    def classify_ema_position(price: float, ema21: float, ema50: float) -> str:
        """
        Clasifica la posición del precio respecto a las EMAs.

        Returns:
            String descriptivo del estado
        """
        if price > ema21 and price > ema50:
            return "Precio sobre EMA 21 y EMA 50"
        elif price < ema21 and price < ema50:
            return "Precio bajo EMA 21 y EMA 50"
        else:
            return "Precio entre EMAs"

    @staticmethod
    def classify_ema_cross(ema21: float, ema50: float) -> str:
        """
        Clasifica el cruce de EMAs.

        Returns:
            String descriptivo del cruce
        """
        if ema21 > ema50:
            return "EMA 21 sobre EMA 50 (golden cross)"
        else:
            return "EMA 21 bajo EMA 50 (death cross)"

    @staticmethod
    def classify_rsi(rsi: float) -> str:
        """
        Clasifica el RSI según rangos específicos.

        Returns:
            String descriptivo del estado RSI
        """
        if rsi < 35:
            return "RSI 0-35 (sobreventa)"
        elif 35 <= rsi <= 45:
            return "RSI 35-45 (zona neutral baja)"
        elif 45 < rsi <= 65:
            return "RSI entre 45-65 (momentum alcista sin sobrecompra)"
        elif 65 < rsi <= 100:
            return "RSI 65-100 (sobrecompra)"
        else:
            # Para casos de RSI entre 35-55 (rango bajista)
            if 35 <= rsi <= 55:
                return "RSI entre 35-55 (momentum bajista sin sobreventa)"
            return "RSI 55-65 (zona neutral alta)"

    @staticmethod
    def classify_bollinger_position(price: float, bb_upper: float, bb_lower: float,
                                    df: pd.DataFrame) -> str:
        """
        Clasifica la posición del precio respecto a las Bandas de Bollinger.

        Args:
            price: Precio actual
            bb_upper: Banda superior
            bb_lower: Banda inferior
            df: DataFrame con datos históricos

        Returns:
            String descriptivo del estado
        """
        # Obtener vela anterior
        prev_high = df['high'].iloc[-2] if len(df) >= 2 else price
        prev_low = df['low'].iloc[-2] if len(df) >= 2 else price
        prev_close = df['close'].iloc[-2] if len(df) >= 2 else price

        current_volume = df['volume'].iloc[-1]
        avg_volume = df['volume'].iloc[-6:-1].mean() if len(df) >= 6 else current_volume

        # Calcular distancias porcentuales
        distance_to_upper = ((bb_upper - price) / price) * 100
        distance_to_lower = ((price - bb_lower) / price) * 100

        # Precio cerca de banda inferior (dentro del 0.5%)
        if distance_to_lower < 0.5 and (prev_low <= bb_lower or prev_close <= bb_lower):
            return "Precio rebotando en BB inferior"

        # Precio rompiendo banda superior con volumen
        if price > bb_upper and current_volume > avg_volume:
            return "Precio rompiendo BB superior"

        # Precio cerca de banda superior sin romper
        if distance_to_upper < 0.5 and prev_high >= bb_upper and price < bb_upper:
            return "Precio rechazando BB superior"

        # Precio rompiendo banda inferior con volumen
        if price < bb_lower and current_volume > avg_volume:
            return "Precio rompiendo BB inferior"

        # En zona media
        return "Precio en zona media"

    @staticmethod
    def classify_macd(macd_line: float, macd_signal: float, histogram: float,
                     histogram_prev: float, histogram_prev2: float) -> Tuple[str, str]:
        """
        Clasifica el estado del MACD.

        Returns:
            Tupla (estado_linea, estado_histograma)
        """
        # Estado de línea
        if macd_line > macd_signal:
            line_state = "MACD línea sobre señal"
        else:
            line_state = "MACD línea bajo señal"

        # Estado de histograma
        if histogram > 0:
            # Histograma positivo (verde)
            if histogram > histogram_prev and histogram_prev > histogram_prev2:
                hist_state = "Histograma creciente verde (positivo)"
            else:
                hist_state = "Histograma decreciente verde"
        else:
            # Histograma negativo (rojo)
            if abs(histogram) > abs(histogram_prev) and abs(histogram_prev) > abs(histogram_prev2):
                hist_state = "Histograma decreciente rojo (negativo)"
            else:
                hist_state = "Histograma creciente rojo"

        return line_state, hist_state

    @staticmethod
    def classify_volume(volume_data: Dict[str, Any]) -> str:
        """
        Clasifica el estado del volumen.

        Returns:
            String descriptivo del estado
        """
        current = volume_data['current']
        avg = volume_data['avg_5']
        change_pct = volume_data['change_pct']
        bullish_candles = volume_data['bullish_candles']
        bearish_candles = volume_data['bearish_candles']
        total_candles = volume_data['total_candles']

        # Volumen significativamente alto (>20% sobre promedio)
        if change_pct > 20:
            if bullish_candles > bearish_candles:
                return "Volumen creciente en velas alcistas"
            elif bearish_candles > bullish_candles:
                return "Volumen creciente en velas bajistas"
            else:
                return "Volumen creciente"

        # Volumen significativamente bajo (<-20% bajo promedio)
        elif change_pct < -20:
            return "Volumen decreciente"

        # Volumen normal
        else:
            return "Volumen normal"

    @staticmethod
    def classify_vwap_position(price: float, vwap: float) -> str:
        """
        Clasifica la posición del precio respecto al VWAP.

        Returns:
            String descriptivo del estado
        """
        if price > vwap:
            return "Precio sobre VWAP"
        else:
            return "Precio bajo VWAP"

    @staticmethod
    def evaluate_long_conditions(indicators: Dict[str, Any], df: pd.DataFrame) -> Tuple[List[bool], int]:
        """
        Evalúa las 7 condiciones para LONG.

        Returns:
            Tupla (lista_de_condiciones, count_cumplidas)
        """
        conditions = []

        # 1. Precio sobre EMA 21 y EMA 50
        cond1 = indicators['price'] > indicators['ema21'] and indicators['price'] > indicators['ema50']
        conditions.append(cond1)

        # 2. EMA 21 sobre EMA 50 (golden cross)
        cond2 = indicators['ema21'] > indicators['ema50']
        conditions.append(cond2)

        # 3. RSI entre 45-65
        cond3 = 45 <= indicators['rsi'] <= 65
        conditions.append(cond3)

        # 4. Precio rebotando en BB inferior o rompiendo BB superior
        bb_state = ConditionEvaluator.classify_bollinger_position(
            indicators['price'],
            indicators['bb_upper'],
            indicators['bb_lower'],
            df
        )
        cond4 = bb_state in ["Precio rebotando en BB inferior", "Precio rompiendo BB superior"]
        conditions.append(cond4)

        # 5. MACD línea sobre señal + histograma creciente verde
        macd_line_state, macd_hist_state = ConditionEvaluator.classify_macd(
            indicators['macd_line'],
            indicators['macd_signal'],
            indicators['macd_histogram'],
            indicators['macd_histogram_prev'],
            indicators['macd_histogram_prev2']
        )
        cond5 = (macd_line_state == "MACD línea sobre señal" and
                 macd_hist_state == "Histograma creciente verde (positivo)")
        conditions.append(cond5)

        # 6. Volumen creciente en velas alcistas
        volume_state = ConditionEvaluator.classify_volume(indicators['volume'])
        cond6 = volume_state == "Volumen creciente en velas alcistas"
        conditions.append(cond6)

        # 7. Precio sobre VWAP
        cond7 = indicators['price'] > indicators['vwap']
        conditions.append(cond7)

        count = sum(conditions)
        return conditions, count

    @staticmethod
    def evaluate_short_conditions(indicators: Dict[str, Any], df: pd.DataFrame) -> Tuple[List[bool], int]:
        """
        Evalúa las 7 condiciones para SHORT.

        Returns:
            Tupla (lista_de_condiciones, count_cumplidas)
        """
        conditions = []

        # 1. Precio bajo EMA 21 y EMA 50
        cond1 = indicators['price'] < indicators['ema21'] and indicators['price'] < indicators['ema50']
        conditions.append(cond1)

        # 2. EMA 21 bajo EMA 50 (death cross)
        cond2 = indicators['ema21'] < indicators['ema50']
        conditions.append(cond2)

        # 3. RSI entre 35-55
        cond3 = 35 <= indicators['rsi'] <= 55
        conditions.append(cond3)

        # 4. Precio rechazando BB superior o rompiendo BB inferior
        bb_state = ConditionEvaluator.classify_bollinger_position(
            indicators['price'],
            indicators['bb_upper'],
            indicators['bb_lower'],
            df
        )
        cond4 = bb_state in ["Precio rechazando BB superior", "Precio rompiendo BB inferior"]
        conditions.append(cond4)

        # 5. MACD línea bajo señal + histograma decreciente rojo
        macd_line_state, macd_hist_state = ConditionEvaluator.classify_macd(
            indicators['macd_line'],
            indicators['macd_signal'],
            indicators['macd_histogram'],
            indicators['macd_histogram_prev'],
            indicators['macd_histogram_prev2']
        )
        cond5 = (macd_line_state == "MACD línea bajo señal" and
                 macd_hist_state == "Histograma decreciente rojo (negativo)")
        conditions.append(cond5)

        # 6. Volumen creciente en velas bajistas
        volume_state = ConditionEvaluator.classify_volume(indicators['volume'])
        cond6 = volume_state == "Volumen creciente en velas bajistas"
        conditions.append(cond6)

        # 7. Precio bajo VWAP
        cond7 = indicators['price'] < indicators['vwap']
        conditions.append(cond7)

        count = sum(conditions)
        return conditions, count

    @staticmethod
    def detect_changes(old_state: Dict[str, Any], new_state: Dict[str, Any],
                      timeframe: str) -> Dict[str, Any]:
        """
        Detecta cambios entre estados anterior y nuevo.

        Args:
            old_state: Estado anterior del timeframe
            new_state: Estado nuevo del timeframe
            timeframe: Nombre del timeframe (ej: "4h")

        Returns:
            Diccionario con los cambios detectados
        """
        changes = {
            'has_changes': False,
            'indicator_changes': [],
            'long_count_change': False,
            'short_count_change': False,
            'condition_changes': {
                'long': [],
                'short': []
            }
        }

        if not old_state:
            return changes

        # Comparar contadores
        if old_state['long_count'] != new_state['long_count']:
            changes['long_count_change'] = True
            changes['has_changes'] = True

        if old_state['short_count'] != new_state['short_count']:
            changes['short_count_change'] = True
            changes['has_changes'] = True

        # Comparar condiciones individuales
        for i in range(7):
            if old_state['long_conditions'][i] != new_state['long_conditions'][i]:
                changes['condition_changes']['long'].append({
                    'index': i,
                    'old': old_state['long_conditions'][i],
                    'new': new_state['long_conditions'][i]
                })
                changes['has_changes'] = True

            if old_state['short_conditions'][i] != new_state['short_conditions'][i]:
                changes['condition_changes']['short'].append({
                    'index': i,
                    'old': old_state['short_conditions'][i],
                    'new': new_state['short_conditions'][i]
                })
                changes['has_changes'] = True

        # Comparar valores de indicadores (cambios significativos)
        threshold = 0.5  # 0.5% cambio considerado significativo

        indicators_to_check = ['precio', 'ema21', 'ema50', 'rsi', 'macd_histograma']

        for indicator in indicators_to_check:
            if indicator in old_state and indicator in new_state:
                old_val = old_state[indicator]
                new_val = new_state[indicator]

                if old_val != 0:
                    pct_change = abs((new_val - old_val) / old_val) * 100
                    if pct_change >= threshold:
                        changes['indicator_changes'].append({
                            'name': indicator,
                            'old': old_val,
                            'new': new_val,
                            'pct_change': pct_change
                        })
                        changes['has_changes'] = True

        return changes
