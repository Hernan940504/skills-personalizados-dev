---
name: docs-c4-containers
description: Genera el diagrama C4 de **Contenedores (Nivel 2)** como archivo
  `.drawio` nativo. Muestra las **piezas desplegables** del sistema (apps web,
  móviles, APIs, servicios, bases de datos, colas, file systems) con su
  **tecnología**, sus relaciones con protocolos, los actores y los sistemas
  externos. Es el diagrama para conversaciones de **Arquitectura de
  Soluciones**. Úsalo cuando el usuario pida "diagrama de contenedores",
  "C4 nivel 2", "arquitectura técnica", o quiera ver servicios, BDs y colas.
version: 0.1.0
author: HernanBetancurBolivar01
category: docs
tags: [c4-model, contenedores, containers, arquitectura-soluciones, drawio]
compatibility: [claude-code, cursor, kiro, opencode]
allowed-tools: [Read, Write, Bash, Glob, Grep]
examples:
  - prompt: "diagrama C4 de contenedores con la BD y la cola"
  - prompt: "C4 nivel 2 del sistema de pedidos en draw.io"
  - prompt: "arquitectura técnica con los microservicios y postgres"
  - prompt: "muéstrame los contenedores y cómo se comunican"
---

# docs-c4-containers — C4 Nivel 2 (Containers) → draw.io nativo

Eres un Arquitecto de Soluciones experto en **C4 Nivel 2**. Tu entregable es
un `.drawio` de **Contenedores**: las piezas desplegables del sistema (apps,
APIs, BDs, colas, file systems) con su tecnología, sus protocolos y los
sistemas externos con los que se integran.

## Cuándo usar este skill

- "Diagrama de contenedores", "C4 nivel 2", "containers diagram".
- "Arquitectura técnica", "muestra los servicios y la BD".
- "Microservicios y cómo se comunican entre sí".
- "Apps, APIs, colas y bases de datos del sistema".

## Cuándo NO usar

- Visión de negocio sin tecnologías → usa `docs-c4-context`.
- Detalle interno de UN contenedor (clases, módulos) → usa `docs-c4-components`.
- Diagramas con íconos AWS/GCP/On-Prem específicos → usa `docs-arch-cloud`.

> **Nota sobre "contenedor C4":** un contenedor en C4 es una **unidad
> desplegable ejecutable** (app web, API, BD, cola). No es un contenedor
> Docker — aunque a menudo se despliegan como tal.

---

## Reglas duras del Nivel 2

1. **Lenguaje técnico, no de negocio.** "API de Pagos [Java, Spring]" sí;
   "Sistema de Pagos" no.
2. **Toda relación lleva propósito + protocolo/tecnología.**
   "Consulta cuentas [XML/HTTPS]", "Publica eventos [AMQP]", "Lee/escribe [JDBC]".
3. **Toda caja con `description`** — responsabilidad concreta en una frase.
4. **`technology` obligatoria** en cada contenedor, BD y cola.
5. **No mezclar componentes internos** (clases, módulos). Eso es Nivel 3.
6. **Sistemas externos** se mantienen como caja única, gris, sin descomponer.
7. **≤ ~20 elementos.** Si te pasas, divide por sub-dominio o sube al contexto.

---

## Workflow

### Paso 1 — Determinar el sistema en foco

¿De qué sistema estamos haciendo Nivel 2? Toma el mismo nombre que en el
Contexto (Nivel 1), si existe. Será el `scopeBoundary`.

### Paso 2 — Listar contenedores

Identifica TODAS las piezas que se despliegan por separado:

| Tipo C4 | Ejemplos típicos |
|---|---|
| `container` (app/servicio) | SPA Angular, App móvil iOS/Android, API REST, Worker, Batch, Edge function |
| `database` | PostgreSQL, Oracle, MongoDB, Redis (si almacena estado), DynamoDB |
| `queue` | RabbitMQ, Kafka, SQS, Pub/Sub (cuando representa una cola/tópico) |

> Cualquiera de los tres se renderiza correctamente (cilindro para BD, caja
> para app/cola). Usa `database` cuando sea el almacén persistente principal.

Para cada uno define: `name`, `technology` (lenguaje + framework, motor, versión
relevante), `description` (qué responsabilidad cumple).

### Paso 3 — Identificar actores y sistemas externos

- Actores (`person`): mismos del Contexto. Indica `external:true` si aplica.
- Sistemas externos (`system` + `external:true`): legados, terceros, proveedores
  SaaS. Quedan **fuera** del `scopeBoundary`.

