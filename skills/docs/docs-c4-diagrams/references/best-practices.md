# Buenas prácticas para diagramas C4

Reglas concretas para que el diagrama sea correcto, legible y útil. Aplícalas al diseñar el
modelo JSON antes de generar el `.drawio`.

---

## 1. Abstracción estricta (la regla número uno)

- **Un diagrama = un nivel de zoom.** No mezcles niveles.
  - Contexto: NO muestres bases de datos, colas ni contenedores internos.
  - Contenedores: NO muestres componentes/clases internas de cada contenedor.
  - Componentes: zoom a **un solo** contenedor; NO muestres sistemas externos que no toquen esos componentes.
- Si sientes que "falta detalle", no lo metas aquí: hazlo en el siguiente nivel (otro `.drawio`).

## 2. Carga cognitiva

- Objetivo: **≤ ~20 elementos** por diagrama. Idealmente 5–15.
- Si te pasas: divide por dominio, por contenedor, o sube un nivel de abstracción.
- Un diagrama que necesita scroll en dos ejes ya es demasiado denso.

## 3. Toda caja tiene descripción

- Cada elemento lleva su **responsabilidad en una frase** (campo `description`).
  - ✅ "Almacena perfiles de usuario y hashes de credenciales."
  - ❌ (sin descripción), o ❌ "Base de datos" (redundante con el tipo).
- El estereotipo `[Person]`, `[Container: Java]`, etc. lo añade el generador — no lo repitas en el nombre.

## 4. Toda relación está etiquetada

- Formato: **propósito + protocolo/tecnología**.
  - ✅ "Consulta cuentas [XML/HTTPS]", "Publica eventos de pago [AMQP]", "Lee/escribe [JDBC]"
  - ❌ flechas sin texto, ❌ "usa", ❌ "conecta con"
- Dirección: la flecha apunta del que **inicia** la interacción al que la recibe.
- Relaciones asíncronas (eventos, colas, pub/sub): marca `async:true` → flecha punteada.
- En diagramas Dynamic, **numera** el flujo: `"1. Envía credenciales"`, `"2. Valida token"`.

## 5. Naming consistente

- Usa el **mismo nombre** para un elemento en todos los niveles donde aparezca.
- Nivel de negocio (Contexto): nombres de capacidad ("Sistema de Pagos").
- Nivel técnico (Contenedores/Componentes): nombre + tecnología ("API de Pagos [Go]").
- Sé consistente con mayúsculas/idioma en todo el diagrama.

## 6. Alcance y límites (boundary)

- Define `scopeBoundary` con el nombre del sistema (Nivel 1–2) o del contenedor (Nivel 3).
- Marca `scope:true` solo en los elementos **propios** (dentro de tu control/equipo).
- Los sistemas de terceros van con `external:true` y sin `scope` → quedan fuera del recuadro y en gris.

## 7. Leyenda / notación

- C4 recomienda incluir una **leyenda** cuando el diagrama se comparte fuera del equipo.
- El esquema de color del generador ya es autoexplicativo (azul oscuro=persona, azul=sistema/contenedor, gris=externo). Si el usuario lo pide, añade una nota de leyenda manualmente en draw.io.

## 8. Layout y legibilidad

- El generador coloca: **actores arriba**, sistema/contenedores en foco al centro (dentro del boundary), **sistemas externos abajo**. Las flechas fluyen verticalmente de arriba a abajo.
- Tras abrir en draw.io puedes reorganizar: selecciona todo y usa `Arrange > Layout` (ej. *Vertical Tree* o *Horizontal Flow*) o mueve cajas a mano para reducir cruces de líneas.
- Minimiza cruces de flechas y mantén las relaciones más importantes lo más cortas y directas posible.

## 9. Trazabilidad

- Acompaña los diagramas con un **ADR** que explique las decisiones (usa el skill `docs-adr`).
- **Versiona el `.drawio` en git** — es texto XML, hace buen diff. Evita exportar solo PNG como fuente de verdad.
- Nombra los archivos por nivel: `c4-contexto.drawio`, `c4-contenedores.drawio`, `c4-componentes-<contenedor>.drawio`.

---

## Checklist antes de entregar

- [ ] El diagrama es de un solo nivel de abstracción.
- [ ] ≤ ~20 elementos.
- [ ] Toda caja tiene `description`.
- [ ] Toda relación tiene propósito + (en enfoque técnico) protocolo.
- [ ] Elementos propios con `scope:true`; terceros con `external:true`.
- [ ] Nombres consistentes con otros niveles del mismo sistema.
- [ ] El `.drawio` abre y valida sin errores.
- [ ] Incluiste la justificación arquitectónica y la guía de apertura en draw.io.
