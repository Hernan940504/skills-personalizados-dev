# Tasks — Plataforma WordPress Multitenant Grupo Bolívar

| Campo | Valor |
|---|---|
| **Producto** | Plataforma WordPress Multitenant (WPMT) Grupo Bolívar |
| **Documento** | Plan de implementación detallado (tasks.md) |
| **Versión** | 0.2 (Borrador detallado) |
| **Fecha** | 2026-08-27 |
| **Basado en** | [`PRD`](./PRD-wordpress-multitenant-grupo-bolivar.md) · [`design.md`](./design.md) · [`deep-research-validacion.md`](./deep-research-validacion.md) · [`deep-research-riesgos.md`](./deep-research-riesgos.md) |
| **Clasificación** | Interno |

> **Cómo leer este plan.** Cada tarea es una ficha con: **responsable** (rol), **prerrequisitos** (qué debe estar listo antes de empezar), **descripción**, **entregable** y **criterio de aceptación**. Los responsables se asignan **por rol** porque el equipo aún no está conformado (PRD Q9); cuando exista, se sustituyen por nombres. Las tareas de actores externos (Gobierno de TI, Finanzas, Mercadeo, Seguridad corporativa) se marcan como tal.

---

## Roles referenciados (RACI)

| Rol | Sigla | Alcance |
|---|---|---|
| Líder de plataforma WPMT | **LID** | Roadmap, gobierno, relación con líneas, aprobaciones internas |
| Ingeniero de plataforma / DevOps | **DEVOPS** | IaC, CI/CD, cómputo, red, persistencia |
| Especialista WordPress / plugins | **WPENG** | Core WP, plugins, imágenes, promoción de contenido |
| Enlace de soporte a marcas | **ENLACE** | Onboarding funcional, capacitación, atención a Mercadeo/UX |
| Seguridad de la Información (corporativo) | **SEC** | Revisión de plugins, compliance, secretos, WAF |
| Gobierno de TI (corporativo) | **GOBTI** | Excepciones de stack, aprobaciones de arquitectura |
| Finanzas / dueños de CeCo (corporativo) | **FIN** | Modelo de costeo |
| Arquitectura (Empresarial/Solución) | **ARQ** | Diseño, gates, alineación |
| Mercadeo / UX (línea de negocio) | **MKT** | Contenido, validación funcional, requisitos SEO |

> Prerrequisito transversal a **toda** tarea técnica: credenciales AWS SSO vigentes en la cuenta correspondiente (Stage/Prod) con el rol adecuado, y acceso al repositorio de IaC y a JFrog. No se repite en cada ficha.

---

## Estados

☐ pendiente · ◐ en progreso · ☑ hecho · ⛔ bloqueada (esperando prerrequisito)

---

# OLA 0 — Fundación y cierre de decisiones (GATE OBLIGATORIO)

> No se construye ningún tenant hasta cerrar esta ola completa.

## Bloque A — Gobierno y decisiones

### O0-GOB-1 · Formalizar excepción de stack (PHP)
- **Responsable:** GOBTI (decide) · ARQ (prepara el sustento)
- **Prerrequisitos:** PRD §7.1 redactado (✅ ya existe); MySQL ya aprobado (2026-08-27); deep research disponibles como sustento técnico.
- **Descripción:** Presentar al comité de Gobierno de TI el waiver formal para operar PHP (WordPress como producto de caja). Documentar controles compensatorios (WAF, inmutabilidad, escaneo, aislamiento).
- **Entregable:** Acta de aprobación firmada del waiver PHP.
- **Criterio de aceptación:** Documento aprobado y archivado; referenciado en el PRD.
- **Ref:** Q1, PRD §7.1 · **Estado:** ☐

### O0-GOB-2 · Confirmar motor de BD gestionado
- **Responsable:** ARQ + DEVOPS (recomiendan) · GOBTI (avala)
- **Prerrequisitos:** O0-GOB-1 cerrada; datos de dimensionamiento §5.1 (✅ ya medidos); recomendación Aurora Serverless v2 (✅ en design D1).
- **Descripción:** Decisión final Aurora Serverless v2 vs RDS MySQL, con base en costo (§5.2) y dimensionamiento (§5.1). Documentar rango de ACU por ambiente.
- **Entregable:** ADR (Architecture Decision Record) del motor de BD.
- **Criterio de aceptación:** ADR aprobado por ARQ; parámetros de ACU definidos para IaC.
- **Ref:** D1, Q3 · **Estado:** ☐

