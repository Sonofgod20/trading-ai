# Sistema de Trading AI - Documentación del Sistema

## Datos del Sistema

### Market Data
El sistema actualmente procesa y envía los siguientes datos de mercado:

De Binance:
- Precio actual (last_price)
- Cambio de precio (price_change_percent)
- Tasa de financiación (funding_rate)
- Precio mark (mark_price)
- Volumen de trading (quote_volume)

### Order Book
Se analiza y envía la siguiente información del libro de órdenes:
- Presión de compra (buy_pressure)
- Presión de venta (sell_pressure)
- Spread del mercado (spread_percentage)
- Paredes de órdenes (bid_walls y ask_walls)
- Zonas de liquidez (liquidity_zones)

## Arquitectura General

El sistema está organizado en los siguientes módulos principales:

```
trading-ai-main/
├── src/
│   ├── analysis/         # Análisis técnico y de mercado
│   ├── trading/         # Ejecución de operaciones
│   └── ui/             # Interfaz de usuario y visualización
├── data/               # Datos históricos y de mercado
└── models/            # Modelos y base de conocimiento
```

## Componentes Críticos

### 1. Análisis de Mercado
- `src/analysis/market_data/market_analyzer.py`: Análisis de datos de mercado
- `src/analysis/indicators/technical_indicators.py`: Indicadores técnicos
- `src/analysis/patterns/candlestick_patterns.py`: Patrones de velas
- **RIESGO**: Modificaciones en estos componentes pueden afectar las señales de trading

### 2. Ejecución de Trading
- `trading_ai.py`: Punto de entrada principal
- `binance_futures.py`: Integración con Binance Futures
- `position_tracker.py`: Seguimiento de posiciones
- **RIESGO**: Cambios aquí afectan directamente las operaciones en vivo

### 3. Interfaz de Usuario
- `src/ui/`: Componentes de visualización y charts
- **RIESGO**: Mantener consistencia en la visualización de datos

## Guía de Mantenimiento

### Reglas Generales
1. **NO MODIFICAR**:
   - Lógica core de trading en `trading_ai.py`
   - Cálculos de indicadores existentes
   - Manejo de posiciones en `position_tracker.py`

2. **PRECAUCIÓN AL MODIFICAR**:
   - Análisis de patrones
   - Configuraciones de riesgo
   - Integración con exchange

3. **SEGURO MODIFICAR**:
   - Componentes UI no críticos
   - Documentación
   - Tests

### Proceso de Actualización
1. Crear backup de archivos a modificar
2. Realizar cambios incrementales
3. Probar en ambiente de desarrollo
4. Validar sin operaciones en vivo
5. Implementar gradualmente

## Base de Conocimiento
- `models/knowledge_base/trading_strategies.txt`: Estrategias implementadas
- Mantener documentadas las estrategias y sus parámetros

## Datos
- `data/market_data/`: Datos históricos y en tiempo real
- **IMPORTANTE**: No eliminar datos históricos

## Consideraciones de Seguridad
1. Verificar permisos API de Binance
2. Mantener límites de riesgo
3. Backup regular de configuraciones
4. Monitoreo de operaciones

## Proceso de Desarrollo
1. Desarrollar en ramas separadas
2. Testing exhaustivo antes de producción
3. Documentar cambios
4. Mantener logs de modificaciones

## Recuperación ante Fallos
1. Mantener copias de seguridad
2. Documentar procedimientos de rollback
3. Tener plan de contingencia para fallos críticos

## Mejores Prácticas
1. Seguir estándares de código Python
2. Mantener modularidad
3. Documentar cambios significativos
4. Testing antes de producción
5. Monitoreo constante

## Notas Importantes
- El sistema está diseñado para operar en futuros de Binance
- Mantener separación de responsabilidades entre módulos
- Priorizar estabilidad sobre nuevas características
- Documentar cualquier cambio en parámetros de trading

## Contacto y Soporte
- Mantener registro de incidentes
- Documentar soluciones implementadas
- Actualizar guías según sea necesario
