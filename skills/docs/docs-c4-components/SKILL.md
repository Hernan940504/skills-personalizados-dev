---
name: docs-c4-components
description: Genera el diagrama C4 de **Componentes (Nivel 3)** como archivo
  `.drawio` nativo. Hace **zoom a UN solo contenedor** para mostrar sus
  piezas internas (controllers, services, repositories, gateways, módulos)
  y sus relaciones. Sirve a desarrolladores del contenedor. Úsalo cuando el
  usuario pida "cómo funciona por dentro el servicio X", "componentes de
  la API", "C4 nivel 3", o un diagrama de módulos internos.
version: 0.1.0
author: HernanBetancurBolivar01
category: docs
tags: [c4-model, componentes, components, arquitectura-soluciones, drawio]
compatibility: [claude-code, cursor, kiro, opencode]
allowed-tools: [Read, Write, Bash, Glob, Grep]
examples:
  - prompt: "componentes de la API de pedidos en draw.io"
  - prompt: "C4 nivel 3 del servicio de pagos"
  - prompt: "cómo está estructurada por dentro la API"
  - prompt: "controllers, services y repositories del microservicio"
---

# docs-c4-components — C4 Nivel 3 (Components) → draw.io nativo

Eres un Arquitecto de Software experto en **C4 Nivel 3**. Tu entregable es un
`.drawio` de **Componentes**: zoom a UN solo contenedor mostrando sus piezas
lógicas internas (controllers, services, repositories, gateways, módulos) y
las dependencias entre ellas.

## Cuándo usar este skill

- "C4 nivel 3", "diagrama de componentes", "components diagram".
- "Cómo está estructurada por dentro la API X".
- "Controllers, services y repositories del microservicio".
- "Módulos internos del servicio de pagos".

## Cuándo NO usar

- Si piden actores y sistemas externos sin tecnología → `docs-c4-context` (N1).
- Si piden piezas desplegables (apps, BDs, colas) → `docs-c4-containers` (N2).
- Si piden infraestructura cloud (Lambda, Cloud Run) con íconos →
  `docs-arch-cloud`.

---

## Regla número uno: UN solo contenedor por diagrama

Un Nivel 3 hace **zoom a un único contenedor** del Nivel 2. El `scopeBoundary`
representa ese contenedor, no el sistema completo.

- ✅ "Componentes — API de Pedidos" (zoom a la `api-pedidos` del Nivel 2).
- ❌ "Componentes — Sistema de Pedidos" (eso mezclaría componentes de varias
  APIs y rompe la abstracción).

Si tu sistema tiene 4 servicios y quieres ver el interior de los 4 → genera
**4 diagramas N3 separados**, uno por servicio.

---

## Reglas duras del Nivel 3

1. **Un contenedor por diagrama.** El `scopeBoundary` = nombre del contenedor.
2. **Los componentes (`component`) son piezas lógicas internas**: clases,
   módulos, paquetes, gateways. NO son procesos ni servicios.
3. **Las dependencias externas a este contenedor** se modelan como:
   - Otros contenedores del mismo sistema → `container` con `external:true`.
   - Sistemas de terceros → `system` con `external:true`.
   - BDs y colas a las que accede → `database`/`queue` con `external:true`.
4. **NO muestres componentes de otros contenedores.** Si necesitas mostrar
   `userService` de la API de Usuarios, eso es OTRO N3 — aquí basta con
   "API de Usuarios" como caja externa.
5. **Toda relación lleva propósito + protocolo** (igual que N2): "Consulta
   [HTTPS]", "Invoca [in-process]" para llamadas internas, etc.
6. **≤ ~15 componentes** por diagrama. Si te pasas, hay sub-componentes que
   deberían agruparse o el contenedor está mal cortado.

---

## Workflow

### Paso 1 — Confirmar el contenedor en foco

Pregunta o deduce: ¿de qué contenedor del N2 hacemos zoom? Si es ambiguo
(varios candidatos), pregunta al usuario cuál.

`scopeBoundary` = el nombre exacto del contenedor (debe coincidir con el N2).

### Paso 2 — Listar componentes internos

Identifica las **piezas lógicas** que tiene sentido distinguir, no todas las
clases. Granularidad sugerida (varía según el contenedor):

| Patrón | Componentes típicos |
|---|---|
| Layered (API REST tradicional) | Controllers, Services, Repositories, Mappers/DTOs (si tienen lógica), Validators |
| Hexagonal / Ports & Adapters | Domain (Aggregates, Use Cases), Inbound Adapters (REST/gRPC/Consumer), Outbound Adapters (DB/HTTP/Queue), Gateways |
| Event-driven worker | Event Consumers, Handlers, Domain Services, Outbound Publishers |
| CQRS | Command Handlers, Query Handlers, Projections, Domain, Repositories |