### O0-GOB-3 · Definir KPIs y SLO por servicio
- **Responsable:** LID + ARQ · con insumo de MKT (expectativa de publicación)
- **Prerrequisitos:** Datos de tráfico y latencia §5.1 (✅); acuerdo con líderes de línea sobre criticidad.
- **Descripción:** Definir disponibilidad objetivo (propuesta 99.5%), tiempo de publicación (<10 min), latencia p95, ventana de mantenimiento. Documentar de dónde sale cada métrica (auditable).
- **Entregable:** Documento de SLO/SLA con línea base y target.
- **Criterio de aceptación:** SLO medibles y aprobados; alertas correspondientes definidas para O1-OBS-1.
- **Ref:** D7, Q7 · **Estado:** ☐

### O0-GOB-4 · Confirmar SSO institucional para editores
- **Responsable:** SEC (define) · DEVOPS (integra) · WPENG (configura en WP)
- **Prerrequisitos:** Inventario de editores por marca; IdP institucional disponible; política de acceso definida.
- **Descripción:** Confirmar integración de WordPress con el IdP institucional (SSO) para editores; definir mapeo de roles WP.
- **Entregable:** Diseño de integración SSO + mapeo de roles.
- **Criterio de aceptación:** SEC aprueba; probado en la PoC de una marca.
- **Ref:** D5, Q5 · **Estado:** ☐

### O0-GOB-5 · Definir modelo de costeo CeCo
- **Responsable:** FIN (decide) · LID (aporta drivers de costo §5.2)
- **Prerrequisitos:** Estimación de costos §5.2 (✅); listado de marcas y su facturación relativa.
- **Descripción:** Definir prorrateo de costos compartidos (plataforma base) y atribución directa por marca (según §5.2), incluyendo licencias.
- **Entregable:** Modelo de costeo CeCo aprobado.
- **Criterio de aceptación:** FIN aprueba; regla clara de prorrateo (partes iguales / consumo / híbrido).
- **Ref:** Q8, PRD §9.2 · **Estado:** ☐

### O0-GOB-6 · Aprobar catálogo de plugins
- **Responsable:** SEC (aprueba seguridad) · WPENG (propone) · MKT (valida funcionalidad)
- **Prerrequisitos:** Catálogo propuesto (✅ design §9.2); política de fuentes confiables (✅ §9.2.3).
- **Descripción:** Revisar y aprobar plugins transversales y por marca; verificar fuente oficial, mantenimiento activo, licenciamiento; descartar cualquier fuente nulled.
- **Entregable:** Catálogo de plugins aprobado (transversales + por marca) con fuente y licencia de cada uno.
- **Criterio de aceptación:** SEC firma; cada plugin tiene fuente oficial verificada y disponible en JFrog.
- **Ref:** PRD §9, design §9.2 · **Estado:** ☐

## Bloque B — Equipo dedicado (recomendación formal, condición de éxito)

### O0-OPS-1 · Aprobar conformación del equipo WPMT
- **Responsable:** GOBTI + LID (patrocinio) · ARQ (justifica)
- **Prerrequisitos:** Recomendación formal PRD §8 (✅); caso de negocio con TCO (§5.2 + costo de equipo).
- **Descripción:** Obtener aprobación ejecutiva para conformar el equipo dedicado, según la recomendación del PRD §8.
- **Entregable:** Aprobación del equipo (headcount y presupuesto).
- **Criterio de aceptación:** Presupuesto asignado; sponsor confirmado.
- **Ref:** PRD §8, Q9 · **Estado:** ☐ · **Nota:** habilita casi todas las tareas técnicas siguientes.

### O0-OPS-2 · Definir tamaño, roles y RACI del equipo
- **Responsable:** LID · con ARQ
- **Prerrequisitos:** O0-OPS-1 cerrada.
- **Descripción:** Concretar el número de personas por rol (propuesta PRD §8.1) y la matriz RACI operativa.
- **Entregable:** Organigrama del equipo + RACI detallado.
- **Criterio de aceptación:** Roles cubiertos o en proceso de contratación; RACI aprobado.
- **Ref:** Q9, PRD §8.1-8.2 · **Estado:** ☐

### O0-OPS-3 · Transferencia de conocimiento desde Seguros Bolívar
- **Responsable:** WPENG (recibe) · equipo actual de Seguros Bolívar (transfiere) · LID (coordina)
- **Prerrequisitos:** O0-OPS-2 (equipo existente); acceso al WordPress actual del portal (✅ cuentas identificadas).
- **Descripción:** Documentar plugins actuales, personalizaciones, cron, integraciones y "conocimiento tribal" del portal actual antes de que se pierda.
- **Entregable:** Runbook del estado actual + inventario de plugins/personalizaciones.
- **Criterio de aceptación:** El equipo WPMT puede operar el portal actual sin depender del personal saliente.
- **Ref:** PRD §8, R5 · **Estado:** ☐

