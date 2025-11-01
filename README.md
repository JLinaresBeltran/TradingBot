# Análisis Técnico ETHUSDT Futuros Binance

Script en Python para análisis técnico automatizado de ETHUSDT en Binance Futures utilizando 7 indicadores técnicos con gestión de riesgo automática.

## Características

- **Análisis Inicial**: Evalúa 3 timeframes (4h, 1h, 15min) con datos completos
- **Actualización Inteligente**: Solo actualiza timeframes con velas cerradas (optimizado)
- **Timing de Entrada**: Análisis detallado en timeframe de 5 minutos
- **7 Indicadores Técnicos**: EMA, RSI, Bandas de Bollinger, MACD, Volumen, VWAP, ATR
- **Gestión de Riesgo ATR**: Cálculo automático de SL y 3 niveles de TP cuando hay señal válida (≥5/7 condiciones)
- **Datos Híbridos**: MACD y Volumen de SPOT, resto de indicadores de FUTUROS
- **Reportes Automatizados**: Guarda análisis en archivos de texto con timestamp
- **Optimizado para Memoria**: Límite de 50 velas para máxima eficiencia

## Indicadores Utilizados

1. **EMA 21 y EMA 50** - Tendencia a corto y medio plazo
2. **RSI 14** - Momentum y zonas de sobrecompra/sobreventa
3. **Bandas de Bollinger (20,2)** - Volatilidad y extremos
4. **MACD (12,26,9)** - Cambios de momentum (datos SPOT)
5. **Volumen** - Confirmación de movimientos (datos SPOT)
6. **VWAP** - Precio promedio ponderado por volumen
7. **ATR 14** - Gestión de riesgo y volatilidad

## Requisitos

- Python 3.8 o superior
- Conexión a internet (para API de Binance)

## Instalación

1. Clonar o descargar el repositorio

2. Crear entorno virtual (recomendado):
```bash
python3 -m venv venv
source venv/bin/activate  # En macOS/Linux
# o
venv\Scripts\activate  # En Windows
```

3. Instalar dependencias:
```bash
pip install -r requirements.txt
```

## Uso

### Ejecutar el Script

```bash
# Activar entorno virtual primero
source venv/bin/activate  # En macOS/Linux
# o
venv\Scripts\activate  # En Windows

# Ejecutar script
python3 analisis_tecnico.py  # En macOS/Linux
# o
python analisis_tecnico.py  # En Windows
```

### Menú Principal

```
=== ANÁLISIS TÉCNICO ETHUSDT FUTUROS ===

Seleccione una opción:

1. ANÁLISIS INICIAL (4h, 1h, 15min)
2. ACTUALIZACIÓN 15 MINUTOS (4h, 1h, 15min)
3. ANÁLISIS 5 MINUTOS (timing de entrada)
4. Salir
```

### Opción 1: Análisis Inicial

**Cuándo usar**: Primera ejecución del día o cuando inicias una sesión de trading

**Qué hace**:
- Analiza 3 timeframes: 4 horas, 1 hora y 15 minutos
- Calcula todos los indicadores técnicos
- Evalúa 7 condiciones LONG y 7 condiciones SHORT
- Guarda el estado inicial en `estado.json`
- Genera reporte completo en `reportes/analisis_inicial_YYYYMMDD_HHMMSS.txt`

**Salida**:
- Todos los valores de indicadores
- Estados clasificados según criterios
- Checklist de condiciones LONG (X/7 cumplidas)
- Checklist de condiciones SHORT (Y/7 cumplidas)

### Opción 2: Actualización 15 Minutos

**Cuándo usar**: Para monitoreo continuo después del análisis inicial

**Requisito**: Debe existir un análisis inicial previo (Opción 1)

**Qué hace**:
- Verifica qué timeframes tienen velas cerradas
- **Solo actualiza timeframes con velas nuevas** (optimizado para eficiencia)
- Compara con el estado anterior
- Detecta cambios en indicadores y condiciones
- Actualiza el archivo `estado.json`
- Genera reporte en `reportes/actualizacion_N_YYYYMMDD_HHMMSS.txt`

