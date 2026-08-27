# Changelog — dev

## [No publicado]

### Agregado
- Se creó script `scripts/jira_update_issues.py` para actualizar issues en Jira reemplazando referencias de TASD-1 por TASD-4 en summary y description
- Se configuró integración con Langfuse MCP para análisis de comportamiento del agente conversacional
- Se creó steering file `langfuse-agent-analysis.md` con flujo de análisis de transferencias a agentes humanos
- Se generó informe completo de comportamiento del agente Victoria (informe-victoria-agent-behavior.html) con análisis mes a mes desde Mayo 2026
- Se creó el skill `docs-prd-aidlc` (categoría docs) para definir PRDs de productos como insumo del framework AI-DLC de AWS, adaptado a los guardrails de Seguros Bolívar: SKILL.md, README.md, plantilla de PRD de 9 secciones + bloque AI-DLC, 4 references (guía de llenado, mapeo a fases AI-DLC, guardrails corporativos, checklist) y script scaffold `new-prd.sh`
