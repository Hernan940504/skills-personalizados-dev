# PRD — Plataforma WordPress Multitenant Grupo Bolívar

| Campo | Valor |
|---|---|
| **Producto** | Plataforma WordPress Multitenant (WPMT) Grupo Bolívar |
| **Versión del documento** | 0.1 (Borrador para revisión) |
| **Fecha** | 2026-08-27 |
| **Autor(es)** | Arquitectura Empresarial / Arquitectura de Solución |
| **Estado** | En definición — pendiente de aprobación de Gobierno de TI y stakeholders |
| **Audiencia** | Arquitectura Empresarial, Arquitectura de Solución, Tecnología/Plataformas, Mercadeo, UX, Líderes de línea de negocio, Gobierno de TI, Seguridad |
| **Clasificación** | Interno |

> **Nota de método:** Este documento sigue el flujo *requisitos → diseño → tareas*. Esta versión cubre el **QUÉ** (problema, objetivos, alcance, requisitos) y un **planteamiento de arquitectura (CÓMO)** a nivel de propuesta. Las decisiones marcadas como `[DECISIÓN ABIERTA]` requieren validación antes de pasar a diseño detallado e implementación.

---

## 1. Resumen ejecutivo

El Grupo Bolívar opera hoy múltiples sitios WordPress de forma fragmentada, principalmente sobre las cuentas AWS de **Seguros Bolívar** (dev/stage/prod) y **Ciencuadras** (solo prod). Este modelo genera carga operativa duplicada, pérdida de conocimiento técnico, deuda tecnológica (versiones de PHP y WordPress desactualizadas) y procesos manuales costosos para los equipos de Mercadeo y UX.

Se propone construir una **plataforma WordPress Multitenant centralizada**, en **dos cuentas AWS dedicadas (Stage y Prod)**, **operada por un equipo dedicado (WPMT)** responsable de su soporte, actualización, mantenimiento y seguridad, que apalanque a las distintas marcas del Grupo con administración unificada y libere a los equipos de desarrollo de las líneas de negocio de mantener soluciones de caja.

> **Recomendación central del planteamiento:** la existencia de un **equipo dedicado a operar la plataforma** es condición de éxito, no un detalle organizacional. Es la respuesta directa a la causa raíz de los dolores actuales (ver §8). Sin operación dedicada, la iniciativa reproduce los mismos problemas que busca resolver.

**Primera ola:** Ciencuadras y Proyectiva. **Segunda ola:** Seguros Bolívar, una vez la plataforma esté estable con las dos primeras. El modelo debe permitir sumar marcas de forma incremental según demanda.

**Marcas objetivo mencionadas:** Ciencuadras, Proyectiva, Seguros Bolívar, El Libertador, Jelpit (y otras futuras).

---

## 1.1 Deep research de soporte (ejecutados)

Este planteamiento se fundamenta en dos deep research ya ejecutados y transcritos a Markdown para consulta y generación de artefactos:

| Deep research | Documento | Qué aporta al PRD |
|---|---|---|
| **Validación / contexto** | [`deep-research-validacion.md`](./deep-research-validacion.md) | Casos de industria regulada (Standard Chartered, AXA, Liberty Mutual, Forte), estado del arte de multitenancy, persistencia y promoción de contenido; recomendación de Aurora Serverless v2 (MySQL) y flujo API REST + WP-CLI. Alimenta §1, §4, §5 y arquitectura. |
| **Crítica / riesgos** | [`deep-research-riesgos.md`](./deep-research-riesgos.md) | Antipatrones, riesgos de adopción/técnicos/compliance (SFC 007, Ley 1581), costos ocultos y **gates de cancelación** del proyecto. Alimenta §6, §7, §8, §9 y riesgos. |

**Conclusiones clave que estos deep research introducen en el PRD:**
- El motor de BD **no puede ser PostgreSQL** (la capa de traducción PG4WP causa corrupción). **Gobierno de TI aprobó el uso de MySQL para este caso (2026-08-27)** como excepción al estándar; implementación recomendada: **Amazon Aurora Serverless v2 (MySQL)**.
- La promoción de contenido Stage → Prod **no debe hacerse por sincronización de BD**; el estado del arte es **API REST + WP-CLI** con mapeo por slugs y `Application Passwords`. **Decisión:** aprobación por botón dentro de WordPress (Opción A) que dispara un pipeline DevOps; alcance acotado a **páginas, posts y medios** (menús y configuración quedan fuera). Ver §7.2, cierra Q2.
- La automatización de promoción de **configuración/estructura queda fuera de alcance**; solo se automatiza el contenido editorial. Requiere **PoC** antes de comprometerla.
- El **equipo dedicado es indispensable** (no es un proyecto secundario de administradores generalistas).
- Deben definirse **gates de cancelación** (funcional, compliance, rendimiento CI/CD, TCO vs SaaS).