**Salida**:
- **Timeframes actualizados**: Muestra cambios detectados con formato "antes → después"
- **Timeframes omitidos**: Indica cuáles no se actualizaron (vela en progreso)
- **Gestión de Riesgo**: Si hay señal válida (≥5/7 condiciones), muestra SL y 3 TP basados en ATR

### Opción 3: Análisis 5 Minutos

**Cuándo usar**: Para timing preciso de entrada cuando ya identificaste una dirección

**Qué hace**:
- Analiza SOLO el timeframe de 5 minutos
- Calcula distancias porcentuales a niveles clave
- Analiza momentum inmediato (últimas 3 velas cerradas)
- Proyecta tiempo restante para cierre de vela
- Genera reporte en `reportes/analisis_5min_YYYYMMDD_HHMMSS.txt`

**Salida**:
- Análisis detallado del timeframe 5min
- Distancias porcentuales a EMAs, BBs y VWAP
- Momentum inmediato de corto plazo
- Evaluación completa de condiciones LONG/SHORT
- **Gestión de Riesgo**: Si hay señal válida (≥5/7 condiciones), muestra SL y 3 TP basados en ATR

## Criterios de Evaluación

### Condiciones LONG (Alcista)

1. ✅ Precio sobre EMA 21 y EMA 50
2. ✅ EMA 21 sobre EMA 50 (golden cross)
3. ✅ RSI entre 45-65 (momentum alcista sin sobrecompra)
4. ✅ Precio rebotando en BB inferior o rompiendo BB superior
5. ✅ MACD línea sobre señal + histograma creciente verde
6. ✅ Volumen creciente en velas alcistas
7. ✅ Precio sobre VWAP

### Condiciones SHORT (Bajista)

1. ✅ Precio bajo EMA 21 y EMA 50
2. ✅ EMA 21 bajo EMA 50 (death cross)
3. ✅ RSI entre 35-55 (momentum bajista sin sobreventa)
4. ✅ Precio rechazando BB superior o rompiendo BB inferior
5. ✅ MACD línea bajo señal + histograma decreciente rojo
6. ✅ Volumen creciente en velas bajistas
7. ✅ Precio bajo VWAP

### Gestión de Riesgo (ATR)

Cuando hay **señal válida (≥5/7 condiciones)**, el script calcula automáticamente:

**Para LONG:**
- **SL (Stop Loss)**: Precio - (1.5 × ATR)
- **TP1 (Take Profit 1)**: Precio + (1.0 × ATR) - Risk/Reward 1:0.67
- **TP2 (Take Profit 2)**: Precio + (2.0 × ATR) - Risk/Reward 1:1.33
- **TP3 (Take Profit 3)**: Precio + (3.0 × ATR) - Risk/Reward 1:2.00

**Para SHORT:**
- **SL (Stop Loss)**: Precio + (1.5 × ATR)
- **TP1 (Take Profit 1)**: Precio - (1.0 × ATR) - Risk/Reward 1:0.67
- **TP2 (Take Profit 2)**: Precio - (2.0 × ATR) - Risk/Reward 1:1.33
- **TP3 (Take Profit 3)**: Precio - (3.0 × ATR) - Risk/Reward 1:2.00

El ATR se calcula con período 14 y se adapta a la volatilidad actual del mercado.

## Estructura del Proyecto

```
TradingBot/
├── analisis_tecnico.py      # Script principal
├── requirements.txt          # Dependencias
├── README.md                 # Documentación
├── .gitignore               # Archivos ignorados
├── estado.json              # Estado guardado (generado automáticamente)
├── src/
│   ├── __init__.py
│   ├── binance_client.py    # Cliente API Binance
│   ├── indicators.py        # Cálculo de indicadores
│   ├── evaluator.py         # Evaluación de condiciones
│   └── reporter.py          # Generación de reportes
└── reportes/                # Reportes generados (automático)
    ├── analisis_inicial_*.txt
    ├── actualizacion_*.txt
    └── analisis_5min_*.txt
```

