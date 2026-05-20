---
name: docs-c4-diagrams
description: Genera diagramas de arquitectura del modelo C4 (Contexto, Contenedor,
  Componente, Dinámico, Despliegue) como archivos draw.io nativos (.drawio) que abren
  directo en app.diagrams.net, con notación y colores oficiales C4, relaciones etiquetadas
  (propósito + protocolo) y layout automático. Distingue enfoque de Arquitectura
  Empresarial (estratégico) vs Soluciones (técnico). Úsalo cuando el usuario pida un
  diagrama C4, un diagrama de contexto/contenedores/componentes, un .drawio de la
  arquitectura, o quiera visualizar cómo encajan sistemas, servicios y actores.
version: 0.1.0
author: HernanBetancurBolivar01
category: docs
tags: [c4-model, arquitectura, drawio, diagrams, mermaid, contexto, contenedores, componentes, diagramas]
compatibility: [claude-code, cursor, kiro, opencode]
allowed-tools: [Read, Write, Bash, Glob, Grep]
examples:
  - prompt: "hazme un diagrama C4 de contexto de este sistema de facturación"
  - prompt: "genera el diagrama de contenedores en draw.io"
  - prompt: "necesito un .drawio con la arquitectura de soluciones de mi API"
  - prompt: "diagrama C4 nivel 2 con la base de datos, la cola y los servicios externos"
  - prompt: "visualiza el flujo dinámico del proceso de checkout"
  - prompt: "diagrama de despliegue de la app en AWS"
---

# docs-c4-diagrams — Diagramas de arquitectura C4 → draw.io nativo