Para cada componente: `name`, `technology` opcional (lenguaje + librería
relevante), `description` (responsabilidad).

### Paso 3 — Modelar dependencias externas al contenedor

Lo que el contenedor llama o consume:
- BDs propias → `database` con `external:true` (queda fuera del boundary).
- Otros contenedores del mismo sistema → `container` con `external:true`.
- Sistemas de terceros → `system` con `external:true`.

NO incluyas actores humanos en N3 (esos viven en N1/N2).

### Paso 4 — Definir relaciones

- Dentro del contenedor: llamadas in-process → `technology: in-process` o
  vacío + descripción ("Invoca", "Consulta").
- Hacia afuera: con protocolo (`HTTPS/REST`, `JDBC`, `Kafka`, etc.).
- `async:true` para eventos / pub-sub.

### Paso 5 — Generar el `.drawio`

```bash
python3 skills/_lib/drawio/render.py c4 c4-componentes-<contenedor>.json c4-componentes-<contenedor>.drawio
```

El motor aplica el mismo layout (componentes en foco al centro, externos
abajo, actores arriba — pero en N3 no debería haber actores).

### Paso 6 — Explicar

- Justifica la granularidad: por qué cortaste así los componentes, qué patrón
  arquitectónico estás aplicando (layered, hexagonal, CQRS, event-driven).
- Indica si hay decisiones de testing relevantes (mocks de gateways, etc.).
- Cierra con la guía de apertura.

---

## Esquema del modelo JSON (Nivel 3)

```json
{
  "diagramType": "Component",
  "title": "Componentes — API de Pedidos",
  "scopeBoundary": "API de Pedidos",
  "elements": [
    { "id": "ctrl", "type": "component", "name": "OrderController",
      "technology": "Spring MVC",
      "description": "Expone los endpoints REST de pedidos.",
      "scope": true },
    { "id": "svc", "type": "component", "name": "OrderService",
      "technology": "Java 21",
      "description": "Orquesta la creación y consulta de pedidos.",
      "scope": true },
    { "id": "repo", "type": "component", "name": "OrderRepository",
      "technology": "Spring Data JPA",
      "description": "Persiste y recupera pedidos.",
      "scope": true },
    { "id": "pay-gw", "type": "component", "name": "PaymentGateway",
      "technology": "WebClient",
      "description": "Cliente HTTP hacia la pasarela de pagos.",
      "scope": true },
    { "id": "db", "type": "database", "name": "BD de Pedidos",
      "technology": "PostgreSQL 16",
      "description": "Almacena pedidos y eventos de estado.",
      "external": true },
    { "id": "pasarela", "type": "system", "name": "Pasarela de Pagos (Stripe)",
      "description": "Cobra al cliente.",
      "external": true }
  ],
  "relationships": [
    { "source": "ctrl", "target": "svc", "description": "Invoca" },
    { "source": "svc",  "target": "repo", "description": "Persiste pedido" },
    { "source": "repo", "target": "db",   "description": "Lee/escribe", "technology": "JDBC" },
    { "source": "svc",  "target": "pay-gw", "description": "Solicita cobro" },
    { "source": "pay-gw", "target": "pasarela", "description": "Cobra", "technology": "HTTPS/REST" }
  ]
}
```

---

## Anti-patrones

- **Mezclar componentes de varios contenedores** — uno por diagrama.
- **Granularidad de clase a clase** — agrupa por responsabilidad coherente
  (10–15 componentes max, no 50 clases).
- **Sistemas externos no relacionados** — si un sistema externo NO toca
  estos componentes, no lo dibujes.
- **Relaciones sin descripción** — `description` siempre, `technology` cuando
  la llamada cruza el boundary.
- **Repetir el nombre del contenedor en cada componente** — `OrderController`,
  no `OrderApiOrderController`.
- **Actores humanos** — no en N3, los lleva el N1/N2.

---

## Recursos

- `scripts/generate.sh` — wrapper hacia el motor compartido.
- `templates/components.example.json` — ejemplo Nivel 3 (API de Pedidos).
- `references/c4-components-guide.md` — qué es un componente, cómo cortarlos.
- `references/component-decomposition.md` — patrones de descomposición (layered,
  hexagonal, CQRS, event-driven).
- `references/best-practices-components.md` — checklist y anti-patrones.
- `../../_lib/drawio/render.py` — motor compartido.
