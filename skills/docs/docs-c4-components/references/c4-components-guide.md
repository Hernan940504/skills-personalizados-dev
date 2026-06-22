# Guía — C4 Nivel 3 (Components)

El diagrama de Componentes responde: *¿Cómo está estructurado internamente
UN contenedor?* Es zoom al interior de una sola pieza desplegable del Nivel 2.

Audiencia: desarrolladores de **ese** contenedor.

---

## Qué es un "componente" C4

Una **agrupación lógica de funcionalidad** dentro de un contenedor. Tiene una
interfaz bien definida y una responsabilidad cohesiva. Pueden ser:

- Una clase principal (un `Controller`, un `Service`).
- Un paquete o módulo (`paquete fulfillment`, `módulo notifications`).
- Un patrón con varias clases (un `Repository` con interfaz + impl).
- Un puerto/adaptador (hexagonal).

Lo que NO es un componente C4:
- Una clase utilitaria minúscula (helper, DTO) — esas no llevan caja propia.
- Un contenedor entero (eso es N2).
- Un módulo que vive en otro proceso (eso es N2).

> **Granularidad sugerida: 5–15 componentes por contenedor.** Si tienes 50
> clases, no las dibujes una por una — agrúpalas por responsabilidad.

---

## Estructura recomendada del diagrama

Dentro del boundary del contenedor:
- Inbound (entry points): Controllers, Consumers, Listeners.
- Domain / Application: Services, Use Cases, Domain Aggregates.
- Outbound: Repositories, Gateways, Publishers.

Fuera del boundary (externos al contenedor):
- BDs propias → `database` con `external:true`.
- Colas / tópicos → `queue` con `external:true`.
- Otros contenedores → `container` con `external:true`.
- Sistemas de terceros → `system` con `external:true`.

---

## Tipos del modelo JSON

| `type`      | Uso en N3 | Render |
|-------------|-----------|--------|
| `component` | Pieza interna del contenedor en foco | Caja azul claro |
| `container` | OTRO contenedor del sistema (siempre `external:true`) | Caja azul medio |
| `database`  | BD usada (con `external:true`) | Cilindro azul medio |
| `queue`     | Cola/tópico (con `external:true`) | Caja azul medio |
| `system`    | Sistema de terceros (con `external:true`) | Caja gris |

Nota: los componentes propios llevan `scope:true`, todo lo demás `external:true`.

---

## `technology` en componentes

Opcional, pero útil cuando aclara la decisión:
- `Spring MVC` (Controller).
- `Spring Data JPA` (Repository).
- `WebClient` (HTTP client).
- `Spring Kafka` (Event publisher).
- `Resilience4j` (Circuit breaker / retry).

Si todos tus componentes son Java + Spring, basta con poner `technology` en
los que aportan información distintiva.

---

## Relaciones en N3

| Caso | `description` | `technology` |
|---|---|---|
| Controller → Service | "Invoca" | (vacío o `in-process`) |
| Service → Repository | "Persiste / consulta" | (vacío) |
| Repository → BD | "Lee/escribe" | `JDBC` / `MongoDB` |
| Service → Gateway | "Solicita cobro" | (vacío) |
| Gateway → API externa | "Cobra" | `HTTPS/REST` |
| Publisher → Cola | "Publica" | `Kafka` (+ `async:true`) |
| Consumer ← Cola | "Consume" | `Kafka` (+ `async:true`) |

Las llamadas in-process pueden omitir `technology` para no saturar; las
llamadas que cruzan el boundary del contenedor (a BD, colas, sistemas
externos) deben llevar protocolo.

---

## Cómo decidir la granularidad

Hazte estas preguntas:
1. ¿Tiene una **responsabilidad cohesiva**? Si no, agrúpalo o sepáralo.
2. ¿Lo testearía como una unidad? Si sí, probablemente es un componente.
3. ¿Cambia por una razón distinta a sus vecinos? Si sí, sepáralo.
4. ¿Es solo "código de adhesión" (1–2 clases pequeñas)? Si sí, fusiónalo con
   su consumidor o productor.

Reglas prácticas:
- En arquitectura layered: cada Controller, Service, Repository es UN
  componente. No metas 5 Controllers de la misma feature como 5 cajas.
- En arquitectura hexagonal: cada adaptador (REST, Kafka, DB, HTTP client)
  es UN componente. El domain a veces es UN solo componente o se desglosa
  en aggregates si son muy distintos.
- En event-driven: cada Consumer + Handler suele ser UN componente.

---

## Cuántos diagramas N3 generar

Uno por contenedor que merezca detalle. **No todos los contenedores
necesitan N3.** Generas N3 cuando:
- El contenedor tiene complejidad interna que vale la pena documentar.
- Nuevos miembros del equipo necesitan entender su estructura.
- Hay decisiones arquitectónicas no triviales (CQRS, hexagonal, etc.).

**No generes N3 para BDs ni colas** (no tienen "componentes" en sentido C4).

---

## Cuándo NO hacer N3

- El contenedor es trivial (1–3 clases) — un README basta.
- El contenedor es una BD, una cola o un object store.
- El contenedor es código de terceros que no controlas.
- El usuario quería ver tecnologías o despliegue — eso es N2 / Deployment.