### O0-OPS-4 · Definir modelo de responsabilidad compartida
- **Responsable:** LID + ARQ · con líderes de línea
- **Prerrequisitos:** O0-OPS-2.
- **Descripción:** Formalizar la frontera plano de control (WPMT) vs contenido (líneas), incluyendo el rol opcional de "Administrador Técnico de Contenido" por marca.
- **Entregable:** Documento de responsabilidad compartida + fast-track de aprobación de plugins.
- **Criterio de aceptación:** Aprobado por líneas de negocio; evita el cuello de botella (riesgo del deep research).
- **Ref:** PRD §8 · **Estado:** ☐

## Bloque C — PoC de promoción de contenido (el mayor riesgo)

### O0-PROMO-1 · PoC extracción vía WP-CLI
- **Responsable:** WPENG · apoyo DEVOPS
- **Prerrequisitos:** Un WordPress de prueba en Stage con contenido representativo (páginas, posts, medios, bloques Gutenberg); WP-CLI disponible.
- **Descripción:** Script que extrae contenido aprobado a JSON normalizado, mapeando por slug/UUID (no por ID autoincremental).
- **Entregable:** Script de extracción + JSON de muestra.
- **Criterio de aceptación:** El JSON captura páginas/posts/medios y sus relaciones sin depender de IDs.
- **Ref:** RF-02, R1, design §7 · **Estado:** ☐

### O0-PROMO-2 · PoC inyección vía API REST
- **Responsable:** WPENG · apoyo DEVOPS · SEC (valida Application Passwords)
- **Prerrequisitos:** O0-PROMO-1; WordPress de prueba en "Prod"; Application Passwords configuradas; Secrets Manager disponible.
- **Descripción:** Inyectar el JSON en el WP destino vía `POST /wp-json/...`, dejando que el core reasigne IDs. Autenticación con Application Passwords desde Secrets Manager.
- **Entregable:** Script de inyección + evidencia de creación sin colisión de IDs.
- **Criterio de aceptación:** Contenido creado en destino con IDs nuevos, sin sobrescribir datos existentes.
- **Ref:** RF-02, design §7 · **Estado:** ☐

### O0-PROMO-3 · PoC integridad de medios y Gutenberg
- **Responsable:** WPENG · MKT (valida visualmente)
- **Prerrequisitos:** O0-PROMO-2; contenido con imágenes y bloques Gutenberg complejos.
- **Descripción:** Verificar que medios y bloques (referencias `wp:image {"id":...}`) queden correctos tras la promoción; reconciliar IDs de medios si es necesario.
- **Entregable:** Reporte de integridad con casos borde probados.
- **Criterio de aceptación:** Sin imágenes rotas ni bloques corruptos en el destino; MKT confirma fidelidad visual.
- **Ref:** R1, design §7 · **Estado:** ☐

### O0-PROMO-4 · GATE FUNCIONAL de promoción
- **Responsable:** ARQ (decide) · LID · WPENG (presenta resultados)
- **Prerrequisitos:** O0-PROMO-1/2/3 completas.
- **Descripción:** Evaluar la PoC contra el gate: si hay corrupción serializada, colisión de IDs o Gutenberg irresoluble → replantear alcance o herramienta antes de continuar.
- **Entregable:** Decisión de gate documentada (pasa / replantea).
- **Criterio de aceptación:** Gate superado explícitamente, o plan alternativo aprobado.
- **Ref:** design §16 (gate), Q2 · **Estado:** ☐ · **Nota:** bloquea toda la Ola 1 de promoción.

### O0-PROMO-5 · Decidir plugin/estados editoriales del botón
- **Responsable:** WPENG + ENLACE · con MKT
- **Prerrequisitos:** O0-PROMO-4 superado.
- **Descripción:** Definir el flujo de estados editoriales (borrador → listo → aprobado) y el plugin/implementación del botón "Promover" (Opción A, dentro de WP).
- **Entregable:** Especificación del botón + estados.
- **Criterio de aceptación:** MKT valida que el flujo es simple y familiar.
- **Ref:** D3 · **Estado:** ☐

### O0-PROMO-6 · Decidir herramienta de pipeline + webhook seguro
- **Responsable:** DEVOPS + SEC
- **Prerrequisitos:** O0-PROMO-4 superado.
- **Descripción:** Elegir el orquestador (GitHub Actions u otro aprobado) y el patrón de webhook autenticado (firma/secreto) desde WP hacia el pipeline.
- **Entregable:** ADR de pipeline + patrón de webhook.
- **Criterio de aceptación:** SEC aprueba el patrón de autenticación; sin secretos en el navegador.
- **Ref:** D4 · **Estado:** ☐

## Bloque D — PoC de persistencia (imagen inmutable)

### O0-WP-1 · PoC imagen con plugins horneados
- **Responsable:** WPENG + DEVOPS
- **Prerrequisitos:** O0-GOB-6 (catálogo aprobado); JFrog con repos Composer configurados; ECR disponible.
- **Descripción:** Construir imagen Docker con core + plugins vía Composer desde JFrog; arrancar en Fargate con FS de solo lectura.
- **Entregable:** Imagen base funcional + Dockerfile multi-stage.
- **Criterio de aceptación:** El contenedor arranca con plugins presentes tras reinicio, sin registro manual en S3.
- **Ref:** RF-03, design §8 · **Estado:** ☐