---

## 2. Contexto y situación actual

### 2.1 Estado actual (As-Is)

| Aspecto | Seguros Bolívar | Ciencuadras |
|---|---|---|
| Cuenta AWS | Propia de la línea | Propia de la línea |
| Ambientes | dev, stage, prod | solo prod |
| Estabilidad | La más estable del Grupo | Deuda técnica (PHP y WP desactualizados) |
| Conocimiento técnico | Equipo con mayor dominio de WP y plugins personalizados | Equipo sin conocimiento de administración/manipulación técnica de WP |
| Cómputo | ECS Fargate | ECS Fargate |
| Persistencia | S3 (plugins, imágenes, media) — se migró de EFS a S3 por costos | S3 |

### 2.2 Dolores identificados (validados con los actores)

**Transversales / técnicos:**
1. **Persistencia de plugins acoplada a S3 + reinicio de Fargate:** cada plugin instalado debe registrarse manualmente en S3 para que al reiniciar la tarea de Fargate no se pierda. Paso manual, propenso a error.
2. **Deuda tecnológica:** versiones de PHP y WordPress desactualizadas; los equipos no saben cómo actualizar plugins ni el core sin romper el sitio.
3. **Pérdida de conocimiento:** el conocimiento técnico se ha ido con la rotación de personal. Cada reemplazo implica reiniciar una curva de aprendizaje de ~2 meses.
4. **Curva de aprendizaje alta:** los ajustes técnicos sobre WordPress (instalaciones/modificaciones solicitadas por usuarios) toman ~2 meses de aprendizaje al equipo técnico de Ciencuadras.

**Del área usuaria (Mercadeo / UX):**
5. **Promoción manual de contenido entre ambientes:** no existe forma sencilla y automatizada de subir a producción el contenido configurado en ambientes bajos. Lo que toma ~1 hora configurar en stage, hay que repetirlo manualmente ~1 hora en prod. **Este es el requisito funcional #1 del área usuaria.**
6. **Falta de ambiente de validación previo (Ciencuadras):** al tener solo prod, UX/Mercadeo no pueden garantizar que lo que hacen quede bien antes de publicar.

### 2.3 Alternativas evaluadas y descartadas

| Alternativa | Resultado | Razón |
|---|---|---|
| Herramientas internas del equipo de Tecnología | Descartada para corto/mediano plazo | Se quedan cortas en SEO, capacidades y flexibilidad que requieren UX/Mercadeo; alcanzar paridad tomaría varios meses. |
| Drupal | Descartada | Complejidad de implementación similar a WordPress, pero se perdería el conocimiento actual de la herramienta y obligaría a reentrenar usuarios, sin reducir la complejidad técnica de administración. |
| **WordPress Multitenant (propuesta)** | **Seleccionada** | Herramienta familiar para los usuarios finales, fácil administración de contenidos, años de experiencia acumulada. Se centraliza y profesionaliza la operación técnica. |

### 2.4 Justificación de la decisión (por qué WordPress)

WordPress es una herramienta **conocida y madura para el usuario final**, de fácil administración de contenidos, con ecosistema robusto de SEO y capacidades de marketing. El problema real no es la herramienta de cara al usuario, sino el **modelo operativo y técnico fragmentado**. La propuesta ataca la causa raíz: centralizar la operación técnica en un equipo dedicado y cuentas dedicadas, conservando la experiencia de usuario que ya funciona.

---

## 3. Objetivos

### 3.1 Objetivos de negocio

- **O1.** Reducir la carga operativa de los equipos de desarrollo de las líneas de negocio, liberándolos para construir producto en lugar de mantener soluciones de caja.
- **O2.** Centralizar y estandarizar la administración, actualización de versiones y mantenimiento de WordPress en un solo frente.
- **O3.** Eliminar la deuda tecnológica recurrente (versiones de PHP/WP) mediante un ciclo de actualización gobernado.
- **O4.** Habilitar la incorporación incremental de nuevas marcas por demanda, con costo marginal decreciente.
- **O5.** Distribuir de forma transparente los costos (CeCo) entre líneas de negocio según consumo y licenciamiento.

### 3.2 Objetivos de producto / experiencia

- **O6.** Automatizar la promoción de contenido de Stage a Prod, eliminando el trabajo manual duplicado.
- **O7.** Garantizar a UX/Mercadeo un ambiente de validación previo (Stage) para todas las marcas.
- **O8.** Preservar la experiencia de administración de contenidos que los usuarios ya conocen.

### 3.3 Métricas de éxito (KPIs propuestos)

