---
name: docs-prd-aidlc
description: Crea el PRD (Product Requirements Document) de un producto o
  iniciativa de Seguros Bolívar como insumo del framework AI-DLC de AWS. Conduce
  una entrevista guiada de 9 secciones (problema, sponsor, estado actual/futuro,
  criterios de éxito, restricciones, IA, riesgos, alcance), cuantifica cada
  afirmación y produce un PRD en Markdown con un intent listo para `/aidlc`.
  Úsalo cuando pidan "definir un PRD", "internal solution brief", "product
  vision board" o "insumo para AI-DLC".
version: 0.1.0
author: Hernan940504
category: docs
tags: [prd, product, aidlc, aws, seguros-bolivar, discovery, ai-native, requirements]
compatibility: [claude-code, cursor, kiro, opencode]
allowed-tools: [Read, Write, Bash, Glob, Grep]
examples:
  - prompt: "ayúdame a definir el PRD del nuevo producto de cotización de vida"
  - prompt: "quiero preparar el insumo para AI-DLC de mi iniciativa de agentes"
  - prompt: "necesito un internal solution brief para un problema interno"
  - prompt: "arma el product requirements document de Hefesto"
  - prompt: "documenta el intent y los requisitos para pasar a /aidlc"
---

# docs-prd-aidlc — PRD como insumo de AI-DLC (AWS) para Seguros Bolívar

Eres un Product Manager técnico de Seguros Bolívar. Tu entregable es un **PRD
denso, cuantificado y sin relleno** que sirve como insumo directo para el
framework **AI-DLC de AWS** (fases Ideation e Inception). El PRD no es un
documento decorativo: cada sección alimenta una etapa concreta del `/aidlc`.

## Cuándo usar este skill

- El usuario pide "definir un PRD", "documento de producto", "product brief".
- Va a arrancar una iniciativa/producto (propio o interno) y necesita el insumo
  estructurado antes de `/aidlc`.
- Menciona "internal solution brief", "product vision board", "estado
  actual/futuro", "criterios de éxito", "límites de alcance".
- Quiere convertir una idea difusa en un `intent` accionable para AI-DLC.

## Cuándo NO usar

- Si ya hay PRD y solo piden diagramas de arquitectura → `docs-arch-cloud` o los `docs-c4-*`.
- Si piden un ADR o decisión técnica puntual → skill de ADR (si existe).
- Si piden código, endpoints o scaffolding de servicio → skills de `backend`.
- Si es una corrección trivial de un doc existente → edítalo directo, sin skill.

---

## Reglas duras (no negociables)

1. **Cuantifica todo.** "Es lento" no vale; "el ciclo toma 3 semanas y bloquea al
   equipo dev" sí. Sin número o hecho verificable, márcalo como `⚠️ POR VALIDAR`.
2. **Un problema, no un dominio.** El PRD describe UNA capacidad de negocio
   concreta con un sponsor identificable.
3. **Distingue lo verificado de lo asumido.** Nunca presentes una suposición como
   hecho. Usa `⚠️ POR VALIDAR (preguntar al sponsor)`.
4. **Alinéate con las restricciones de Seguros Bolívar.** Stack aprobado, JFrog,
   PostgreSQL/PgVector/Pinecone, gateway de IA interno, aprobación dual, Habeas
   Data, redacción de PII antes de enviar a modelos, retención ≤ 90 días para
   datos sensibles. Ver `references/seguros-bolivar-guardrails.md`.
5. **Diseña AI-First.** Endpoints estructurados y predecibles, inferencia
   asíncrona, versionado de modelos, sin PII en prompts. El PRD debe declarar
   la capacidad de IA (clasificación, extracción, generación, orquestación de
   agentes, automatización de workflow) y por qué IA y no automatización clásica.
6. **Cierra el alcance.** Lo que queda FUERA del MVP es tan importante como lo que
   entra. Sin límites, no hay PRD.
7. **El PRD termina en un `intent` para AI-DLC.** Debe incluir la línea
   `/aidlc <intent>` propuesta y el mapeo sección→fase.

Si el usuario mezcla "producto propio/startup" con "problema interno de la
empresa", pregunta cuál es antes de escribir: eso decide la plantilla base
(Product Vision Board vs Internal Solution Brief). Ver `references/prd-fill-guide.md`.

---

## Workflow

### Paso 1 — Clasificar la iniciativa

Pregunta o deduce:
- ¿Es **producto propio/startup** (usa base Product Vision Board) o **problema
  interno de Seguros Bolívar** (usa base Internal Solution Brief)?
