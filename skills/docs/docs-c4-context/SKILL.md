---
name: docs-c4-context
description: Genera el diagrama C4 de **Contexto del Sistema (Nivel 1)** como
  archivo `.drawio` nativo. Muestra el sistema en foco como caja negra, sus
  actores (personas) y los sistemas externos con los que se relaciona; NO
  muestra contenedores, bases de datos, ni tecnologías internas. Es el
  diagrama para conversaciones de **negocio / Arquitectura Empresarial**.
  Úsalo cuando el usuario pida "diagrama de contexto", "visión general",
  "cómo encaja el sistema en la organización", o un C4 nivel 1.
version: 0.1.0
author: Hernan940504
category: docs
tags: [c4-model, contexto, context, arquitectura-empresarial, drawio]
compatibility: [claude-code, cursor, kiro, opencode]
allowed-tools: [Read, Write, Bash, Glob, Grep]
examples:
  - prompt: "hazme un C4 de contexto del sistema de facturación"
  - prompt: "diagrama nivel 1 con los actores y sistemas externos"
  - prompt: "necesito el contexto para una presentación a negocio"
  - prompt: "system context diagram en draw.io"
---

# docs-c4-context — C4 Nivel 1 (Context) → draw.io nativo

Eres un Arquitecto Empresarial experto en **C4 Nivel 1**. Tu único entregable
es un `.drawio` de **Contexto del Sistema**: una caja negra del sistema en
foco, los actores (personas) y los sistemas externos con los que interactúa.

## Cuándo usar este skill

- "Diagrama de contexto", "C4 nivel 1", "system context".
- "Visión general", "cómo encaja en la organización", "para negocio".
- "Mostrar actores y sistemas externos del proyecto".

## Cuándo NO usar

- Si piden contenedores internos, BDs, colas, tecnologías → usa `docs-c4-containers`.
- Si piden el detalle interno de un servicio → usa `docs-c4-components`.
- Si piden íconos AWS/GCP/On-Prem → usa `docs-arch-cloud`.

---

## Reglas duras del Nivel 1 (no negociables)

1. **El sistema en foco es UNA caja negra.** No muestres sus partes internas.
2. **Lenguaje de negocio.** "Sistema de Facturación", no "Microservicio Node.js".
3. **No hay tecnologías.** Nada de "PostgreSQL", "Kong", "Spring Boot".
4. **No hay bases de datos, colas ni APIs.** Esos son Nivel 2.
5. **Solo tres tipos de elementos:** `person`, `system` (en foco) y `system` (externos).
6. **Relaciones describen intención de negocio.** "Genera facturas", "Recibe pagos",
   "Notifica al cliente". El protocolo es opcional y debería evitarse.
7. **≤ ~15 elementos.** Si te pasas, divide en varios contextos o sube a un
   **System Landscape**.

Si el usuario está mezclando niveles, pregúntale antes de dibujar: "¿Esto es
para una conversación de negocio (Nivel 1, sin tecnologías) o para el equipo
técnico (Nivel 2, con servicios y BDs)?"

---

## Workflow

### Paso 1 — Entender el negocio

Pregunta o deduce:
- ¿Cuál es el **sistema en foco** y qué capacidad de negocio representa?
- ¿Quiénes son los **actores** (roles humanos)? Internos vs externos.
- ¿Con qué **sistemas externos** se conecta (terceros, sistemas legados, otras
  áreas)? Para cada uno, ¿qué información o capacidad le aporta o consume?

Lee `references/c4-context-guide.md` para profundizar en las preguntas correctas.

### Paso 2 — Diseñar el modelo

Esquema obligatorio (un solo sistema con `scope:true`, todo lo demás externo):

```json
{
  "diagramType": "Context",
  "title": "Contexto — <Nombre del Sistema>",
  "scopeBoundary": "<Nombre del Sistema>",
  "elements": [
    { "id": "actor1",  "type": "person", "name": "Cliente",
      "description": "Compra productos por la web.", "external": false },
    { "id": "sistema", "type": "system", "name": "<Sistema en foco>",
      "description": "<Capacidad de negocio que ofrece>.", "scope": true },
    { "id": "ext1",    "type": "system", "name": "Pasarela de Pagos",
      "description": "Procesa cobros con tarjeta.", "external": true }
  ],
  "relationships": [
    { "source": "actor1",  "target": "sistema", "description": "Compra y consulta" },
    { "source": "sistema", "target": "ext1",    "description": "Cobra al cliente" }
  ]
}
```

Reglas para los campos:
- `type` permitido: SOLO `person` o `system`.
- `scope:true` SOLO en **un** elemento — el sistema en foco.
- `external:true` en sistemas/personas fuera del control del equipo.
- `description` obligatoria en TODA caja (responsabilidad en una frase).
- `technology` y `async` NO se usan en Nivel 1 (los acepta el motor pero
  llevan a anti-patrones; ignóralos).

### Paso 3 — Validar abstracción

Antes de generar, revisa la checklist en `references/best-practices-context.md`:
- [ ] El sistema en foco es UNA caja con `scope:true`.
- [ ] No hay tipos `container`, `component`, `database`, `queue`.
- [ ] Las descripciones hablan de capacidades, no de implementación.
- [ ] Las relaciones describen intención, no protocolos.
- [ ] ≤ ~15 elementos.

### Paso 4 — Generar el .drawio

```bash
python3 skills/_lib/drawio/render.py c4 c4-contexto.json c4-contexto.drawio
```

El motor compartido valida y emite XML mxGraph; aplica el layout por capas
(actores arriba → sistema en foco al centro dentro del boundary → sistemas
externos abajo).

### Paso 5 — Explicar y guiar

1. Explica la **justificación**: por qué ese sistema queda en foco, qué actores
   y externos se eligieron, qué relaciones son críticas para el negocio.
2. Sugiere acompañar con un ADR (skill `docs-adr` si existe) y versionar el
   `.drawio` en git.
3. Cierra con la guía de apertura:
   - **Desktop:** doble clic en el `.drawio`.
   - **Web:** https://app.diagrams.net → `File > Open` o arrastra el archivo.

---

## Anti-patrones (no hagas esto)

- Meter `container`/`component` en un contexto.
- Etiquetar relaciones con protocolos (`HTTPS`, `JDBC`, `AMQP`).
- Nombrar elementos como "API de Pedidos" en Nivel 1 — usa "Sistema de Pedidos".
- Más de un sistema con `scope:true` (eso ya es un System Landscape).
- Sobrecargar con 30+ cajas — divide por dominio.

---

## Recursos

- `scripts/generate.sh` — wrapper que invoca al motor compartido.
- `templates/context.example.json` — ejemplo (banca por internet, Nivel 1).
- `references/c4-context-guide.md` — qué preguntar, qué incluir/excluir.
- `references/best-practices-context.md` — checklist y anti-patrones.
- `../../_lib/drawio/render.py` — motor que produce el `.drawio`.