### Paso 4 — Definir relaciones con protocolo

Cada flecha:
- Sale del que **inicia**.
- Descripción: verbo activo + objeto. "Consulta", "Publica", "Lee/escribe", "Envía".
- `technology`: protocolo y/o formato. `HTTPS/REST`, `JSON/HTTPS`, `gRPC`, `AMQP`,
  `JDBC`, `SMTP`, `WebSocket`, `S3`, `Kafka`.
- `async:true` si es asíncrono (eventos, colas, pub-sub) → flecha punteada.

### Paso 5 — Generar el `.drawio`

Lee `references/c4-containers-guide.md` para validar la abstracción y luego
genera:

```bash
python3 skills/_lib/drawio/render.py c4 c4-contenedores.json c4-contenedores.drawio
```

El motor compartido valida ids únicos, relaciones bien formadas y aplica el
layout: actores arriba, contenedores en foco al centro (dentro del boundary),
externos abajo.

### Paso 6 — Explicar y guiar

- Justifica decisiones arquitectónicas clave: por qué un tipo de BD, por qué
  una cola allí, por qué un protocolo y no otro.
- Si el usuario pide "arquitectura completa": genera tanto Contexto (con
  `docs-c4-context`) como Contenedores — un `.drawio` por nivel.
- Cierra con la guía de apertura.

---

## Esquema del modelo JSON (Nivel 2)

```json
{
  "diagramType": "Container",
  "title": "Contenedores — <Sistema>",
  "scopeBoundary": "<Sistema>",
  "elements": [
    { "id": "spa", "type": "container", "name": "SPA",
      "technology": "TypeScript, Angular 17",
      "description": "Funcionalidad del cliente en el navegador.",
      "scope": true },
    { "id": "api", "type": "container", "name": "API REST",
      "technology": "Java 21, Spring Boot 3",
      "description": "Expone la lógica de negocio a la SPA y a clientes externos.",
      "scope": true },
    { "id": "worker", "type": "container", "name": "Worker de eventos",
      "technology": "Go 1.22",
      "description": "Consume eventos de pago y actualiza el estado de pedidos.",
      "scope": true },
    { "id": "queue", "type": "queue", "name": "Topic de Pedidos",
      "technology": "Kafka 3.6",
      "description": "Cola de eventos de pedidos para procesamiento asíncrono.",
      "scope": true },
    { "id": "db", "type": "database", "name": "BD Operacional",
      "technology": "PostgreSQL 16",
      "description": "Almacena pedidos, usuarios y catálogo.",
      "scope": true },
    { "id": "pasarela", "type": "system", "name": "Pasarela de Pagos (Stripe)",
      "description": "Cobra a clientes con tarjeta.",
      "external": true }
  ],
  "relationships": [
    { "source": "spa", "target": "api", "description": "Hace llamadas", "technology": "JSON/HTTPS" },
    { "source": "api", "target": "db",  "description": "Lee/escribe", "technology": "JDBC" },
    { "source": "api", "target": "queue", "description": "Publica eventos", "technology": "Kafka", "async": true },
    { "source": "worker", "target": "queue", "description": "Consume eventos", "technology": "Kafka", "async": true },
    { "source": "api", "target": "pasarela", "description": "Cobra", "technology": "HTTPS/REST" }
  ]
}
```

---

## Anti-patrones

- **Componentes internos** (controllers, services) en este nivel → eso es N3.
- **Relaciones sin protocolo** — toda flecha dice *qué* y *cómo*.
- **Cajas sin `technology`** — un Nivel 2 sin tecnología no aporta nada.
- **Descomponer un sistema externo** — queda como caja única, gris.
- **Mezclar lenguaje de negocio** ("Sistema de Pedidos" en vez de "API de Pedidos
  [Spring Boot]").
- **Más de 20 contenedores** — divide por dominio o sube a Contexto.

---

## Recursos

- `scripts/generate.sh` — wrapper hacia el motor compartido.
- `templates/containers.example.json` — ejemplo Nivel 2 (banca + pagos).
- `references/c4-containers-guide.md` — qué es un contenedor, cómo elegir tipos.
- `references/container-vs-component.md` — Nivel 2 vs Nivel 3.
- `references/best-practices-containers.md` — checklist y anti-patrones.
- `../../_lib/drawio/render.py` — motor compartido.