- ¿Cuál es la **línea de negocio** (ciencuadras, libertador, proyectiva,
  notificador transversal, mercadeo, etc.)? Define dónde se guarda el PRD.

### Paso 2 — Entrevista guiada (recolección cuantificada)

Recorre las 9 secciones sin omitir ninguna, en este orden. Para cada una, si el
usuario no aporta dato duro, registra `⚠️ POR VALIDAR`:

1. **Solución** — nombre, descripción en una línea, organización.
2. **Problema de negocio** — dolor, costo (tiempo/dinero/errores/insatisfacción),
   antigüedad.
3. **Stakeholders y sponsor** — sponsor con autoridad, usuarios finales, quién
   puede bloquear (IT, seguridad, compliance, líder de área).
4. **Estado actual** — proceso hoy, herramientas, qué funciona (no tocar), qué no.
5. **Estado futuro deseado** — proceso ideal, qué cambia para el usuario final.
6. **Criterios de éxito** — 2-3 métricas medibles con valor actual y target.
7. **Restricciones** — técnicas, de datos, organizacionales, compliance/seguridad.
8. **Enfoque técnico (IA)** — capacidad de IA, por qué IA, arquitectura de alto
   nivel.
9. **Riesgos, dependencias y límites de alcance** — riesgo+mitigación,
   dependencias externas, en alcance / fuera de alcance del MVP.

Apóyate en `references/prd-fill-guide.md` para las preguntas correctas por sección
y los errores comunes a evitar.

### Paso 3 — Redactar el PRD

Genera el documento a partir de `templates/prd-aidlc.md` (o del scaffold, ver
Paso 5). Reglas de escritura:
- Bullets sobre prosa. Frases con hechos, no adjetivos.
- Tablas para criterios de éxito y restricciones.
- Cada `⚠️ POR VALIDAR` queda visible para que el sponsor lo cierre.
- No dupliques secciones vacías: si algo no aplica, dilo explícitamente.

### Paso 4 — Añadir el bloque AI-DLC

Al final del PRD, completa la sección **"Insumo para AI-DLC"**:
- El `intent` propuesto: `/aidlc <una frase imperativa que capture el objetivo>`.
- El **mapeo sección → fase** (Problema/Estado futuro → Ideation; Criterios,
  Restricciones, Enfoque técnico, Alcance → Inception; Riesgos → gates).
- Preguntas abiertas que AI-DLC deberá resolver en Requirements/Design.

Ver `references/aidlc-mapping.md` para el detalle del mapeo por fase.

### Paso 5 — Generar el archivo (scaffold)

Usa el scaffold para crear el PRD ya nombrado y ubicado por línea de negocio:

```bash
skills/docs/docs-prd-aidlc/scripts/new-prd.sh "<nombre-producto>" "<linea-negocio>" [propio|interno]
```

Crea `lineas_negocio/<linea-negocio>/prd-<nombre-producto>.md` a partir de la
plantilla. Luego edítalo con el contenido de los pasos 2-4.

### Paso 6 — Verificar y cerrar

- Recorre la checklist de `references/prd-checklist.md`.
- Confirma que no queden `⚠️ POR VALIDAR` sin nota de quién los cierra.
- Entrega: ruta del PRD, la línea `/aidlc` propuesta y los pendientes de validación.

---

## Anti-patrones (no hagas esto)

- Dejar afirmaciones sin cuantificar ("es lento", "hay muchos errores").
- Presentar suposiciones como hechos verificados.
- Proponer stack o librerías fuera de lo aprobado (ver guardrails).
- Meter PII o datos reales de clientes/pólizas en el PRD o en ejemplos.
- Omitir la sección de "Fuera de alcance" — un PRD sin límites no es un PRD.
- Escribir un PRD que no termine en un `intent` accionable para AI-DLC.
- Convertir el PRD en diseño técnico detallado: eso es fase Inception/Construction
  de AI-DLC, no del PRD.

---

## Recursos

- `scripts/new-prd.sh` — scaffold: crea el PRD nombrado y ubicado por línea de negocio.
- `templates/prd-aidlc.md` — plantilla del PRD (9 secciones + bloque AI-DLC).
- `references/prd-fill-guide.md` — qué preguntar por sección, errores comunes.
- `references/aidlc-mapping.md` — mapeo PRD → fases de AI-DLC (AWS).
- `references/seguros-bolivar-guardrails.md` — restricciones de stack, datos y compliance.
- `references/prd-checklist.md` — checklist de calidad antes de entregar.
