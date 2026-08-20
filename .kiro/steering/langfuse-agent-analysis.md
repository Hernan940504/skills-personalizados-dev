---
inclusion: manual
---

# Langfuse — Análisis de Comportamiento del Agente y Transferencias

## Proyecto

- **Nombre**: Victoria
- **Project ID**: cm2kl5wij0vueqzz4t6zdsjdd
- **Organización**: El Libertador
- **Org ID**: cm2kl48wm0vypkr7gzgruattw
- **Host**: https://us.cloud.langfuse.com

## Objetivo

Analizar las conversaciones del agente conversacional para identificar:
1. **Resolución autónoma**: Casos donde el agente resuelve sin intervención humana
2. **Transferencias a agentes humanos**: Casos donde transfiere y por qué
3. **Patrones problemáticos**: Identificar por qué transfiere excesivamente

## Herramientas MCP Disponibles (langfuse-mcp)

### Para análisis de trazas y sesiones
- `fetch_traces` — Obtener trazas del agente (conversaciones completas)
- `fetch_trace` — Detalle de una traza específica
- `fetch_observations` — Observaciones dentro de una traza (pasos, decisiones)
- `fetch_observation` — Detalle de una observación
- `fetch_sessions` — Sesiones de usuario
- `get_session_details` — Detalle de sesión completa
- `get_user_sessions` — Sesiones por usuario

### Para análisis de routing/transferencia
- `find_route_decisions` — Decisiones de enrutamiento (transferencias)
- `get_route_decision` — Detalle de una decisión de routing
- `summarize_route_decisions` — Resumen agregado de decisiones
- `find_low_confidence_route_decisions` — Decisiones con baja confianza

### Para excepciones y errores
- `find_exceptions` — Errores que pudieron causar transferencias
- `get_exception_details` — Detalle del error

### Para métricas
- `query_metrics` — Métricas agregadas (costo, latencia, conteos)
- `get_metrics_schema` — Esquema de métricas disponible

## Flujo de Análisis Recomendado

### Paso 1: Panorama general
```
fetch_traces(limit=100, order_by="timestamp", order="DESC")
```
Revisar las trazas recientes para identificar el volumen total.

### Paso 2: Identificar transferencias
```
find_route_decisions(limit=50)
summarize_route_decisions()
```
Buscar decisiones de routing que indiquen transferencia a humano.

### Paso 3: Analizar baja confianza
```
find_low_confidence_route_decisions(threshold=0.5)
```
Identificar casos donde el agente no tiene confianza para resolver.

### Paso 4: Comparar resoluciones vs transferencias
Buscar en las trazas patrones como:
- Metadata con `transfer`, `handoff`, `escalation`, `human_agent`
- Observaciones con nombres como `route_to_human`, `transfer_decision`
- Scores o tags que indiquen resolución exitosa vs transferencia

### Paso 5: Clasificar motivos de transferencia
Categorizar por:
- **Complejidad del tema**: El agente no puede resolver por limitaciones de conocimiento
- **Solicitud explícita del usuario**: El usuario pide hablar con un humano
- **Falla técnica**: Error o timeout que fuerza la transferencia
- **Política de negocio**: Reglas que exigen intervención humana (ej: reclamos, cancelaciones)
- **Baja confianza**: El modelo no está seguro de su respuesta

### Paso 6: Métricas de impacto
```
query_metrics(
    view="traces",
    metrics=[{"measure": "count", "aggregation": "sum"}],
    dimensions=["tags"],
    age=10080
)
```
Cuantificar el impacto: % de transferencias vs resoluciones autónomas.

## Preguntas Clave para el Análisis

1. ¿Qué porcentaje de conversaciones se transfieren a humanos?
2. ¿En qué punto de la conversación ocurre la transferencia? (turno 1, 2, 3+)
3. ¿Qué temas/intenciones se transfieren más frecuentemente?
4. ¿Hay transferencias que el agente podría haber resuelto solo?
5. ¿Cuáles son los top 5 motivos de transferencia?
6. ¿Hay patrones temporales? (más transferencias en ciertos horarios/días)
7. ¿La confianza del modelo correlaciona con las transferencias?

## Campos a Buscar en las Trazas

Dependiendo de cómo esté instrumentado el agente, buscar en metadata/tags:
- `action: transfer_to_human` / `action: resolved`
- `transfer_reason: *`
- `confidence_score: <float>`
- `intent: *`
- `resolution_type: autonomous | human_assisted | transferred`
- `escalation_level: *`

## Formato de Reporte

Al finalizar el análisis, estructurar hallazgos como:

```markdown
## Resumen Ejecutivo
- Total conversaciones analizadas: X
- Resueltas autónomamente: X (Y%)
- Transferidas a humano: X (Y%)

## Top Motivos de Transferencia
1. [Motivo] — X% de transferencias
2. [Motivo] — X% de transferencias

## Casos donde el agente PUEDE resolver solo
- [Patrón identificado]

## Recomendaciones
- [Acción concreta para reducir transferencias]
```