| KPI | Línea base actual | Meta |
|---|---|---|
| Tiempo de promoción de contenido stage → prod | ~1 hora manual por publicación | < 10 min, asistido/automatizado `[VALIDAR meta]` |
| Tiempo de incorporación de una nueva marca | N/A (no existe modelo) | < X semanas `[DEFINIR]` |
| Curva de aprendizaje técnico por rotación | ~2 meses | Eliminada para las líneas (absorbida por equipo central) |
| Cobertura de ambiente de validación previo | Parcial (Ciencuadras sin stage) | 100% de marcas con Stage |
| Antigüedad de versiones (PHP/WP) respecto a última estable soportada | Desactualizado | Dentro de ventana de soporte gobernada |
| Disponibilidad de sitios en Prod | Sin SLO formal | SLO definido (ver §8) |

---

## 4. Alcance

### 4.1 Dentro de alcance (MVP)

- Plataforma WordPress multitenant en dos cuentas AWS dedicadas: **Stage** y **Prod**, región **us-east-1 (Virginia)**.
- Onboarding de **Ciencuadras y Proyectiva** en la primera ola; **Seguros Bolívar** en segunda ola.
- **Aislamiento por marca** con base de datos independiente por marca `[DECISIÓN RECOMENDADA — ver §6.2]`.
- **Resolución del dolor de persistencia de plugins** (eliminar el registro manual en S3 tras reinicio de Fargate).
- **Automatización de promoción de contenido Stage → Prod.**
- **Matriz de plugins:** transversales vs por línea de negocio, licenciados vs libres, para distribución de CeCo.
- **Modelo operativo propuesto:** roles, RACI y SLAs del equipo dedicado.
- **Coexistencia en paralelo** con los WordPress actuales hasta estabilizar la nueva plataforma.

### 4.2 Fuera de alcance (MVP) / diferido

- **Ambiente de desarrollo (dev):** descartado. Al ser una solución de caja y por costos, Stage + Prod es suficiente para el área usuaria.
- **Integraciones con sistemas del Grupo** (APIs operativas, Data Operativa vía GraphQL, CRM): no en MVP. La arquitectura debe quedar **preparada** para habilitarlas después. Los sitios son principalmente de contenido y marketing.
- **Migración masiva automatizada de contenido histórico:** el alcance y volumen aún no está claro (ver §9 y preguntas abiertas).
- Marcas fuera de la primera y segunda ola (El Libertador, Jelpit, etc.): incorporación posterior por demanda.

### 4.3 No objetivos

- No se busca reemplazar la experiencia de edición de WordPress por una herramienta nueva.
- No se busca desarrollar un CMS propio.

---

## 5. Usuarios y actores

| Actor | Descripción | Necesidad principal |
|---|---|---|
| **Editores de contenido (Mercadeo/UX)** | Usuarios finales que alimentan los sitios | Administración de contenido familiar, SEO, ambiente de validación, promoción automática a prod |
| **Equipo WordPress dedicado** | Nuevo equipo central de operación (a proponer) | Herramientas de administración unificada, CI/CD, observabilidad, gestión de plugins/versiones |
| **Equipos de desarrollo de las líneas** | Hoy cargan con la operación WP | Liberarse de la operación de la caja |
| **Arquitectura (Empresarial/Solución)** | Gobierna el diseño | Alineación con estándares, seguridad, excepción de stack documentada |
| **Gobierno de TI / Seguridad** | Aprobación y cumplimiento | Excepción de stack, cumplimiento Habeas Data, gestión de secretos, aislamiento |
| **Finanzas / dueños de CeCo** | Distribución de costos | Modelo de costeo por marca y por licenciamiento |

---

## 6. Requisitos

### 6.1 Requisitos funcionales

| ID | Requisito | Prioridad |
|---|---|---|
| RF-01 | La plataforma debe alojar múltiples marcas de forma aislada, cada una con su base de datos independiente. | Alta |
| RF-02 | Debe existir un mecanismo de promoción de contenido Stage → Prod por marca: aprobación por botón en el admin de WordPress que dispara un pipeline DevOps (WP-CLI + API REST). Alcance: páginas, posts y medios (menús y configuración fuera de alcance); ver §7.2. | Alta (crítico usuario) |
| RF-03 | La instalación/actualización de plugins no debe requerir pasos manuales de registro en S3 tras reinicios de cómputo. | Alta |
| RF-04 | Cada marca debe contar con ambiente Stage y Prod. | Alta |
| RF-05 | Debe existir una administración centralizada de versiones de core WP y plugins (plano de control). | Alta |
| RF-06 | Debe soportarse un catálogo de plugins clasificados como transversales o por línea de negocio. | Media |
| RF-07 | Debe registrarse el licenciamiento de cada plugin para la distribución de CeCo. | Media |
| RF-08 | La plataforma debe preservar las capacidades de SEO requeridas por UX/Mercadeo. | Alta |
| RF-09 | El onboarding de una nueva marca debe ser un proceso repetible y documentado (idealmente parametrizado/plantilla). | Media |
| RF-10 | La autenticación de editores debe soportar SSO con el IdP institucional. `[VALIDAR con Seguridad]` | Media |

