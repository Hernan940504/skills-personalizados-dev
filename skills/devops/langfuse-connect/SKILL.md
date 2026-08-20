---
name: langfuse-connect
description: Conecta a la API pública de Langfuse y valida el consumo de LLM (modelo exacto, tokens de entrada/salida, costo en USD y factor de amplificación generaciones/traza). Cada proyecto tiene su carpeta en proyectos/ con su config.env (host y public key) y un secret.env gitignored para la secret key. Úsalo cuando quieras auditar cuánto y con qué modelo consume una app instrumentada con Langfuse (p.ej. MIA), confrontar el consumo de LLM con la facturación del proveedor (Vertex/Gemini, OpenAI), o depurar amplificación de llamadas por conversación.
version: 1.0.0
author: Hernan940504
category: devops
tags: [langfuse, llm, observability, gemini, vertex, openai, tokens, costos, finops, mia]
compatibility: [claude-code, cursor, kiro, opencode]
allowed-tools: [Bash, Read, Write]
examples:
  - prompt: "valida en Langfuse qué modelo y cuántos tokens consume MIA"
  - prompt: "confronta el consumo de Gemini de GCP con las trazas de Langfuse"
  - prompt: "cuánto está costando MIA en LLM este mes según Langfuse"
  - prompt: "cuántas llamadas al modelo hace MIA por conversación (amplificación)"
  - prompt: "conéctate a Langfuse del proyecto mia-ciencuadras"
---

# Langfuse Connect

Consulta la **API pública de Langfuse** para auditar el consumo de LLM de una aplicación
instrumentada (trazas → generaciones). Es el complemento del lado "observabilidad" a los
skills de facturación/infra: mientras `gcp-connect` mide llamadas a Gemini en GCP y el
tráfico se ve en AWS, **Langfuse dice el modelo exacto, los tokens y el costo por llamada**,
y permite calcular la **amplificación** (cuántas generaciones LLM ocurren por conversación).

## Cuándo usar este skill

- Quieres saber **con qué modelo** (p.ej. `gemini-2.5-flash` vs `gpt-4o`) y **cuántos tokens**
  consume una app, para ponerle **costo en USD**.
- Necesitas **confrontar** el consumo de LLM medido por el proveedor (Vertex/Gemini en GCP,
  OpenAI) contra lo que la app realmente registra en Langfuse.
- Quieres medir **amplificación**: generaciones LLM por traza/conversación, y si subió con el tiempo.
- Depurar picos de costo o de llamadas (flujos agénticos, reintentos).

## Cuándo NO usar

- La app **no está instrumentada con Langfuse** (no hay trazas que consultar).
- Solo quieres **renovar credenciales de nube** → usa `aws-sso-refresh` / `gcp-connect`.
- Quieres **gestión de prompts** vía MCP oficial de Langfuse: ese caso lo cubre el MCP de
  Langfuse (prompt management), no este skill (analítica de trazas/tokens por REST).

## Modelo mental (patrón de los otros skills)

| gcp-connect / aws-sso-refresh | langfuse-connect |
|---|---|
| `proyectos|cuentas/<x>/config.env` | `proyectos/<x>/config.env` (HOST + PUBLIC_KEY) |
| credencial de nube | `secret.env` con `LANGFUSE_SECRET_KEY` (gitignored) |
| CLI del proveedor | API REST de Langfuse (`/api/public/...`) |

## Workflow

### 1. Configurar el proyecto

Copia `proyectos/_ejemplo/` a `proyectos/<tu-proyecto>/` (o usa el ya creado
`proyectos/mia-ciencuadras/`) y completa:

- `config.env` → `LANGFUSE_HOST` y `LANGFUSE_PUBLIC_KEY`.
- `secret.env`  → `LANGFUSE_SECRET_KEY=sk-lf-...`  (este archivo está gitignored).

Las llaves se generan en Langfuse: **Settings → API Keys** del proyecto.

### 2. Probar conexión

```bash
bash scripts/langfuse.sh mia-ciencuadras ping
```

### 3. Validar consumo (informe principal)

```bash
bash scripts/langfuse.sh mia-ciencuadras validate --days 30
# confrontando con el nº de llamadas Gemini medido en GCP:
bash scripts/langfuse.sh mia-ciencuadras validate --days 30 --gcp-calls 404211
```

Devuelve: trazas, generaciones, **amplificación (gen/traza)**, costo total, desglose
**Gemini vs otros**, tabla por modelo (tokens y USD) y la evolución de la amplificación
(1ª vs 2ª mitad del periodo).

### Otros comandos

```bash
bash scripts/langfuse.sh mia-ciencuadras daily  --days 90            # serie diaria
bash scripts/langfuse.sh mia-ciencuadras models --days 30 --grep gemini
```

Rangos: `--days N` o `--from YYYY-MM-DD --to YYYY-MM-DD`.

## Recursos

- `scripts/langfuse_query.py` — cliente REST + agregaciones (solo stdlib de Python).
- `scripts/langfuse.sh` — wrapper que carga la config del proyecto y ejecuta el comando.
- `proyectos/<x>/config.env` — host + public key.
- `proyectos/<x>/secret.env` — secret key (gitignored).

## API que usa

- `GET /api/public/projects` — verificación de credenciales (`ping`).
- `GET /api/public/metrics/daily` — métricas diarias con `usage[]` por modelo (tokens y costo).

Autenticación: HTTP Basic con `public_key:secret_key`.

## Anti-patrones

- **No commitear** `secret.env` ni llaves reales; el `.gitignore` del skill ya excluye
  `secret.env` y los `config.env` de proyectos reales (solo se versiona `_ejemplo`).
- No hardcodear el host/llaves en scripts; usar siempre la config del proyecto.
- No traer las llaves de Langfuse desde Secrets Manager de producción a la terminal
  (materializa un secreto); pídelas en la UI de Langfuse o al equipo dueño.
