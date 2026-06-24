---
name: {{name}}
description: {{TODO — description densa siguiendo SKILL-FORMAT.md §4. Empieza con verbo,
  menciona el stack/herramienta y añade "Úsalo cuando…" con señales de activación. ≤500 chars.}}
version: 0.1.0
author: {{author}}
category: {{category}}
tags: [{{tag1}}, {{tag2}}]
compatibility: [claude-code, cursor, kiro, opencode]
allowed-tools: [Read, Edit, Write, Bash, Grep, Glob]
examples:
  - prompt: "{{ejemplo de prompt que activa el skill}}"
---

# {{Título humano}}

## Cuándo usar este skill

- {{señal de activación 1}}
- {{señal de activación 2}}

## Cuándo NO usar

- {{caso límite donde otro skill encaja mejor}}

## Convenciones

- {{regla concreta del stack, una por línea}}

## Workflow

1. {{paso, idealmente referenciando scripts/ y templates/}}

## Recursos

- `scripts/{{...}}` — {{qué hace}}
- `templates/{{...}}` — {{qué genera}}
- `references/{{...}}` — {{qué consultar y cuándo}}

## Anti-patrones

- {{error común a evitar}}