### O0-WP-2 · PoC media offload a S3
- **Responsable:** WPENG + DEVOPS
- **Prerrequisitos:** O0-WP-1; bucket S3 + CloudFront de prueba.
- **Descripción:** Configurar offload de media a S3 y servir vía CloudFront; verificar que el estado dinámico sobrevive al reinicio del contenedor.
- **Entregable:** Configuración de offload + evidencia.
- **Criterio de aceptación:** Media subida sobrevive reinicios; se sirve desde CDN.
- **Ref:** RF-03, design §5.1 · **Estado:** ☐

### O0-WP-3 · Decidir inmutable puro vs EFS acotado
- **Responsable:** DEVOPS + WPENG · ARQ (avala)
- **Prerrequisitos:** O0-WP-1/2; lista de plugins que exigen escritura local (de O0-GOB-6).
- **Descripción:** Determinar si algún plugin transversal requiere escritura local (caché) y si se resuelve con object cache Redis o con EFS acotado a rutas específicas.
- **Entregable:** ADR de persistencia (D2).
- **Criterio de aceptación:** Decisión documentada; sin plugins fallando silenciosamente por FS de solo lectura.
- **Ref:** D2 · **Estado:** ☐

## Bloque E — IaC base, pipeline y seguridad

### O0-INFRA-1 · Provisionar cuentas AWS Stage y Prod
- **Responsable:** DEVOPS · GOBTI (habilita cuentas)
- **Prerrequisitos:** O0-GOB-1 (waiver); cuentas dedicadas autorizadas; acceso SSO.
- **Descripción:** Habilitar las dos cuentas dedicadas (us-east-1), baseline de seguridad y facturación separada.
- **Entregable:** Cuentas Stage y Prod operativas con guardrails.
- **Criterio de aceptación:** Ambientes físicamente separados (gobierno de TI ✅), acceso por SSO.
- **Ref:** PRD §4, design §5 · **Estado:** ☐

### O0-INFRA-2 · Módulo IaC base (VPC, red, NAT, ECR)
- **Responsable:** DEVOPS
- **Prerrequisitos:** O0-INFRA-1; repositorio de IaC; estándar de red del Grupo.
- **Descripción:** Módulo reutilizable: VPC, subredes Multi-AZ, NAT, ECR, DNS. Parametrizable por ambiente.
- **Entregable:** Módulo IaC versionado + documentación.
- **Criterio de aceptación:** `terraform plan/apply` idempotente; revisado por ARQ.
- **Ref:** RNF-07, design §5 · **Estado:** ☐

### O0-INFRA-3 · Módulo IaC de tenant parametrizable
- **Responsable:** DEVOPS · con WPENG
- **Prerrequisitos:** O0-INFRA-2; O0-GOB-2 (motor de BD decidido); parámetros de dimensionamiento §5.1.3.
- **Descripción:** Módulo que crea un tenant completo: ECS (tamaños por ambiente), Aurora Serverless v2 (rango ACU), S3, Redis, Secrets, autoscaling (Prod 2-4, Stage 2).
- **Entregable:** Módulo de tenant + variables documentadas.
- **Criterio de aceptación:** Crea un tenant de prueba end-to-end con un solo comando parametrizado.
- **Ref:** RF-09, design §9 · **Estado:** ☐

### O0-PIPE-1 · Pipeline base CI/CD
- **Responsable:** DEVOPS · SEC (valida controles)
- **Prerrequisitos:** O0-INFRA-2; O0-PROMO-6 (herramienta elegida); JFrog.
- **Descripción:** Pipeline con build multi-stage, escaneo SCA + imagen, `--no-scripts` en Composer, cooldown 72h, deploy rolling a Stage y blue/green a Prod, rollback.
- **Entregable:** Pipeline funcional + documentación del flujo (design §9.1).
- **Criterio de aceptación:** Un cambio pasa por todo el flujo hasta un tenant de prueba; rollback probado.
- **Ref:** design §8, §9.1 · **Estado:** ☐

### O0-SEC-1 · Cloudflare + CloudFront + WAF con anti-bypass
- **Responsable:** SEC + DEVOPS
- **Prerrequisitos:** O0-INFRA-1; cuenta Cloudflare; reglas WAF gestionadas identificadas.
- **Descripción:** Configurar Cloudflare (DNS, DDoS, bots) delante de CloudFront + WAF (reglas OWASP + WordPress + PHP); restringir origen para impedir bypass (header secreto/mTLS + IPs Cloudflare).
- **Entregable:** Configuración perimetral + prueba de que no se puede saltar Cloudflare.
- **Criterio de aceptación:** Petición directa a CloudFront sin pasar por Cloudflare es rechazada.
- **Ref:** D8, design §10-11 · **Estado:** ☐