### 6.2 Requisitos no funcionales

| ID | Requisito | Detalle |
|---|---|---|
| RNF-01 | **Aislamiento** | Blast radius acotado por marca. Una falla, brecha o plugin problemático de una marca no debe afectar a las demás. |
| RNF-02 | **Seguridad** | Secretos en Secret Manager / variables de entorno, nunca en código. Comunicación vía DNS, no IPs estáticas. Encabezados de seguridad (HSTS, CSP, X-Content-Type-Options, etc.). TLS en tránsito. Cumplimiento Habeas Data para cualquier dato personal. |
| RNF-03 | **Disponibilidad** | SLO por definir (ver §8). Producción con alta disponibilidad. |
| RNF-04 | **Escalabilidad** | Incorporación incremental de marcas con costo marginal decreciente. |
| RNF-05 | **Observabilidad** | Logs estructurados centralizados con Correlation-ID; métricas y alertas por marca y plataforma. |
| RNF-06 | **Costos** | Persistencia en S3 (no EFS). Modelo de costeo atribuible por marca (CeCo). |
| RNF-07 | **Mantenibilidad** | Ciclo gobernado de actualización de core/plugins; infraestructura como código. |
| RNF-08 | **Portabilidad/Recuperación** | Backups cifrados por marca con pruebas de restauración. Retención acorde a normativa. |
| RNF-09 | **Resiliencia** | Graceful shutdown de contenedores; estrategia de reinicio sin pérdida de estado (plugins/media). |

---

## 7. Planteamiento de arquitectura

> Esta sección es una **propuesta** para alinear a Arquitectura Empresarial, de Solución y Tecnología. No es diseño detallado. Las decisiones abiertas se resuelven antes de diseño.

### 7.1 Arquitectura Empresarial

**Capacidad de negocio:** "Gestión de Presencia Digital de Marca" como capacidad **compartida y centralizada** del Grupo, ofrecida como servicio interno (modelo *Platform-as-a-Service* interno) a las líneas de negocio.

**Principios rectores:**
- **Centralización de la operación técnica, autonomía del contenido.** El equipo dedicado gobierna plataforma, versiones y seguridad; las marcas mantienen autonomía sobre su contenido.
- **Multitenancy con aislamiento.** Cada marca es un *tenant* aislado.
- **Extensibilidad por demanda.** Nuevas marcas se incorporan mediante un proceso repetible.
- **Costeo transparente.** CeCo atribuibles por consumo y licenciamiento.

**Excepción de stack (obligatoria de documentar y aprobar):**
> WordPress corre sobre **PHP**, catalogado en el marco de arquitectura del Grupo como **legacy — solo mantenimiento**, no apto para proyectos nuevos, y requiere **MySQL/MariaDB**, motores no estándar frente a PostgreSQL. Esta iniciativa se plantea como **excepción arquitectónica formal justificada**: WordPress es un **producto de caja operado**, no una aplicación desarrollada internamente. Las extensiones que el equipo construya alrededor (automatizaciones de CI/CD, APIs de integración, herramientas de plano de control) **deben seguir el stack aprobado** (Node.js, Java/Spring Boot o Python/FastAPI), salvo el código de plugins que por naturaleza vive dentro del ecosistema PHP de WordPress.
>
> **Estado de la excepción:** el uso de **MySQL** fue **aprobado por Gobierno de TI para este caso (2026-08-27)**. Resta formalizar por escrito la excepción de PHP como parte del mismo acuerdo.

### 7.2 Arquitectura de Solución

#### `[DECISIÓN CLAVE]` Modelo de multitenancy

Se evaluaron dos caminos:

| Criterio | A. WordPress Multisite (una instalación, red de sitios) | B. Multi-instancia aislada (una instancia WP por marca, plano de control común) |
|---|---|---|
| Aislamiento entre marcas | Débil (comparten core, plugins, red) | **Fuerte** (cómputo y BD independientes) |
| Blast radius | Alto (un plugin/brecha afecta a toda la red) | **Bajo (acotado por marca)** |
| Base de datos independiente por marca | No nativo (tablas prefijadas en misma BD) | **Sí** |
| Complejidad operativa | Menor (un solo core que actualizar) | Mayor (N instancias, mitigable con automatización/IaC) |
| Actualización unificada de versiones | Nativa | Vía plano de control + pipelines |
| Costo | Menor | Mayor (mitigable con dimensionamiento y compartición de capa base) |
| Alineación con norma "ambientes/datos separados" | Parcial | **Alta** |

