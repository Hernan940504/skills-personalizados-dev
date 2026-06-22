# Buenas prácticas — C4 Contenedores (Nivel 2)

Reglas concretas para que el diagrama sirva al equipo técnico.

---

## 1. Tecnología explícita en cada contenedor

Cada `container`, `database` y `queue` debe tener `technology` con:
- Lenguaje + framework (servicios): `Java 21, Spring Boot 3`.
- Motor + versión (BDs/colas): `PostgreSQL 16`, `Kafka 3.6`, `Redis 7`.
- Plataforma específica si afecta diseño: `AWS Lambda`, `Cloud Run`.

Un Nivel 2 **sin tecnologías** es un Contexto disfrazado — y entonces usa
`docs-c4-context`.

## 2. Toda relación con propósito + protocolo

Formato: `description` = verbo activo, `technology` = protocolo/formato.

| ✅ | ❌ |
|---|---|
| "Consulta cuentas [XML/HTTPS]" | "Usa" |
| "Publica eventos [Kafka]" | "Conecta con" |
| "Lee/escribe [JDBC]" | (sin etiqueta) |
| "Envía emails [SMTP]" | "Manda emails" |

Las relaciones asíncronas se marcan con `async:true` → flecha punteada.

## 3. Solo piezas desplegables

Si la "pieza" no tiene su propio proceso/runtime/artefacto → es un componente
y va en N3 (`docs-c4-components`), no aquí.

Ver `container-vs-component.md` para el criterio.

## 4. Sistemas externos NO se descomponen

Un sistema externo es siempre **una caja única gris**. No le mires por
dentro — eso no está en tu alcance.

✅ "Pasarela de Pagos (Stripe)" — 1 caja.
❌ "Stripe API" + "Stripe Webhook" + "Stripe Dashboard".

## 5. Boundary y alcance

- `scopeBoundary` con el mismo nombre del sistema del Contexto (N1).
- `scope:true` en todos los contenedores propios.
- Actores y sistemas externos quedan fuera del boundary.

## 6. Tamaño y carga cognitiva

- Objetivo: **5–15 contenedores** + actores + externos. Máximo total: ~20.
- Si te pasas: divide por sub-dominio (cuenta, pagos, fulfillment). Cada
  sub-dominio en su propio Nivel 2.

## 7. Layout y legibilidad

- El motor coloca: actores arriba → contenedores en foco (boundary) → externos
  abajo. Las flechas fluyen verticalmente.
- En draw.io puedes reordenar con `Arrange > Layout > Vertical Tree` o
  arrastrando manualmente para minimizar cruces.

## 8. Naming consistente con N1 y N3

- Contexto (N1): "Sistema de Pedidos" → Contenedores (N2): `scopeBoundary =
  "Sistema de Pedidos"`.
- Cada contenedor de N2 será el **alcance** de un posible N3.
  - "API de Pedidos" en N2 → boundary "API de Pedidos" en N3.

## 9. Trazabilidad

- Versiona el `.drawio` en git.
- Nombre recomendado: `c4-contenedores-<sistema>.drawio`.
- Acompáñalo con un ADR si las decisiones (BD, cola, framework) son
  significativas.

---

## Checklist antes de entregar

- [ ] `scopeBoundary` con el nombre del sistema.
- [ ] Todos los contenedores propios con `scope:true`.
- [ ] Cada `container`/`database`/`queue` con `technology` específica.
- [ ] Cada elemento con `description` de su responsabilidad.
- [ ] Cada relación con propósito + protocolo/tecnología.
- [ ] Relaciones asíncronas marcadas con `async:true`.
- [ ] Sistemas externos como caja única, sin descomponer.
- [ ] ≤ ~20 elementos totales.
- [ ] El `.drawio` abre y valida sin errores.
- [ ] Diste la guía de apertura y justificaste decisiones clave.

---

## Anti-patrones más comunes

1. **Mezclar componentes** (controllers, services, repositories) en N2.
   → Llévalo a N3 con `docs-c4-components` (zoom a UN contenedor).
2. **Descomponer un sistema externo** ("Stripe API", "Stripe Webhook").
   → Una sola caja gris.
3. **Relaciones sin protocolo** — "Usa", "Se comunica con".
4. **Cajas sin `technology`** — el lector no sabe qué decisión técnica importa.
5. **Microservicios fantasma** — cajas separadas para módulos del mismo
   proceso. Si comparten runtime, son UN contenedor.
6. **Más de 20 cajas** — pierde su valor. Divide por sub-dominio.
7. **Lenguaje de negocio** — "Sistema de Pagos" en vez de "API de Pagos
   [Spring Boot 3]".
