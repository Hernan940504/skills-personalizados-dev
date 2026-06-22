# Guía — C4 Nivel 2 (Containers)

El diagrama de Contenedores responde: *¿Cuáles son las piezas desplegables
del sistema, qué tecnología usa cada una y cómo se comunican?*

Audiencia: arquitectos, desarrolladores, operaciones, SRE.

---

## Qué es un "contenedor" C4

Una **unidad desplegable y ejecutable** que tiene su propio proceso, su
propio runtime y su propia configuración. Un contenedor C4 ≠ contenedor
Docker, aunque a menudo se despliegan como tal.

Ejemplos:
- Una app web (Single Page Application) que corre en el navegador.
- Una app móvil iOS/Android.
- Un servicio backend (API REST, gRPC).
- Un worker / job batch.
- Una base de datos (PostgreSQL, MongoDB, DynamoDB).
- Una cola de mensajes (Kafka, RabbitMQ, SQS).
- Un file system / object store (S3, GCS).
- Una función serverless (cuando es la unidad principal del sistema).

NO son contenedores C4:
- Una clase, un módulo, un controller, un service interno. (Eso es N3.)
- Un script utilitario que se ejecuta en otro proceso.
- Una librería compartida.

---

## Tipos del modelo JSON

| `type`      | Qué representa                                | Cómo se renderiza |
|-------------|-----------------------------------------------|-------------------|
| `container` | App / servicio / worker / función             | Rectángulo azul medio |
| `database`  | Almacén persistente                           | Cilindro azul medio |
| `queue`     | Cola, tópico, pub/sub                         | Rectángulo azul medio |
| `person`    | Actor humano                                  | Rectángulo redondeado azul |
| `system`    | Sistema externo (terceros o legados)          | Rectángulo gris (con `external:true`) |

Todos los contenedores del sistema en foco van con `scope:true` (dentro del
boundary). Los sistemas externos van sin `scope` y con `external:true`.

---

## `technology` — qué poner

Sé concreto y útil para una conversación técnica:

| Contenedor | `technology` ✅ | `technology` ❌ |
|---|---|---|
| API backend | `Java 21, Spring Boot 3` | `Java`, `backend` |
| SPA | `TypeScript, Angular 17` | `JS` |
| App móvil | `Kotlin / Swift (iOS/Android)` | `Móvil` |
| Worker | `Go 1.22` | `Worker` |
| Base de datos | `PostgreSQL 16` | `SQL` |
| Cola | `Kafka 3.6` | `Cola` |
| Cache | `Redis 7` | `Cache` |

Incluye la versión si es relevante para una decisión (ej. PostgreSQL 16 para
índices BRIN, Java 21 para virtual threads).

---

## Relaciones — propósito + protocolo

Toda flecha lleva los dos:

| Caso | `description` | `technology` |
|---|---|---|
| Frontend ↔ API | "Hace llamadas" | `JSON/HTTPS` |
| API ↔ BD | "Lee/escribe" | `JDBC` / `MongoDB Wire Protocol` |
| API → Cola | "Publica eventos" | `Kafka` (+ `async:true`) |
| Worker ← Cola | "Consume eventos" | `Kafka` (+ `async:true`) |
| API → Email | "Envía notificaciones" | `SMTP` (+ `async:true`) |
| API ↔ Pasarela pagos | "Cobra" | `HTTPS/REST` |
| Microservicio ↔ MS | "Solicita datos" | `gRPC` |
| App ↔ S3 | "Lee/escribe blobs" | `HTTPS/AWS SDK` |

`async:true` cambia la flecha a punteada — usa en colas, pub/sub, webhooks,
eventos y notificaciones (todo lo que NO bloquea al emisor).

---

## Cómo elegir cuándo dividir contenedores

- **Despliegue separado** → contenedor separado. (Una SPA y su API son DOS.)
- **Runtime separado** (proceso, máquina, función serverless) → separados.
- **Tecnología radicalmente distinta** y comunicación por red → separados.
- Misma codebase, mismo proceso, comunicación in-memory → es **un solo
  contenedor**; sus piezas internas serían componentes (N3).

---

## Boundary y alcance

- `scopeBoundary` = nombre del sistema (mismo que en el Contexto).
- `scope:true` en TODOS los contenedores propios.
- `external:true` en sistemas que NO controlas (terceros, otras áreas).
- Actores humanos quedan **fuera** del boundary (arriba en el layout).

---

## Cantidad esperada

| Tipo de sistema | Contenedores típicos | Total con actores y externos |
|---|---|---|
| Monolito web | App + BD (2) | 3–6 |
| API + SPA + BD | 3 | 5–8 |
| Microservicios pequeños (3–5 svc) | + BD + cola | 7–12 |
| Plataforma SaaS B2B | 8–15 | 15–20 |

Si superas 20 elementos: divide el diagrama por **sub-dominio** (cuenta
distinto: pagos, catálogo, fulfillment) y genera un Nivel 2 por sub-dominio.

---

## Diagramas de variantes (mismos contenedores, ángulos distintos)

Si el usuario lo pide:

- **Dynamic** — mismo modelo pero numerando relaciones en un caso de uso
  concreto (login, checkout, etc.). Incluye el número en `description`:
  `"1. Envía credenciales"`, `"2. Valida token"`.
- **Deployment** — mapeo a infraestructura. Modela nodos como `system` o
  `container` y agrupa con `scopeBoundary` (o varios diagramas).