### O0-SEC-2 · Secrets Manager + least-privilege
- **Responsable:** SEC + DEVOPS
- **Prerrequisitos:** O0-INFRA-2.
- **Descripción:** Estructura de secretos por marca/ambiente; políticas IAM de mínimo privilegio para el pipeline y las tareas.
- **Entregable:** Estructura de secretos + políticas IAM.
- **Criterio de aceptación:** SEC audita; sin secretos en código ni en imágenes.
- **Ref:** RNF-02, design §10 · **Estado:** ☐

**🚦 SALIDA DE OLA 0 (gate):** todas las decisiones cerradas, equipo aprobado y conformándose, PoC de promoción (O0-PROMO-4) y persistencia superadas, IaC base + pipeline + perímetro funcionando. **Solo entonces inicia la Ola 1.**

---

# OLA 1 — Primeras marcas (Ciencuadras y Proyectiva)

> Prerrequisito global de la ola: **Ola 0 cerrada** (gate superado). No repetir en cada ficha.

## Onboarding Ciencuadras

### O1-INFRA-1 · Medir tráfico real de Ciencuadras
- **Responsable:** DEVOPS · con acceso a la cuenta de Ciencuadras
- **Prerrequisitos:** Acceso SSO a la cuenta AWS de Ciencuadras (rol ViewOnly); método de medición §5.1 (✅ documentado).
- **Descripción:** Repetir el análisis de CloudWatch (CPU, memoria, RPS, latencia, BD) sobre el WordPress actual de Ciencuadras.
- **Entregable:** Reporte de dimensionamiento de Ciencuadras.
- **Criterio de aceptación:** Tamaños de tarea y rango ACU ajustados a su perfil real.
- **Ref:** design §5.1.4 · **Estado:** ☐

### O1-INFRA-2 · Provisionar tenant Ciencuadras
- **Responsable:** DEVOPS
- **Prerrequisitos:** O1-INFRA-1; módulo IaC de tenant (O0-INFRA-3).
- **Descripción:** Instanciar tenant con IaC. Stage: 2 tareas 0.5vCPU/1GB. Prod: 2-4 tareas 1vCPU/2GB, Multi-AZ.
- **Entregable:** Tenant Ciencuadras en Stage y Prod.
- **Criterio de aceptación:** Ambientes activos; autoscaling Prod 2-4, Stage 2 configurado.
- **Ref:** RF-01, design §5.1.3 · **Estado:** ☐

### O1-INFRA-3 · BD Aurora + Redis por marca
- **Responsable:** DEVOPS
- **Prerrequisitos:** O1-INFRA-2.
- **Descripción:** Aurora Serverless v2 (Prod 0.5-4 ACU Multi-AZ writer+reader / Stage 0.5-2 ACU) + ElastiCache Redis; credenciales en Secrets Manager.
- **Entregable:** BD y cache por marca, aisladas.
- **Criterio de aceptación:** Sin acceso cruzado entre BD; cifrado en reposo y tránsito.
- **Ref:** RF-01, D6, design §6 · **Estado:** ☐

### O1-WP-1 · Imagen derivada Ciencuadras
- **Responsable:** WPENG
- **Prerrequisitos:** Imagen base (O0-WP-1); plugins por marca de Ciencuadras definidos y aprobados (O0-GOB-6).
- **Descripción:** Construir imagen derivada (multi-stage) con base + plugins específicos del tema de Ciencuadras (page builder, etc.).
- **Entregable:** Imagen Ciencuadras en ECR.
- **Criterio de aceptación:** Solo los plugins requeridos por Ciencuadras; escaneo limpio.
- **Ref:** design §9.2.2 · **Estado:** ☐

### O1-PROMO-1 · Habilitar promoción para Ciencuadras
- **Responsable:** WPENG + DEVOPS
- **Prerrequisitos:** O1-WP-1; botón/estados (O0-PROMO-5); pipeline (O0-PIPE-1).
- **Descripción:** Activar el botón de promoción + webhook + pipeline para Ciencuadras (páginas/posts/medios).
- **Entregable:** Flujo de promoción operativo para la marca.
- **Criterio de aceptación:** Una promoción real de Stage a Prod exitosa y auditable.
- **Ref:** RF-02 · **Estado:** ☐

### O1-OBS-1 · Observabilidad Ciencuadras
- **Responsable:** DEVOPS
- **Prerrequisitos:** O1-INFRA-2; SLO definidos (O0-GOB-3).
- **Descripción:** Logs estructurados centralizados con correlation-id, métricas y alertas por tenant contra los SLO.
- **Entregable:** Dashboards + alertas.
- **Criterio de aceptación:** Alertas disparan ante degradación; trazabilidad end-to-end.
- **Ref:** RNF-05, design §9.1 · **Estado:** ☐