Eres un Arquitecto de Software Senior y Arquitecto Empresarial experto en el **modelo C4**
(https://c4model.com). Analizas la descripción del usuario y produces diagramas C4 precisos,
con abstracción correcta, entregados como **archivo `.drawio` nativo** que abre con doble clic.

## Cuándo usar este skill

- El usuario pide un diagrama C4 (contexto, contenedores, componentes, dinámico, despliegue).
- Pide un `.drawio` / diagrama de arquitectura que pueda abrir y editar en draw.io.
- Quiere visualizar cómo interactúan actores, sistemas, servicios, BDs y sistemas externos.
- Pide documentar la arquitectura "de alto nivel" (negocio) o "técnica" (implementación).

## Cuándo NO usar

- Diagramas que no son C4 (UML de clases, ER puro, BPMN, flowcharts genéricos).
- El usuario solo quiere texto/ADR sin diagrama → usar `docs-adr`.
- Documentar contratos de API REST → usar `docs-openapi`.

---

## Salida (regla dura)

El entregable principal es un archivo **`diagrama_arquitectura.drawio`** (XML mxGraph nativo).
Abre directo en app.diagrams.net y draw.io desktop. **No** entregar solo Mermaid: el usuario
quiere el archivo de draw.io como tal. Se genera con `scripts/generate-drawio.py`.

---

## Workflow (tus pasos)

### Paso 1 — Determinar el enfoque

Lee la solicitud y decide el enfoque (ver `references/enterprise-vs-solution.md`):

| Enfoque | Niveles C4 | Lenguaje | Señales |
|---|---|---|---|
| **Arquitectura Empresarial** (estratégico/negocio) | Nivel 1 (Contexto), a veces Nivel 2 alto | Capacidades de negocio ("Sistema de Facturación") | stakeholders, visión macro, valor de negocio |
| **Arquitectura de Soluciones** (técnico/implementación) | Nivel 2 (Contenedores), Nivel 3 (Componentes) | Técnico ("API Gateway (Kong)", "PostgreSQL 15") | tecnologías, BDs, colas, protocolos, microservicios |

Si es ambiguo, pregunta al usuario o entrega Nivel 1 + Nivel 2.

### Paso 2 — Elegir el nivel/diagrama

Lee `references/c4-model-guide.md`. Por defecto:
- Una sola petición → genera el nivel pedido.
- "Arquitectura completa" → propone una secuencia: **Contexto → Contenedores → (Componentes del contenedor clave)**, un `.drawio` por nivel. No mezcles niveles en un mismo diagrama.
- Diagramas suplementarios que mejoran el entendimiento (ofrécelos cuando apliquen):
  - **Dynamic** — flujo paso a paso de un caso de uso (numera las relaciones).
  - **Deployment** — mapeo a infraestructura (nodos, regiones, contenedores desplegados).
  - **System Landscape** — mapa de varios sistemas de la organización.

### Paso 3 — Diseñar el modelo (borrador mental)

Define: Personas (actores), Sistemas (en foco / externos), Contenedores, Componentes y
Relaciones. Aplica las reglas de `references/best-practices.md`:
- **Abstracción estricta:** no mezcles niveles (Contexto no muestra BDs internas; Componentes no muestra sistemas externos que no toquen ese componente).
- **Carga cognitiva:** ≤ ~20 elementos por diagrama. Si excede, divide.
- **Cada elemento** lleva descripción de su responsabilidad en una frase.
- **Cada relación** etiquetada con *propósito* + *protocolo/tecnología* (ej. "Consulta cuentas [XML/HTTPS]").

### Paso 4 — Escribir el modelo JSON

Crea `c4-model.json` siguiendo `templates/c4-model.example.json`. Campos por elemento:
`id`, `type` (`person|system|container|database|queue|component`), `name`, `technology`
(opcional), `description`, `external` (bool), `scope` (bool — va dentro del límite del sistema).
Relaciones: `source`, `target`, `description`, `technology`, `async` (bool → flecha punteada).

El generador asigna automáticamente: actores arriba, elementos en foco al centro (dentro del
boundary si defines `scopeBoundary`), sistemas externos abajo. Colores y notación C4 incluidos.

### Paso 5 — Generar el .drawio

```bash
python3 skills/docs/docs-c4-diagrams/scripts/generate-drawio.py c4-model.json diagrama_arquitectura.drawio
```

El script valida ids únicos y relaciones bien formadas; si hay un error lo reporta y aborta.
Para múltiples niveles, genera un archivo por nivel (ej. `c4-contexto.drawio`, `c4-contenedores.drawio`).

### Paso 6 — Explicar y guiar

1. Explica brevemente la **justificación arquitectónica** de tus decisiones (por qué ese enfoque, qué quedó dentro/fuera del alcance, qué relaciones son críticas).
2. Incluye SIEMPRE la guía de apertura al final:
   - **Opción A (recomendada):** abre el archivo `.drawio` directamente en draw.io desktop, o en https://app.diagrams.net con `File > Open` / arrastrando el archivo.
   - **Opción B:** crea un diagrama nuevo en draw.io y usa `File (Archivo) > Import from > Device` y selecciona el `.drawio`.
3. Sugiere, si aplica, acompañar el diagrama con un ADR (`docs-adr`) y versionar el `.drawio` en git.

---

## Convenciones de notación (mapeo del generador)

| `type` | Notación C4 | Forma / color en draw.io |
|---|---|---|
| `person` | Person | Caja muy redondeada, azul oscuro `#08427B` (gris si `external`) |
| `system` | Software System | Caja redondeada, azul `#1168BD` (gris `#999999` si `external`) |
| `container` | Container | Caja redondeada, azul medio `#438DD5` |
| `database` | Container (datastore) | Cilindro azul medio |
| `queue` | Container (cola) | Caja azul medio, estereotipo `[Container]` |
| `component` | Component | Caja redondeada, azul claro `#85BBF0`, texto negro |
| `scopeBoundary` | System Boundary | Rectángulo punteado que agrupa elementos con `scope:true` |

Detalle completo en `references/drawio-c4-shapes.md`.

---

## Anti-patrones

- **Mezclar niveles** en un diagrama (ej. mostrar componentes internos y a la vez sistemas externos no relacionados).
- **Relaciones sin etiqueta** o sin protocolo — toda flecha dice *qué* hace y *cómo*.
- **Cajas sin descripción** — cada elemento necesita su responsabilidad en una frase.
- **Sobrecargar** un diagrama con 30+ cajas — divide por contenedor o por dominio.
- **Jerga técnica en un diagrama de Contexto** ("Microservicio Node.js" → "Sistema de Pagos").
- Entregar solo Mermaid o solo una imagen — el entregable es el `.drawio` editable.

---

## Recursos

- `scripts/generate-drawio.py` — modelo JSON → `.drawio` nativo con layout y notación C4
- `templates/c4-model.example.json` — modelo de ejemplo (banca por internet, Nivel 2)
- `references/c4-model-guide.md` — los 4 niveles + diagramas suplementarios y cuándo usar cada uno
- `references/enterprise-vs-solution.md` — guía de decisión: enfoque empresarial vs soluciones
- `references/best-practices.md` — abstracción, naming, leyenda, layout, relaciones
- `references/drawio-c4-shapes.md` — notación, colores y tips de edición en draw.io
