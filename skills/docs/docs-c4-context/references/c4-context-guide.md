# Guía — C4 Nivel 1 (Context)

El diagrama de Contexto responde **una sola pregunta**: *¿Qué construimos y
con qué/quién interactúa?* Es un mapa "desde el espacio": el sistema en foco
aparece como una caja negra, rodeado de personas (actores) y sistemas externos.

---

## Qué muestra y qué NO muestra

| Sí | No |
|---|---|
| El sistema en foco (1 caja) | Su arquitectura interna (eso es Nivel 2) |
| Personas / roles que lo usan | Funciones técnicas (API, BD) |
| Sistemas externos con los que se integra | Tecnologías ("Spring", "PostgreSQL") |
| Intención de negocio en las relaciones | Protocolos ("HTTPS", "JDBC") |

Audiencia objetivo: **stakeholders no técnicos** — product owners, dirección,
arquitectos empresariales, clientes internos.

---

## Preguntas que debes responder antes de dibujar

1. **¿Cuál es el sistema en foco?** Una capacidad de negocio, no un servicio
   técnico. Ej. "Sistema de Facturación", no "Servicio de Cálculo de IVA".
2. **¿Qué problema de negocio resuelve?** Una frase de descripción.
3. **¿Quiénes lo usan directamente?**
   - Roles humanos (clientes, empleados, terceros). Cada rol es un `person`.
   - ¿Es interno o externo a la organización?
4. **¿Con qué otros sistemas se integra?**
   - Sistemas de terceros (pasarelas de pago, proveedores de email, ERPs).
   - Sistemas legados/internos (mainframes, ERPs, CRMs).
   - Para cada uno: ¿qué información intercambia? ¿quién inicia la interacción?
5. **¿Qué intercambios son críticos para el negocio?** Esos son las relaciones
   con etiqueta clara.

---

## Cómo escribir cada elemento

### `person`
```json
{ "id": "cliente", "type": "person", "name": "Cliente Premium",
  "description": "Cliente con saldo > 100k que opera transferencias internacionales." }
```
- `external:true` si es un actor fuera de la organización (cliente, proveedor).
- `external:false` (o ausente) si es interno (empleado, operador).
- Color azul oscuro (interno) o gris (externo) lo aplica el motor.

### `system` en foco (único, con `scope:true`)
```json
{ "id": "facturacion", "type": "system", "name": "Sistema de Facturación",
  "description": "Genera facturas electrónicas y reportes para clientes B2B.",
  "scope": true }
```
- Solo UN elemento debería tener `scope:true`.
- Va dentro del recuadro punteado (`scopeBoundary`).

### `system` externo (terceros, legados, otras áreas)
```json
{ "id": "sat", "type": "system", "name": "Servicio de Autoridad Fiscal",
  "description": "Recibe y valida facturas electrónicas oficiales.",
  "external": true }
```
- Color gris en el resultado.

---

## Cómo etiquetar relaciones (Nivel 1)

- **Intención de negocio**, no protocolo.
- Verbo activo + complemento corto.
- Ejemplos:
  - ✅ "Compra productos"
  - ✅ "Recibe notificaciones por email"
  - ✅ "Liquida pagos con tarjeta"
  - ❌ "API REST" (es técnico)
  - ❌ "HTTPS" (es protocolo)
  - ❌ "Usa" (sin información)

La dirección de la flecha indica **quién inicia** la interacción.

---

## Casos típicos y cuántos elementos esperar

| Caso | Personas | Sistema foco | Externos | Total |
|---|---|---|---|---|
| App de e-commerce | Cliente, Admin | 1 | Pasarela pagos, Email, ERP | 6 |
| Sistema bancario | Cliente, Soporte | 1 | Mainframe, Antifraude, Email | 6–7 |
| Plataforma SaaS B2B | Usuario, Admin tenant, Soporte | 1 | Auth (Okta), Email, Facturación | 7–8 |
| Pipeline analítico interno | Analista, Data engineer | 1 | Fuentes de datos (3–5) | 6–8 |

Si superas ~15 elementos en un contexto, considera:
- Dividir en **varios** diagramas de contexto por área de negocio.
- Subir a un **System Landscape** que muestre el ecosistema de la organización.

---

## Salida final

Un `.drawio` con:
- Actores arriba (azules / grises según interno o externo).
- El sistema en foco al centro, dentro del recuadro punteado.
- Sistemas externos abajo (grises).
- Flechas etiquetadas con la intención de negocio.

Acompáñalo con una explicación de **por qué** este es el alcance: qué quedó
dentro/fuera, qué relaciones son críticas para el negocio, qué riesgos
representa cada sistema externo.
