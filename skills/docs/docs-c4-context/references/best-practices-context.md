# Buenas prácticas — C4 Contexto (Nivel 1)

Reglas concretas para que el diagrama sea correcto, legible y útil para una
audiencia de negocio.

---

## 1. Una sola caja para el sistema en foco

El sistema en foco se modela como **caja negra**. Si te dan ganas de mostrar
sus piezas internas, eso ya es Nivel 2 (Contenedores) — genera otro `.drawio`.

✅ "Sistema de Facturación" (1 caja con `scope:true`).
❌ "API de Facturación" + "BD de Facturación" + "Worker" en el mismo contexto.

## 2. Lenguaje de negocio en todo

Nombres y descripciones hablan de **capacidades**, no de tecnología.

| Reemplaza | Por |
|---|---|
| "Microservicio Node.js" | "Sistema de Pedidos" |
| "PostgreSQL 15" | (no aparece — eso es Nivel 2) |
| "Endpoint REST de Pagos" | "Pasarela de Pagos" |
| "Cluster Kubernetes" | (no aparece) |

## 3. Toda caja con `description`

Una frase que diga qué hace ese elemento desde el punto de vista del negocio.

✅ "Permite a clientes B2B emitir facturas electrónicas conformes con SAT."
❌ "Sistema" / "ERP" / (vacío).

## 4. Relaciones describen intención, no protocolo

| ✅ Negocio | ❌ Técnico |
|---|---|
| "Cobra al cliente" | "POST /charges" |
| "Notifica al cliente" | "SMTP" |
| "Consulta tipos de cambio" | "REST API" |
| "Registra movimiento" | "JDBC" |

Excepción: si el usuario explícitamente quiere ver protocolos, súbele al Nivel 2
con `docs-c4-containers` — no contamines el contexto.

## 5. Externo vs interno

- `external:true` en personas o sistemas fuera del **control del equipo**.
- Un cliente del banco es un actor externo (`person` + `external:true`).
- Un empleado del banco es interno (`person` sin `external`).
- Un proveedor SaaS (SendGrid, Stripe, Okta) es `system` + `external:true`.
- Un sistema interno legado (Mainframe, ERP corporativo) es `system` +
  `external:true` **si no es desarrollado por el equipo que dibuja**.

## 6. Tamaño y carga cognitiva

- Objetivo: **5–10 elementos**, máximo 15.
- Si te pasas, divide por dominio de negocio o sube a **System Landscape**.
- Un contexto con 25 cajas no se lee — pierde su propósito.

## 7. Nombres consistentes con otros niveles

Si más tarde se hace el Nivel 2 (Contenedores), el sistema en foco debe
llamarse **igual** que aquí. La consistencia permite trazabilidad.

✅ Contexto: "Sistema de Pedidos" → Contenedores: "Sistema de Pedidos" como
   `scopeBoundary` y dentro: "API de Pedidos", "BD de Pedidos", etc.

## 8. Trazabilidad

- Versiona el `.drawio` en git (es XML, hace buen diff).
- Acompáñalo con un ADR (skill `docs-adr` si existe).
- Nombre de archivo recomendado: `c4-contexto-<sistema>.drawio`.

---

## Checklist antes de entregar

- [ ] Exactamente **UN** elemento con `scope:true`.
- [ ] Solo tipos `person` o `system` (no `container`/`component`/`database`/`queue`).
- [ ] Toda caja con `description` en lenguaje de negocio.
- [ ] Toda relación con descripción de intención (no protocolo).
- [ ] ≤ ~15 elementos.
- [ ] `scopeBoundary` con el nombre del sistema en foco.
- [ ] El `.drawio` abre y valida sin errores.
- [ ] Acompañas con justificación de alcance.
- [ ] Diste la guía de apertura en draw.io.

---

## Anti-patrones más comunes

1. **Mezclar niveles** — meter "Base de datos" o "Cola" en un contexto.
   → Genera el Nivel 2 aparte si esa información es relevante.
2. **Múltiples sistemas en foco** — si tienes 3 con `scope:true`, lo que quieres
   es un **System Landscape**, no un contexto.
3. **Relaciones genéricas** — "Usa", "Se conecta con" no aportan nada.
4. **Iconitos de tecnología** — el Nivel 1 NO lleva logos de AWS, Postgres, etc.
   Para eso usa `docs-arch-cloud` en su propio diagrama.
5. **Repetir el nombre del sistema en cada caja** — "API de Pagos del Sistema de
   Pagos" → solo "Pasarela de Pagos".
