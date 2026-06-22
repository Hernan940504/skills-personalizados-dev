# ¿Es esto un Contenedor (N2) o un Componente (N3)?

La pregunta más frecuente al modelar C4. La respuesta cambia el diagrama y la
audiencia. Esta guía evita el error más común: meter componentes (clases,
módulos) en un diagrama de Contenedores.

---

## Regla de oro

> **Si dos piezas se despliegan por separado, son contenedores. Si viven en el
> mismo proceso/runtime y se comunican in-memory, son componentes.**

| Pregunta | Sí → Contenedor (N2) | No → Componente (N3) |
|---|---|---|
| ¿Tiene su propio proceso/runtime? | ✅ | ❌ |
| ¿Se despliega como artefacto independiente? | ✅ | ❌ |
| ¿Tiene su propia configuración/secrets? | ✅ | ❌ |
| ¿La comunicación es por red (HTTP, gRPC, cola)? | ✅ | ❌ |
| ¿Está en la misma codebase y JVM/proceso que otros? | ❌ | ✅ |

---

## Ejemplos

| Pieza | Nivel | Por qué |
|---|---|---|
| `OrderController` | **N3 (componente)** | Clase dentro del proceso de la API. |
| `OrderService` | **N3** | Módulo lógico dentro del mismo runtime. |
| `OrderRepository` | **N3** | Acceso a la BD desde dentro del mismo servicio. |
| `payments-api` (FastAPI) | **N2 (contenedor)** | Servicio separado, su propio proceso, expone REST. |
| `payments-worker` (Celery) | **N2** | Proceso aparte, consume cola, runtime independiente. |
| Redis cache | **N2** | Servicio externo al proceso, comunicación por red. |
| Librería compartida (jar / npm) | **NINGUNO** | Es código, no infraestructura ni runtime. |
| Lambda function (1 sola, principal del sistema) | **N2** | Es la unidad desplegable principal. |
| Lambdas anidadas (varias pequeñas dentro de un servicio) | Generalmente **N2** cada una, o agrúpalas como un `container` "Functions" si son piezas pequeñas de un mismo flujo. |

---

## Caso ambiguo: monolito modular

Tienes UNA app monolítica con módulos internos: `pedidos`, `pagos`, `usuarios`.

- En **N2**: aparece como UN solo contenedor (`API Monolítica`), con
  `technology: Java 21, Spring Boot 3`, `description: "App monolítica con
  módulos: pedidos, pagos, usuarios"`.
- En **N3**: cada módulo es un `component` dentro de la API Monolítica
  (zoom a UN solo contenedor).

No metas `Pedidos`, `Pagos`, `Usuarios` como contenedores separados si en
realidad viven en el mismo proceso y se llaman in-memory.

---

## Caso ambiguo: microservicios + BFF

Tienes 5 microservicios (`orders`, `inventory`, `payments`, `notifications`,
`users`) + un BFF (`web-bff`) + un API Gateway (Kong/AWS API Gateway).

- En **N2**: cada uno es un contenedor (`orders-api`, `inventory-api`,
  `payments-api`, `notifications-svc`, `users-api`), más `web-bff` y
  `api-gateway`. Total ~7 contenedores + sus BDs + colas.
- Si tienes BD compartida (mal patrón, pero existe) → 1 `database`. Si cada
  servicio tiene su BD → 5 `database`.

---

## Caso ambiguo: serverless con muchas funciones

App con 30 Lambdas. No metas 30 cajas — eso satura el diagrama.

Estrategia:
- Agrupa las Lambdas por **dominio funcional**: `orders-fns`, `inventory-fns`,
  `notifications-fns`. Cada grupo se modela como UN contenedor con
  `technology: "AWS Lambda + Python"` y `description: "Functions de pedidos
  (12 funciones)"`.
- Si una función es el corazón del sistema (ej. el procesador de pagos),
  modélala como contenedor propio.
- Para mostrar las 30 individualmente → usa **N3** (componentes dentro del
  contenedor `orders-fns`).

---

## Caso ambiguo: base de datos compartida vs dedicada

- BD por servicio → cada servicio tiene su `database` con `scope:true`.
- BD compartida → UNA caja `database` a la que apuntan varios contenedores.
- Es lícito en N2 mostrar **lectores** (read replicas) como cajas separadas
  si tienen un rol distinto, pero no inventes piezas por amor a la simetría.

---

## Si la duda persiste

Por defecto, prefiere **Nivel 2** y consérvalo simple. Si el usuario pregunta
por la mecánica interna de un solo contenedor, eso ya es Nivel 3 — genera ese
diagrama aparte con `docs-c4-components`.