### O1-MIG-1 · Migrar contenido de Ciencuadras
- **Responsable:** ENLACE + WPENG · con MKT de Ciencuadras
- **Prerrequisitos:** O1-WP-1; inventario de contenido actual; mapa de URLs y redirects.
- **Descripción:** Migrar contenido; preservar URLs/SEO con redirects 301; validar volumen.
- **Entregable:** Contenido migrado + tabla de redirects.
- **Criterio de aceptación:** Sin pérdida de posicionamiento; MKT valida contenido.
- **Ref:** Q6, PRD §10 · **Estado:** ☐

### O1-OPS-1 · Capacitación editorial Ciencuadras
- **Responsable:** ENLACE · a MKT de Ciencuadras
- **Prerrequisitos:** O1-PROMO-1.
- **Descripción:** Capacitar a editores en el flujo de contenido y el botón de promoción.
- **Entregable:** Editores capacitados + guía rápida.
- **Criterio de aceptación:** Un editor promueve contenido sin asistencia técnica.
- **Ref:** PRD §8 · **Estado:** ☐

## Onboarding Proyectiva

### O1-INFRA-4 · Medir tráfico real de Proyectiva
- **Responsable:** DEVOPS · con acceso a la cuenta de Proyectiva
- **Prerrequisitos:** Acceso SSO a la cuenta de Proyectiva.
- **Descripción / Entregable / Criterio:** Igual patrón que O1-INFRA-1, para Proyectiva.
- **Ref:** design §5.1.4 · **Estado:** ☐

### O1-INFRA-5 · Provisionar tenant Proyectiva
- **Responsable:** DEVOPS
- **Prerrequisitos:** O1-INFRA-4; módulo IaC (O0-INFRA-3).
- **Descripción / Entregable / Criterio:** Igual patrón que O1-INFRA-2.
- **Ref:** RF-01 · **Estado:** ☐

### O1-WP-2 · Imagen derivada Proyectiva
- **Responsable:** WPENG
- **Prerrequisitos:** Imagen base; plugins de Proyectiva aprobados.
- **Descripción / Entregable / Criterio:** Igual patrón que O1-WP-1.
- **Ref:** design §9.2.2 · **Estado:** ☐

### O1-PROMO-2 · Habilitar promoción para Proyectiva
- **Responsable:** WPENG + DEVOPS
- **Prerrequisitos:** O1-WP-2; botón/pipeline (Ola 0).
- **Descripción / Entregable / Criterio:** Igual patrón que O1-PROMO-1.
- **Ref:** RF-02 · **Estado:** ☐

### O1-MIG-2 · Migrar contenido de Proyectiva
- **Responsable:** ENLACE + WPENG · con MKT de Proyectiva
- **Prerrequisitos:** O1-WP-2; inventario + redirects.
- **Descripción / Entregable / Criterio:** Igual patrón que O1-MIG-1.
- **Ref:** Q6, PRD §10 · **Estado:** ☐

### O1-OPS-2 · Capacitación editorial Proyectiva
- **Responsable:** ENLACE · a MKT de Proyectiva
- **Prerrequisitos:** O1-PROMO-2.
- **Descripción / Entregable / Criterio:** Igual patrón que O1-OPS-1.
- **Ref:** PRD §8 · **Estado:** ☐

## Estabilización Ola 1

### O1-OPS-3 · Coexistencia en paralelo
- **Responsable:** LID + DEVOPS
- **Prerrequisitos:** O1-MIG-1, O1-MIG-2.
- **Descripción:** Mantener los WordPress actuales operando en paralelo hasta estabilizar los nuevos.
- **Entregable:** Plan de coexistencia con criterios de estabilidad.
- **Criterio de aceptación:** Ambos entornos accesibles; sin pérdida de servicio.
- **Ref:** PRD §10 · **Estado:** ☐

### O1-OPS-4 · Validar SLO/KPIs con datos reales
- **Responsable:** LID + DEVOPS
- **Prerrequisitos:** O1-OBS-1; SLO (O0-GOB-3); 2-4 semanas de operación.
- **Descripción:** Contrastar SLO objetivo vs comportamiento real de las 2 marcas.
- **Entregable:** Reporte de cumplimiento de SLO.
- **Criterio de aceptación:** SLO cumplidos o plan de ajuste definido.
- **Ref:** Q7, D7 · **Estado:** ☐

### O1-SEC-3 · Simulacro fast-track de seguridad (gate)
- **Responsable:** SEC + DEVOPS
- **Prerrequisitos:** Pipeline (O0-PIPE-1); WAF (O0-SEC-1).
- **Descripción:** Simular una vulnerabilidad zero-day y medir tiempo de mitigación (virtual patching en WAF + parche por pipeline).
- **Entregable:** Reporte del simulacro con tiempos.
- **Criterio de aceptación:** Mitigación efectiva dentro de la ventana; si no, reforzar WAF/proceso.
- **Ref:** design §9.1.2, §16 · **Estado:** ☐