**Recomendación:** **Opción B — Multi-instancia aislada, con base de datos independiente por marca.** Coincide con tu preferencia y con el requisito de aislamiento (RNF-01) y separación de datos. La mayor complejidad operativa se mitiga con **Infraestructura como Código** y un **plano de control** que estandarice el ciclo de vida (crear, actualizar, respaldar, promover). Se mantiene abierta a recomendación técnica en la fase de diseño (por ejemplo, un modelo híbrido: capa base/imagen común + instancias aisladas por marca).

#### Vista lógica (conceptual)

```
Cuenta AWS STAGE (us-east-1)                 Cuenta AWS PROD (us-east-1)
┌─────────────────────────────┐              ┌─────────────────────────────┐
│  Plano de control (IaC/CI)  │              │  Plano de control (IaC/CI)  │
│  - Catálogo de plugins      │              │  - Catálogo de plugins      │
│  - Gestión de versiones     │──promoción──▶│  - Gestión de versiones     │
│  - Orquestación onboarding  │  gobernada   │  - Orquestación onboarding  │
├─────────────────────────────┤              ├─────────────────────────────┤
│ Tenant Ciencuadras          │              │ Tenant Ciencuadras          │
│  WP (Fargate) + BD propia   │              │  WP (Fargate) + BD propia   │
│ Tenant Proyectiva           │              │ Tenant Proyectiva           │
│  WP (Fargate) + BD propia   │              │  WP (Fargate) + BD propia   │
│ Tenant Seguros Bolívar (2ª) │              │ Tenant Seguros Bolívar (2ª) │
│  WP (Fargate) + BD propia   │              │  WP (Fargate) + BD propia   │
└─────────────────────────────┘              └─────────────────────────────┘
        │  media/assets                               │  media/assets
        ▼                                             ▼
   S3 por marca                                  S3 por marca
```

#### `[DECISIÓN CLAVE]` Promoción de contenido Stage → Prod (RF-02)

**Advertencia técnica honesta:** en WordPress el contenido vive en la base de datos con **IDs autoincrementales**, media acoplada y datos serializados en `wp_options`. La sincronización directa de BD (volcado o clonado) **queda descartada**: colisiona claves primarias y corrompe datos serializados (ver `deep-research-riesgos.md` y `deep-research-validacion.md`).

**Enfoque decidido:** aprobación por botón dentro de WordPress + motor de promoción por pipeline (WP-CLI + API REST). Se separa el **acto de aprobar** (usuario de negocio, sin fricción técnica) del **motor de promoción** (automatizado, auditable).

**Capa de aprobación — Opción A (decidida para el MVP):** el botón vive **dentro del admin de WordPress (Stage)**, apoyado en un flujo de estados editoriales (borrador → listo → aprobado). Respeta el pilar de "no sacar al usuario de la herramienta que ya conoce". Las opciones B (front satélite en React) y C (herramienta de terceros de content staging) quedan como alternativas evaluables más adelante, no para el MVP.

**Motor de promoción (orquestado por pipeline DevOps):**

```
Usuario aprueba (botón en WP Stage)
  → webhook autenticado dispara el pipeline DevOps (p. ej. GitHub Actions)
     → 1. WP-CLI en Stage extrae el contenido aprobado a JSON normalizado (mapeo por slug/UUID, no por ID autoincremental)
     → 2. valida el payload (esquema; verifica que la media referenciada exista en destino)
     → 3. inyecta en Prod vía API REST (POST /wp-json/wp/v2/...), autenticado con Application Passwords (secretos en Secret Manager)
     → 4. reporta el resultado (éxito/error) de vuelta al usuario de forma asíncrona
```

El core de Producción reasigna IDs, taxonomías y metadatos sin colisiones. La acción es sensible (dispara hacia Prod): webhook autenticado, pipeline con permisos mínimos, sin secretos en el navegador.

**Alcance de la promoción (cierra Q2).** El botón promueve **únicamente contenido editorial discreto: páginas, posts, medios y sus taxonomías asociadas.** Es el alcance que el flujo API REST + WP-CLI garantiza de forma segura (reasignación nativa de IDs, sin corromper datos serializados).

**Explícitamente fuera de alcance de la promoción automatizada:** menús, widgets, configuración global de tema/page builder, ajustes serializados de plugins y cualquier configuración estructural. Estos cambios se gestionan por procedimiento aparte (configuración directa por ambiente o despliegue controlado por el equipo WPMT), no por el botón.

> **Nota de expectativa:** no se promete promover "todo el sitio" con un botón. La promoción automatizada cubre el contenido editorial que produce el día a día de Mercadeo/UX. Ampliar el alcance (p. ej. menús o bloques reutilizables) sería una evolución futura sujeta a su propia PoC, **no forma parte del compromiso actual**.

**Feedback asíncrono:** el pipeline tarda de segundos a minutos; el botón no bloquea. El usuario ve "en proceso" y recibe el resultado (notificación o estado en la misma pantalla). Es diseño de UX real, no un `onclick` síncrono.

