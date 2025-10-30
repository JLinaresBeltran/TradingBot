"""
Cliente para interactuar con la API de Binance Futures.
Obtiene datos de velas (klines) incluyendo la vela en progreso.
"""

import requests
from datetime import datetime, timezone
from typing import List, Dict, Any
import time


class BinanceClient:
    """Cliente para API pública de Binance Futures"""

    BASE_URL = "https://fapi.binance.com"

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'User-Agent': 'TradingBot/1.0'
        })

    def get_klines(self, symbol: str, interval: str, limit: int = 200) -> List[Dict[str, Any]]:
        """
        Obtiene velas (klines) para un símbolo e intervalo específico.
        Incluye la vela actual en progreso.

        Args:
            symbol: Par de trading (ej: "ETHUSDT")
            interval: Timeframe (ej: "4h", "1h", "15m", "5m")
            limit: Número de velas a obtener (máximo 1500)

        Returns:
            Lista de diccionarios con datos de velas

        Raises:
            ConnectionError: Si hay problemas de conexión
            ValueError: Si la respuesta de la API es inválida
        """
        endpoint = f"{self.BASE_URL}/fapi/v1/klines"

        params = {
            'symbol': symbol,
            'interval': interval,
            'limit': limit
        }

        max_retries = 3
        retry_delay = 1  # segundos

        for attempt in range(max_retries):
            try:
                response = self.session.get(endpoint, params=params, timeout=10)

                # Manejar rate limits
                if response.status_code == 429:
                    retry_after = int(response.headers.get('Retry-After', 60))
                    raise ConnectionError(f"Rate limit excedido. Esperar {retry_after} segundos")

                response.raise_for_status()

                data = response.json()

                if not isinstance(data, list) or len(data) == 0:
                    raise ValueError("Respuesta de API inválida o vacía")

                # Convertir datos a formato más manejable
                klines = []
                for k in data:
                    kline = {
                        'open_time': k[0],
                        'open': float(k[1]),
                        'high': float(k[2]),
                        'low': float(k[3]),
                        'close': float(k[4]),
                        'volume': float(k[5]),
                        'close_time': k[6],
                        'quote_volume': float(k[7]),
                        'trades': int(k[8]),
                        'taker_buy_base': float(k[9]),
                        'taker_buy_quote': float(k[10])
                    }
                    klines.append(kline)

                return klines

            except requests.exceptions.Timeout:
                if attempt < max_retries - 1:
                    time.sleep(retry_delay * (attempt + 1))
                    continue
                raise ConnectionError("Timeout al conectar con Binance API")

            except requests.exceptions.ConnectionError:
                if attempt < max_retries - 1:
                    time.sleep(retry_delay * (attempt + 1))
                    continue
                raise ConnectionError("Error de conexión con Binance API. Verificar internet")

            except requests.exceptions.RequestException as e:
                raise ConnectionError(f"Error en solicitud a Binance API: {str(e)}")

        raise ConnectionError("Máximo número de reintentos alcanzado")

    def get_klines_spot(self, symbol: str, interval: str, limit: int = 200) -> List[Dict[str, Any]]:
        """
        Obtiene velas (klines) del mercado SPOT para un símbolo e intervalo específico.
        Incluye la vela actual en progreso.

        Args:
            symbol: Par de trading (ej: "ETHUSDT")
            interval: Timeframe (ej: "4h", "1h", "15m", "5m")
            limit: Número de velas a obtener (máximo 1500)

        Returns:
            Lista de diccionarios con datos de velas

        Raises:
            ConnectionError: Si hay problemas de conexión
            ValueError: Si la respuesta de la API es inválida
        """
        # URL para mercado SPOT
        endpoint = "https://api.binance.com/api/v3/klines"

        params = {
            'symbol': symbol,
            'interval': interval,
            'limit': limit
        }

        max_retries = 3
        retry_delay = 1  # segundos

        for attempt in range(max_retries):
            try:
                response = self.session.get(endpoint, params=params, timeout=10)

                # Manejar rate limits
                if response.status_code == 429:
                    retry_after = int(response.headers.get('Retry-After', 60))
                    raise ConnectionError(f"Rate limit excedido. Esperar {retry_after} segundos")

                response.raise_for_status()

                klines_data = response.json()

                # Convertir a formato consistente
                result = []
                for kline in klines_data:
                    result.append({
                        'open_time': kline[0],
                        'open': float(kline[1]),
                        'high': float(kline[2]),
                        'low': float(kline[3]),
                        'close': float(kline[4]),
                        'volume': float(kline[5]),
                        'close_time': kline[6],
                        'quote_volume': float(kline[7]),
                        'trades': int(kline[8]),
                        'taker_buy_base': float(kline[9]),
                        'taker_buy_quote': float(kline[10])
                    })

                return result

            except requests.exceptions.HTTPError as e:
                if attempt < max_retries - 1:
                    time.sleep(retry_delay * (attempt + 1))
                    continue
                raise ConnectionError("Error de conexión con Binance SPOT API. Verificar internet")

            except requests.exceptions.RequestException as e:
                raise ConnectionError(f"Error en solicitud a Binance SPOT API: {str(e)}")

        raise ConnectionError("Máximo número de reintentos alcanzado")

    def get_current_price(self, symbol: str) -> float:
        """
        Obtiene el precio actual del símbolo.

        Args:
            symbol: Par de trading (ej: "ETHUSDT")

        Returns:
            Precio actual como float
        """
        endpoint = f"{self.BASE_URL}/fapi/v1/ticker/price"

        params = {'symbol': symbol}

        try:
            response = self.session.get(endpoint, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            return float(data['price'])
        except Exception as e:
            raise ConnectionError(f"Error obteniendo precio actual: {str(e)}")

    @staticmethod
    def calculate_candle_completion(open_time: int, close_time: int) -> tuple:
        """
        Calcula el porcentaje de completitud de una vela y tiempo restante.

        Args:
            open_time: Timestamp de apertura de vela (ms)
            close_time: Timestamp de cierre de vela (ms)

        Returns:
            Tupla (porcentaje_completado, segundos_restantes)
        """
        now_ms = int(datetime.now(timezone.utc).timestamp() * 1000)

        total_duration = close_time - open_time
        elapsed = now_ms - open_time

        if elapsed < 0:
            return 0.0, total_duration // 1000
        if elapsed > total_duration:
            return 100.0, 0

        percentage = (elapsed / total_duration) * 100
        remaining_seconds = (close_time - now_ms) // 1000

        return round(percentage, 1), max(0, remaining_seconds)

    @staticmethod
    def format_candle_time(open_time: int, close_time: int, interval: str) -> str:
        """
        Formatea el rango de tiempo de una vela.

        Args:
            open_time: Timestamp de apertura (ms)
            close_time: Timestamp de cierre (ms)
            interval: Intervalo de la vela

        Returns:
            String formateado (ej: "04:00-08:00")
        """
        open_dt = datetime.fromtimestamp(open_time / 1000, tz=timezone.utc)
        close_dt = datetime.fromtimestamp(close_time / 1000, tz=timezone.utc)

        # Para timeframes de 4h o más, incluir fecha si es diferente
        if interval in ['4h', '1d', '1w']:
            if open_dt.date() != close_dt.date():
                return f"{open_dt.strftime('%Y-%m-%d %H:%M')}-{close_dt.strftime('%Y-%m-%d %H:%M')}"
            return f"{open_dt.strftime('%H:%M')}-{close_dt.strftime('%H:%M')}"
        else:
            # Para timeframes menores, solo mostrar hora
            return f"{open_dt.strftime('%H:%M')}-{close_dt.strftime('%H:%M')}"

    def test_connection(self) -> bool:
        """
        Prueba la conexión con la API de Binance.

        Returns:
            True si la conexión es exitosa, False en caso contrario
        """
        endpoint = f"{self.BASE_URL}/fapi/v1/ping"

        try:
            response = self.session.get(endpoint, timeout=5)
            return response.status_code == 200
        except:
            return False