### O1-OPS-5 · Cutover progresivo Ola 1
- **Responsable:** LID + DEVOPS · con MKT
- **Prerrequisitos:** O1-OPS-3, O1-OPS-4 (estabilidad confirmada).
- **Descripción:** Apagar los WordPress viejos de Ciencuadras y Proyectiva de forma progresiva.
- **Entregable:** Marcas 100% en la nueva plataforma.
- **Criterio de aceptación:** Sin incidentes de disponibilidad ni SEO tras el cutover.
- **Ref:** PRD §10 · **Estado:** ☐

---

# OLA 2 — Marca estable (Seguros Bolívar)

> Prerrequisito global: **Ola 1 estabilizada** (O1-OPS-5 hecha).

### O2-INFRA-1 · Confirmar dimensionamiento Seguros Bolívar
- **Responsable:** DEVOPS
- **Prerrequisitos:** Datos §5.1 ya capturados (✅); acceso a cuentas Portal Web (✅).
- **Descripción:** Refinar dimensionamiento con los datos ya medidos; validar picos de campaña con MKT.
- **Entregable:** Dimensionamiento confirmado.
- **Criterio de aceptación:** Tamaños y ACU ajustados; ventana de campaña considerada.
- **Ref:** design §5.1 · **Estado:** ☐

### O2-INFRA-2 · Provisionar tenant Seguros Bolívar
- **Responsable:** DEVOPS
- **Prerrequisitos:** O2-INFRA-1; módulo IaC (O0-INFRA-3).
- **Descripción / Entregable / Criterio:** Igual patrón que O1-INFRA-2, con el dimensionamiento de SB.
- **Ref:** RF-01 · **Estado:** ☐

### O2-WP-1 · Imagen derivada Seguros Bolívar
- **Responsable:** WPENG
- **Prerrequisitos:** O2-INFRA-2; inventario de plugins del portal actual (O0-OPS-3); aprobación SEC.
- **Descripción:** Imagen con plugins del portal actual, auditados y saneados.
- **Entregable:** Imagen SB en ECR.
- **Criterio de aceptación:** Plugins auditados; sin fuentes nulled; escaneo limpio.
- **Ref:** design §9.2 · **Estado:** ☐

### O2-SEC-1 · GATE de compliance (SFC 007 / Habeas Data)
- **Responsable:** SEC (decide) · WPENG (implementa)
- **Prerrequisitos:** O2-WP-1; integración con CRM disponible.
- **Descripción:** Verificar que los leads se envían por webhook al CRM y **no** se almacena PII en `wp_postmeta`; cifrado y masking donde aplique.
- **Entregable:** Evidencia de que no hay PII en texto plano en BD.
- **Criterio de aceptación:** **Gate:** sin PII en BD, o no se lanza a Prod.
- **Ref:** design §10, gate §16 · **Estado:** ☐ · **Nota:** bloqueante para el cutover de SB.

### O2-PROMO-1 · Habilitar promoción para Seguros Bolívar
- **Responsable:** WPENG + DEVOPS
- **Prerrequisitos:** O2-WP-1; O2-SEC-1 superado.
- **Descripción / Entregable / Criterio:** Igual patrón que O1-PROMO-1.
- **Ref:** RF-02 · **Estado:** ☐

### O2-MIG-1 · Migrar contenido de Seguros Bolívar
- **Responsable:** ENLACE + WPENG · con MKT de SB
- **Prerrequisitos:** O2-WP-1; inventario (mayor volumen); mapa de redirects/SEO histórico.
- **Descripción:** Migrar contenido cuidando el SEO (es la marca con más tráfico y presencia).
- **Entregable:** Contenido migrado + redirects.
- **Criterio de aceptación:** Sin pérdida de posicionamiento; MKT valida.
- **Ref:** Q6, PRD §10 · **Estado:** ☐

### O2-OPS-1 · Capacitación + cutover Seguros Bolívar
- **Responsable:** ENLACE + LID
- **Prerrequisitos:** O2-MIG-1; O2-SEC-1.
- **Descripción:** Capacitar editores y ejecutar cutover progresivo.
- **Entregable:** SB en la nueva plataforma.
- **Criterio de aceptación:** Sin incidentes; SLO cumplidos.
- **Ref:** PRD §10 · **Estado:** ☐

---

# OLA 3+ — Escala por demanda

> Prerrequisito global: **Ola 2 completada**.