**Requiere PoC obligatoria** (RF-02): probar extraer-validar-inyectar con contenido real de una marca, verificando integridad de medios y bloques Gutenberg antes de comprometer el flujo a producción.

### 7.3 Arquitectura de Tecnología

**Cómputo:** ECS Fargate (se conserva el patrón actual conocido por el equipo).

**Persistencia — resolución del dolor RF-03:**

El problema actual es que los plugins/media se guardan en S3 y deben re-registrarse tras reinicios de Fargate. Se proponen dos estrategias complementarias:

1. **Plugins y core: imagen de contenedor inmutable ("horneada").** Los plugins aprobados se incluyen en la imagen Docker versionada, construida por el pipeline del plano de control. Al reiniciar Fargate, la tarea arranca con los plugins ya presentes — **elimina el registro manual en S3**. La instalación de un plugin se vuelve un cambio versionado (PR → build → deploy), no una acción manual en runtime.
2. **Media/uploads (imágenes, archivos subidos por editores): S3 vía offload.** El contenido dinámico que suben los editores se sirve desde S3 mediante un plugin de offload de media, desacoplado del ciclo de vida del contenedor. Se conserva S3 por costos (RNF-06), evitando EFS.

> Este split (plugins en la imagen, media en S3) resuelve la causa raíz: el estado mutable en runtime (uploads) va a S3, y el estado que hoy causa el dolor (plugins) pasa a ser inmutable y versionado. `[VALIDAR en PoC]`

**Base de datos:** una BD independiente por marca (RF-01). Motor: **MySQL — DECISIÓN APROBADA (2026-08-27).** Gobierno de TI autorizó el uso de MySQL para este caso, como excepción al estándar corporativo de PostgreSQL, dado que WordPress no soporta PostgreSQL de forma nativa y estable (las capas de traducción tipo PG4WP causan corrupción de datos e incompatibilidad con plugins — ver `deep-research-validacion.md` y `deep-research-riesgos.md`). Se descartan las soluciones de compatibilidad con PostgreSQL. **Recomendación de implementación: Amazon Aurora Serverless v2 (compatible con MySQL)** por su autoescalado por ACU (eficiente en Stage y marcas de bajo tráfico), tolerancia a fallos Multi-AZ y rendimiento. La elección fina entre Aurora Serverless v2 y RDS MySQL se cierra en diseño según dimensionamiento y costo. La excepción queda formalizada dentro de la excepción de stack de WordPress (ver §7.1).

**Red y seguridad:** VPC por cuenta, comunicación vía DNS (no IPs estáticas), WAF frente a los sitios, TLS, encabezados de seguridad, secretos en Secret Manager. Autorización de administración vía SSO institucional `[VALIDAR]`.

**CI/CD e IaC:** pipelines para build de imágenes, despliegue por tenant y promoción gobernada. Infraestructura como código para el onboarding repetible de marcas (RF-09). El tooling alrededor sigue el stack aprobado (no PHP nuevo fuera de plugins).

**Observabilidad:** logs estructurados centralizados con Correlation-ID, métricas y alertas por tenant (RNF-05).

**Preparación para integraciones futuras (§4.2):** exponer/consumir vía APIs versionadas; dejar el patrón listo para APIs operativas o Data Operativa (GraphQL) cuando se habilite.

---

## 8. Modelo operativo — Equipo dedicado (recomendación formal)

> **Recomendación de arquitectura (no negociable para el éxito de la iniciativa):** la plataforma debe ser **operada por un equipo dedicado a WordPress Multitenant (WPMT)**, responsable del soporte, la actualización de versiones (core y plugins), el mantenimiento, la seguridad y el onboarding de marcas. No es viable operar esta plataforma como un encargo secundario de administradores de propósito general ni dejarla en manos de cada línea de negocio.

**Por qué es una recomendación y no solo una opción:**
- **Es la causa raíz del problema actual.** Los dolores del As-Is (deuda técnica, curva de aprendizaje de ~2 meses por rotación, pérdida de conocimiento) no vienen de WordPress como herramienta, sino de que **nadie lo opera de forma dedicada y continua**. Centralizar la operación en un equipo especializado ataca esa causa.
- **Lo respalda la evidencia.** El `deep-research-validacion.md` documenta que los líderes del sector (Standard Chartered, AXA, Liberty Mutual) resolvieron exactamente este problema con un **equipo de plataforma central** que opera la infraestructura mientras las líneas conservan autonomía de contenido. El `deep-research-riesgos.md` advierte que **subestimar este equipo es la principal causa de fracaso** (colapso operativo, Shadow IT).
- **Habilita el resto del diseño.** La inmutabilidad de imágenes, el pipeline de promoción, el fast-track de seguridad y el onboarding por IaC (ver design.md) **requieren** un dueño técnico permanente; sin él, la arquitectura no se sostiene en el tiempo.
- **Libera a las líneas de negocio (Objetivo O1).** El propósito central de la iniciativa es que Ciencuadras, Proyectiva, Seguros Bolívar y demás **dejen de mantener soluciones de caja** y se enfoquen en producto. Eso solo ocurre si alguien más asume esa operación de forma explícita.