## Archivos Generados

### estado.json
Archivo que mantiene el estado del análisis (optimizado, ~3KB):
- Timestamp del análisis inicial
- Contador de actualizaciones
- Valores de todos los indicadores por timeframe (incluye ATR)
- Condiciones LONG/SHORT cumplidas
- SL/TP calculados para señales válidas
- Timestamps de última vela cerrada por timeframe

### Reportes (.txt)
Archivos de texto con el análisis formateado:
- `analisis_inicial_YYYYMMDD_HHMMSS.txt` - Análisis completo inicial
- `actualizacion_N_YYYYMMDD_HHMMSS.txt` - Actualizaciones con cambios detectados
- `analisis_5min_YYYYMMDD_HHMMSS.txt` - Análisis detallado de 5 minutos

## Flujo de Trabajo Recomendado

1. **Inicio del día**:
   - Ejecutar Opción 1 (Análisis Inicial)
   - Revisar los 3 timeframes y condiciones

2. **Monitoreo continuo**:
   - Ejecutar Opción 2 cada 15 minutos (o cuando desees)
   - Revisar cambios detectados

3. **Identificación de oportunidad**:
   - Cuando timeframes mayores muestren confluencia (≥5/7 condiciones)
   - El script mostrará automáticamente SL y 3 niveles de TP
   - Ejecutar Opción 3 para timing preciso

4. **Entrada al mercado**:
   - Usar Opción 3 para confirmar momentum de corto plazo
   - Verificar que también tenga ≥5/7 condiciones para confirmar gestión de riesgo
   - Determinar punto exacto de entrada usando niveles calculados

5. **Seguimiento**:
   - Continuar con Opción 2 para monitoreo
   - Usar Opción 3 para ajustes o salidas

## Importante

### El script NO incluye:
- ❌ Interpretaciones de los datos
- ❌ Recomendaciones de trading
- ❌ Señales de compra/venta
- ❌ Conclusiones sobre qué hacer

### El script SÍ entrega:
- ✅ Datos numéricos procesados
- ✅ Estados clasificados de indicadores
- ✅ Cumplimiento de condiciones (✅/❌)
- ✅ Contadores objetivos (X/7)

**El análisis y toma de decisiones es responsabilidad del usuario.**

## Optimizaciones de Rendimiento

El script está optimizado para **máxima eficiencia y mínimo uso de memoria**:

1. **Límite de velas**: Solo solicita 50 velas (suficientes para todos los indicadores)
2. **Actualización inteligente**: Solo actualiza timeframes con velas cerradas
3. **Estado compacto**: archivo estado.json optimizado (~3KB vs MB anteriormente)
4. **Verificación previa**: Revisa velas antes de hacer análisis completo

Estos cambios permiten:
- ✅ Ejecutar sin problemas de memoria
- ✅ Respuestas más rápidas de la API
- ✅ Menor consumo de recursos
- ✅ Precisión 100% mantenida (50 velas son suficientes para EMA50)

## Manejo de Errores

El script maneja automáticamente:
- Problemas de conexión a internet
- Rate limits de la API de Binance
- Timeouts en solicitudes
- Validación de datos insuficientes
- Errores en cálculos de indicadores

## Fuentes de Datos

El script utiliza un enfoque **híbrido** para máxima precisión:

### Binance Futures (mayoría de indicadores)
- EMA 21 y EMA 50
- RSI 14
- Bandas de Bollinger
- VWAP
- ATR 14
- Precio actual

### Binance Spot (MACD y Volumen)
- MACD (12,26,9) - Usa datos SPOT para mayor precisión
- Volumen - Usa datos SPOT para análisis más confiable

**Nota**: Ambas APIs son públicas, no requieren autenticación ni API keys, y solo obtienen datos de mercado (sin realizar operaciones de trading).