### O3-OPS-1 · Onboarding autoservicio
- **Responsable:** LID + DEVOPS
- **Prerrequisitos:** Módulo IaC de tenant maduro (O0-INFRA-3) probado en 3 marcas.
- **Descripción:** Formalizar el proceso de alta de marca como servicio repetible/parametrizado, con checklist y tiempos.
- **Entregable:** Runbook de onboarding + plantilla.
- **Criterio de aceptación:** Una marca nueva se da de alta en el tiempo objetivo (KPI a definir).
- **Ref:** RF-09, design §9 · **Estado:** ☐

### O3-INFRA-1 · Onboarding de marcas adicionales
- **Responsable:** DEVOPS + ENLACE
- **Prerrequisitos:** O3-OPS-1; solicitud de la marca; CeCo asignado.
- **Descripción:** Incorporar El Libertador, Jelpit u otras según demanda.
- **Entregable:** Tenant por marca.
- **Criterio de aceptación:** Onboarding sin intervención excepcional.
- **Ref:** PRD §4 · **Estado:** ☐

### O3-GOB-1 · Revisar modelo de licencias (ELA)
- **Responsable:** LID + FIN
- **Prerrequisitos:** Portafolio ≥ N marcas; catálogo de plugins licenciados.
- **Descripción:** Negociar ELA multimarca para plugins licenciados y evitar la "explosión de licencias".
- **Entregable:** Acuerdos de licencia optimizados.
- **Criterio de aceptación:** Costo de licencias por marca decreciente.
- **Ref:** PRD §9, R4 · **Estado:** ☐

### O3-INFRA-2 · Evaluar Headless-ready
- **Responsable:** ARQ + DEVOPS
- **Prerrequisitos:** Marca con exigencias de rendimiento/SEO que lo justifique.
- **Descripción:** Evaluar front-end desacoplado (Next.js) consumiendo la API de la plataforma, sin reestructurar la base.
- **Entregable:** Estudio de viabilidad Headless por marca.
- **Criterio de aceptación:** Decisión informada por caso de negocio.
- **Ref:** design §4 (alt A) · **Estado:** ☐

### O3-INFRA-3 · Optimización de costos
- **Responsable:** DEVOPS + FIN
- **Prerrequisitos:** ≥ 3 meses de datos de facturación real.
- **Descripción:** Aplicar Compute Savings Plans y VPC endpoints (reducir NAT), según §5.2.4.
- **Entregable:** Plan de optimización aplicado.
- **Criterio de aceptación:** Reducción medible de costo sin afectar SLO.
- **Ref:** design §5.2.4 · **Estado:** ☐

---

## Mapa de trazabilidad (resumen)

| Requisito / Decisión / Pregunta | Tareas |
|---|---|
| RF-01 (aislamiento + BD por marca) | O0-INFRA-3, O1-INFRA-2/3/5, O2-INFRA-2 |
| RF-02 (promoción de contenido) | O0-PROMO-1..6, O1-PROMO-1/2, O2-PROMO-1 |
| RF-03 (persistencia de plugins) | O0-WP-1/2/3 |
| RF-09 (onboarding repetible) | O0-INFRA-3, O3-OPS-1 |
| RNF-02/05 (seguridad, observabilidad) | O0-SEC-1/2, O1-OBS-1, O1-SEC-3, O2-SEC-1 |
| Equipo dedicado (PRD §8) | O0-OPS-1..4 |
| D1 motor BD | O0-GOB-2 · D2 persistencia | O0-WP-3 · D3 botón | O0-PROMO-5 |
| D4 pipeline | O0-PROMO-6 · D5 SSO | O0-GOB-4 · D6 Redis | O1-INFRA-3 |
| D7 SLO | O0-GOB-3 · D8 anti-bypass | O0-SEC-1 |
| Q1 | O0-GOB-1 · Q2 | O0-PROMO-4 · Q3 | O0-GOB-2 · Q5 | O0-GOB-4 |
| Q6 | O1-MIG-1/O2-MIG-1 · Q7 | O0-GOB-3 · Q8 | O0-GOB-5 · Q9 | O0-OPS-1/2 |

---

## Gates de control (no avanzar sin superarlos)

| Gate | Tarea | Regla |
|---|---|---|
| Funcional (promoción) | O0-PROMO-4 | Sin corrupción de IDs/serialización/Gutenberg, o se replantea |
| Compliance (SFC/Habeas Data) | O2-SEC-1 | Sin PII en texto plano en BD, o no se lanza a Prod |
| Rendimiento CI/CD | O1-SEC-3 | Fast-track mitiga dentro de la ventana de explotación |
| Financiero (continuo) | O3-INFRA-3 y revisión | TCO (infra §5.2 + equipo §8) vs SaaS; si se equipara, reconsiderar |

---

*Plan de implementación detallado en borrador. Los responsables están por rol (el equipo se conforma en O0-OPS-1/2, PRD Q9). Las estimaciones de tiempo por tarea se añaden al iniciar cada ola, cuando el equipo y los SLO estén definidos. La Ola 0 es un gate: no se construyen tenants hasta cerrarla.*