**Modelo de responsabilidad compartida (recomendado):** el equipo WPMT gobierna el **plano de control** (core, infraestructura, seguridad transversal, versiones); las líneas de negocio mantienen la **autonomía sobre su contenido** y, si lo requieren, financian "Administradores Técnicos de Contenido" para su marca. Esto evita que el equipo central se convierta en cuello de botella (riesgo señalado en el deep research).

> El tamaño y la conformación exactos del equipo quedan **por definir** (PRD Q9); lo que esta sección recomienda **formalmente** es que el equipo dedicado **exista** como condición de la iniciativa. La estructura de roles siguiente es una propuesta de punto de partida.

### 8.1 Roles propuestos

| Rol | Responsabilidad | Dedicación sugerida (a validar) |
|---|---|---|
| Líder de plataforma WPMT | Roadmap, gobierno, relación con líneas | 1 |
| Ingeniero(s) de plataforma / DevOps | IaC, CI/CD, cómputo, persistencia, observabilidad | 1–2 |
| Especialista WordPress / plugins | Core, plugins, actualizaciones, soporte técnico | 1–2 |
| Enlace de soporte a marcas | Onboarding, atención a UX/Mercadeo, promoción de contenido | 1 |
| Seguridad (compartido) | Revisión de plugins, cumplimiento, secretos | Parcial |

### 8.2 RACI (resumen)

| Actividad | Equipo WPMT | Línea de negocio (Mercadeo/UX) | Arquitectura | Seguridad |
|---|---|---|---|---|
| Operación de plataforma y versiones | **R/A** | I | C | C |
| Instalación/aprobación de plugins | **R/A** | C | I | C |
| Creación/edición de contenido | I | **R/A** | - | - |
| Promoción de contenido stage→prod | C (herramienta) | **R/A** | I | I |
| Onboarding de nueva marca | **R** | C | **A** | C |
| Gestión de secretos y cumplimiento | R | I | C | **A** |

### 8.3 SLA / SLO propuestos (a validar)

| Indicador | Propuesta inicial |
|---|---|
| Disponibilidad Prod | 99.5% `[VALIDAR]` |
| Tiempo de atención a solicitud técnica de una marca | Bug crítico: 1 día hábil; no crítico: 5 días hábiles |
| Ventana de mantenimiento | Definir por marca, comunicada con anticipación |
| Tiempo de publicación (promoción a prod) | < 10 min asistido `[VALIDAR]` |

---

## 9. Gestión de plugins y costeo (CeCo)

### 9.1 Matriz de plugins (marco a completar)

Se establecerá un **catálogo gobernado de plugins** con esta clasificación, que además alimenta la distribución de CeCo:

| Dimensión | Categorías |
|---|---|
| **Ámbito** | Transversal (aplica a todas las marcas) / Por línea de negocio (específico) |
| **Licenciamiento** | Libre (GPL/gratuito) / Licenciado (costo por sitio o por red) |
| **Criticidad** | Core (SEO, seguridad, caché, media offload) / Complementario |
| **Aprobación de seguridad** | Aprobado / En revisión / Rechazado |

**Ejemplo de estructura (a poblar en diseño):**

| Plugin | Ámbito | Licenciamiento | Criticidad | CeCo asignado |
|---|---|---|---|---|
| SEO (p. ej. suite SEO) | Transversal | `[POR DEFINIR]` | Core | Prorrateo entre marcas |
| Media offload a S3 | Transversal | `[POR DEFINIR]` | Core | Plataforma |
| Staging/migración de contenido | Transversal | `[POR DEFINIR]` | Core | Plataforma |
| Plugin específico marca X | Por línea | `[POR DEFINIR]` | Complementario | Marca X |

> **Nota:** los nombres de plugins concretos se definirán en diseño tras validar existencia, mantenimiento activo y disponibilidad en el repositorio institucional. No se comprometen nombres específicos en este PRD para evitar suposiciones.

### 9.2 Modelo de costeo (CeCo)

- **Costos de plataforma** (plano de control, plugins transversales, equipo): prorrateados entre marcas según modelo a definir (partes iguales, por consumo, o híbrido). `[DEFINIR con Finanzas]`
- **Costos específicos por marca** (cómputo, BD, S3, plugins licenciados por línea): atribuidos directamente a la marca.

---

## 10. Migración y coexistencia

