# Buenas prácticas — C4 Componentes (Nivel 3)

Reglas concretas para que el diagrama sirva a los desarrolladores del
contenedor.

---

## 1. Un solo contenedor por diagrama

`scopeBoundary` = nombre del contenedor (el mismo que en N2). Si necesitas
varios contenedores con sus componentes → genera **varios `.drawio`**.

✅ "Componentes — API de Pedidos".
❌ "Componentes — Sistema completo" (mezcla niveles).

## 2. Granularidad 5–15

- <5 componentes → quizás no necesitabas un N3 (un README basta).
- 15–20 → al límite; revisa si hay sub-componentes que agrupar.
- 25+ → estás dibujando clases, no componentes. Agrupa por responsabilidad.

## 3. Componentes con responsabilidad cohesiva

Cada `component` debe poder describirse en una frase clara:
- ✅ "Persiste y recupera pedidos en la BD operacional."
- ✅ "Cliente HTTP hacia Stripe para cobros y reembolsos."
- ❌ "Lógica" / "Utils" / (vacío).

## 4. Lo externo al contenedor lleva `external:true`

- Otros contenedores del mismo sistema → `container` + `external:true`.
- BDs propias → `database` + `external:true` (sí, propias del sistema pero
  externas a ESTE contenedor; van fuera del boundary).
- Colas → `queue` + `external:true`.
- Terceros → `system` + `external:true`.

## 5. Relaciones con descripción siempre

- In-process (componente → componente del mismo contenedor): `description`
  obligatoria, `technology` opcional (puede ser vacío o `in-process`).
- Hacia afuera (componente → BD / cola / sistema externo): `description` +
  `technology` (protocolo).
- `async:true` para colas, pub/sub, webhooks.

## 6. No actores humanos en N3

Los actores viven en N1 y N2. En N3 las "entradas" son otros contenedores
(la SPA, el API Gateway, etc.) → modélalos como `container` + `external:true`.

## 7. Naming consistente

- El boundary lleva el nombre del contenedor exacto que está en N2.
- Componentes con nombre técnico de su rol: `OrderController`, no
  `ApiPedidosOrderController` (el contenedor ya identifica el contexto).
- Si dos contenedores tienen un `OrderRepository`, en su N3 respectivo el
  nombre se mantiene; el diagrama por sí solo aclara a cuál pertenece.

## 8. Trazabilidad

- Nombre recomendado: `c4-componentes-<contenedor>.drawio`.
- Versiona en git.
- Acompáñalo con un ADR si introduce un patrón (hexagonal, CQRS) o decisiones
  no triviales.

---

## Checklist antes de entregar

- [ ] `scopeBoundary` con el nombre exacto del contenedor (igual al N2).
- [ ] Todos los componentes con `scope:true`.
- [ ] Cada `component` con `description` cohesiva.
- [ ] Dependencias externas (BD, colas, otros contenedores, sistemas) con
      `external:true`.
- [ ] No hay componentes de OTROS contenedores.
- [ ] Cada relación con `description`.
- [ ] Relaciones que cruzan el boundary con `technology` (protocolo).
- [ ] Relaciones asíncronas con `async:true`.
- [ ] 5–15 componentes.
- [ ] El `.drawio` abre y valida sin errores.
- [ ] Justificaste el patrón de descomposición (layered, hexagonal, CQRS,
      event-driven).

---

## Anti-patrones más comunes

1. **Mezclar componentes de varios contenedores**.
   → Uno por diagrama. Si necesitas el panorama, eso es N2.
2. **Granularidad clase-a-clase**. 50 cajas para 50 clases → reagrupa.
3. **Componentes sin responsabilidad clara** ("Utils", "Helpers", "Common").
   → Si no tienen razón propia, no merecen caja.
4. **Sistemas externos no relacionados** — si no toca estos componentes, no
   lo metas.
5. **Relaciones sin `description`** — "usa", "conecta con" no aporta.
6. **Repetir el nombre del contenedor** en cada componente.
7. **Modelar tu código fuente** (paquetes con todas sus sub-clases). Esto es
   un diagrama de **arquitectura**, no un mapa del repo.
