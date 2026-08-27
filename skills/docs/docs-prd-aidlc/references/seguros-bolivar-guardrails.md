# Guardrails de Seguros Bolívar para el PRD

Restricciones corporativas que el PRD debe respetar al declarar stack, datos y
enfoque técnico. Fuente única de estas reglas para el skill. Si una restricción
aplica pero el dato exacto se desconoce, márcalo `⚠️ POR VALIDAR`.

---

## Stack aprobado (no proponer nada fuera de esto)

**Runtimes**
- Node.js 20.x LTS (Express o Fastify)
- Java JDK 21 LTS (Spring Boot)
- Python 3.12+ (FastAPI — preferido para APIs nuevas y cargas AI/ML)

**Frontend**
- Angular (apps corporativas) o React (interfaces dinámicas). Ambos aprobados.
- Prohibidos: Vue, Svelte, SolidJS, Next.js, Nuxt, Astro.

**Backend**
- Java/Spring Boot, Python/FastAPI, Node.js/Express o Fastify.
- Prohibidos: NestJS, Go/Gin, Rails, Django, Flask, .NET.

**Bases de datos**
- PostgreSQL 15+ (relacional estándar).
- PgVector (búsqueda vectorial sobre PostgreSQL) o Pinecone (vector dedicado
  para similitud AI/ML).
- MongoDB 7.0+ solo para datos no estructurados.
- Prohibidos: MySQL, MariaDB, nuevos esquemas Oracle.

**Datos operativos**
- Data Lake se consume **solo vía APIs GraphQL** (no queries directas a BigQuery).

**Registro de dependencias**
- Todas desde **JFrog Artifactory** institucional. Versiones pineadas (nada de
  `latest`, `^`, `*`).

**Legacy (solo mantenimiento)**
- PHP y Oracle DB existen en sistemas legados. No arrancar nuevos proyectos ahí.

---

## Datos y privacidad

- Datos sensibles regulados por **Habeas Data** (pólizas, clientes, siniestros).
- **Redactar PII** antes de enviar cualquier contenido a modelos de IA.
- Respuestas de API con DTOs allowlisted y **enmascaramiento** de PII/financiero/salud.
- **Retención ≤ 90 días** para datos sensibles.
- Aislamiento de datos entre líneas de negocio (multi-tenancy lógico).
- Trazabilidad/auditoría completa de acciones (correlation-id).

---

## Compliance y seguridad

- **Superintendencia Financiera**: IA en decisiones financieras puede requerir
  supervisión humana.
- **Aprobación dual** (negocio + técnico) para pasar a producción cuando aplique.
- Autenticación entre servicios con JWT del IdP institucional.
- Autorización siempre en backend; nunca en cliente.
- Secretos vía Secret Manager / variables de entorno; nunca en código.
- Sin tokens en `localStorage` (usar cookies httpOnly).

---

## Arquitectura y AI-First (lo que el §7 del PRD debe reflejar)

- Endpoints de IA con **salida estructurada y predecible** (no texto libre).
- **Inferencia asíncrona** para operaciones pesadas (encolar, 202 + job id).
- **Fail-fast** con timeouts bajos para transacciones cortas.
- **Versionado de modelos**; log de inputs/outputs (sin PII).
- Búsqueda por similitud con **PgVector o Pinecone**.
- API First: rutas versionadas (`/api/v1/...`) y contrato OpenAPI.
- Resiliencia: circuit breakers y rate limiting en llamadas externas.
- Gateway de IA **interno** (p. ej. Vertex AI / Gemini vía gateway) — no acceso
  directo a modelos externos cuando la organización así lo exige.

---

## Uso en el PRD

Al llenar §6 (Restricciones) y §7 (Enfoque técnico):
1. Verifica que el stack propuesto esté en la lista aprobada.
2. Declara explícitamente el manejo de PII y la retención de datos.
3. Indica si aplica aprobación dual y supervisión humana.
4. Si algo no encaja con estos guardrails, es un riesgo (§8), no un detalle menor.