- **Estrategia:** coexistencia en paralelo. Los WordPress actuales siguen operando hasta que la nueva plataforma esté estable con cada marca.
- **Orden:** Ciencuadras y Proyectiva primero; Seguros Bolívar después.
- **Corte:** progresivo por marca, sin *big bang*.
- **Pendientes de definir:** volumen de contenido a migrar por marca; preservación de URLs y SEO histórico (redirects 301); estrategia de migración de media. `[REQUIERE LEVANTAMIENTO]`

---

## 11. Riesgos y mitigaciones

| # | Riesgo | Impacto | Mitigación |
|---|---|---|---|
| R1 | Promoción automática de contenido más compleja de lo esperado (IDs, media, serialización) | Medio (acotado) | Alcance limitado a páginas, posts y medios vía API REST + WP-CLI; menús y configuración fuera de alcance; PoC obligatoria. Ver §7.2 |
| R2 | Tensión de norma de stack: PHP legacy y motor MySQL no estándar | Bajo (reducido) | **MySQL aprobado por Gobierno de TI (2026-08-27).** Resta formalizar por escrito la excepción de PHP; ambas documentadas en §7.1 |
| R3 | Mayor complejidad operativa del modelo multi-instancia | Medio | IaC + plano de control + automatización de onboarding |
| R4 | Dependencia de plugins licenciados y su modelo de licenciamiento en red | Medio | Matriz de plugins con licenciamiento explícito; validar términos multitenant |
| R5 | Curva de conformación del equipo dedicado (no existe hoy) | Medio | Definir roles/RACI temprano; transferencia de conocimiento desde Seguros Bolívar |
| R6 | Seguridad multitenant (aislamiento insuficiente) | Alto | Aislamiento por cómputo y BD; revisión de plugins; WAF; cumplimiento Habeas Data |
| R7 | Costos crecientes al escalar marcas | Medio | Dimensionamiento, compartición de capa base, modelo de costeo por consumo |

---

## 12. Supuestos

- S1. Stage + Prod es suficiente; no se requiere ambiente dev.
- S2. Región única us-east-1 (Virginia).
- S3. Sitios principalmente de contenido y marketing (sin integraciones core en MVP).
- S4. El equipo dedicado se conformará como parte de esta iniciativa.
- S5. La experiencia de edición de WordPress se conserva sin cambios disruptivos para el usuario.

---

## 13. Preguntas abiertas (para resolver antes de diseño detallado)

| # | Pregunta | Responsable | Estado |
|---|---|---|---|
| Q1 | Excepción de stack por Gobierno de TI | Gobierno de TI / Arquitectura | **MySQL: APROBADO (2026-08-27).** Resta formalizar por escrito la excepción de PHP (WordPress como producto de caja) |
| Q2 | Alcance exacto de la promoción stage→prod | Mercadeo/UX + WPMT | **RESUELTA.** Solo páginas, posts y medios; menús y configuración fuera de alcance. Aprobación Opción A (botón en WP) → pipeline. Ver §7.2 |
| Q3 | Motor de BD gestionado definitivo | Arquitectura/Tecnología | **MySQL: APROBADO.** Resta elegir en diseño Aurora Serverless v2 (recomendado) vs RDS MySQL, según dimensionamiento y costo |
| Q4 | Lista concreta y no negociable de capacidades SEO/marketing requeridas | Mercadeo/UX | Parcial (SEO confirmado) |
| Q5 | ¿SSO institucional para administración de editores? | Seguridad | Abierta |
| Q6 | Volumen de contenido a migrar y necesidad de redirects/SEO histórico por marca | Líneas de negocio | Abierta |
| Q7 | Metas cuantitativas de KPIs y SLO/SLA | Negocio + WPMT | Abierta |
| Q8 | Modelo de distribución de CeCo (prorrateo vs consumo) | Finanzas | Abierta |
| Q9 | Tamaño y dedicación definitiva del equipo WPMT | Liderazgo / RRHH | Abierta |

---

## 14. Próximos pasos

1. Revisión del PRD con Arquitectura Empresarial, de Solución y Tecnología.
2. Formalizar por escrito la excepción de stack (MySQL ya aprobado; falta PHP) por Gobierno de TI (Q1) y elegir en diseño el motor gestionado (Q3).
3. Ejecutar la **PoC** de RF-02 (promoción de páginas/posts/medios: botón en WP → pipeline → API REST + WP-CLI) y RF-03. (Alcance Q2 ya cerrado en §7.2.)
4. Definir el modelo operativo y el equipo (Q9).
5. Levantamiento de migración y KPIs (Q6, Q7).
6. Avanzar a la fase de **diseño** (design.md) y luego **tareas** (tasks.md) del ciclo spec-driven.

---

*Documento en borrador. Las secciones marcadas con `[DECISIÓN ABIERTA]`, `[VALIDAR]`, `[DEFINIR]`, `[REQUIERE DECISIÓN]` y `[PENDIENTE]` deben cerrarse antes de pasar a diseño detallado.*
