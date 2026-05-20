# Enfoque: Arquitectura Empresarial vs Arquitectura de Soluciones

Antes de dibujar, decide para quién es el diagrama. El mismo sistema se modela distinto según
si la conversación es estratégica (negocio) o técnica (implementación).

---

## Arquitectura Empresarial (estratégico / negocio)

- **Objetivo:** comunicar valor de negocio, alcance y flujos macro de información.
- **Niveles C4:** Nivel 1 (Contexto) y, ocasionalmente, Nivel 2 de alto nivel sin tecnologías.
- **Foco:** actores (usuarios, áreas), sistemas externos, el sistema central como caja negra.
- **Lenguaje:** capacidades de negocio. Evita jerga técnica.
  - ✅ "Sistema de Facturación", "Plataforma de Clientes", "Pasarela de Pagos"
  - ❌ "Microservicio Node.js", "Pod de Kubernetes", "Tabla `invoices`"
- **Relaciones:** describen intención de negocio. "Genera facturas", "Notifica al cliente".
  El protocolo es secundario (puedes omitirlo o dejarlo genérico).
- **Audiencia:** dirección, product owners, stakeholders, arquitectos empresariales.

**Señales en la petición:** "visión general", "para presentar a negocio", "cómo encaja en la
organización", "stakeholders", "valor", "panorama".

---

## Arquitectura de Soluciones (técnico / implementación)

- **Objetivo:** guiar el diseño y la construcción; base para decisiones técnicas.
- **Niveles C4:** Nivel 2 (Contenedores) y Nivel 3 (Componentes).
- **Foco:** tecnologías concretas, bases de datos, APIs, colas, protocolos, microservicios.
- **Lenguaje:** técnico y específico.
  - ✅ "API Gateway (Kong)", "Base de Datos Relacional (PostgreSQL 15)", "Cola (RabbitMQ)"
  - ✅ Relaciones con protocolo: "Publica eventos [AMQP]", "Consulta [gRPC]", "Lee/escribe [JDBC]"
- **Relaciones:** SIEMPRE con propósito + protocolo/tecnología.
- **Audiencia:** equipo de desarrollo, arquitectos de solución, DevOps/SRE.

**Señales en la petición:** "arquitectura técnica", "los servicios", "la base de datos", "las
colas", nombres de tecnologías, "cómo se comunica X con Y", "microservicios".

---

## Tabla de decisión rápida

| Criterio | Empresarial | Soluciones |
|---|---|---|
| Nivel C4 principal | 1 (Contexto) | 2–3 (Contenedores/Componentes) |
| ¿Muestra tecnologías? | No | Sí, explícitas |
| ¿Muestra BDs/colas internas? | No | Sí |
| Etiqueta de relación | Intención de negocio | Propósito + protocolo |
| Audiencia | Negocio / estrategia | Ingeniería |

---

## Casos mixtos

Si el usuario quiere "ver todo", entrega una **secuencia progresiva** (no un solo diagrama
sobrecargado): primero Contexto (lenguaje de negocio) y luego Contenedores (lenguaje técnico).
Cada uno en su propio `.drawio`. Esto respeta ambas audiencias y la regla de abstracción estricta.

Cuando dudes del enfoque, **pregunta**: "¿Este diagrama es para una conversación de negocio
(alto nivel, sin tecnologías) o para el equipo técnico (con servicios, BDs y protocolos)?"
