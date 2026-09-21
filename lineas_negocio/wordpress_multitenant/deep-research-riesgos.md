# Deep Research — Crítica / Riesgos

> Tipo: Deep research de **crítica / riesgos** (alimenta Inception y gates: §6, §7, §8, §9 del PRD).
> Fuente: "Evaluación Arquitectónica y Análisis de Riesgos Estructurales: Plataforma WordPress Multitenant Centralizada".
> Estado: EJECUTADO. Transcripción a Markdown del informe original para lectura y generación de artefactos.
> Documento relacionado: `PRD-wordpress-multitenant-grupo-bolivar.md`.

---

## Resumen ejecutivo

La iniciativa fuerza un CMS heredado y dependiente del estado (WordPress) dentro de un paradigma de infraestructura inmutable y nativa de la nube (ECS Fargate, imágenes horneadas en CI/CD, media a S3). A pesar de la intención de reducir deuda técnica y unificar operación, existen **fricciones fundamentales** entre el diseño de WordPress y las expectativas operativas del modelo.

### Riesgos más severos (Probabilidad × Impacto)

1. **Corrupción estructural de datos en la promoción automatizada** (Prob: Muy Alta · Impacto: Muy Alto). La migración automatizada Stage → Prod choca con el diseño monolítico de la BD de WordPress: persistencia unificada de configuración/contenido/metadatos, datos serializados en PHP y JSON anidado (Gutenberg) → colisión de IDs autoincrementales y destrucción silenciosa de configuraciones.
2. **Explotación "Negative-Day" y ataques de cadena de suministro** (Prob: Alta · Impacto: Crítico). 11,334 vulnerabilidades nuevas en el último año, 91% en componentes de terceros; tiempo medio a explotación masiva ~5 horas; 46% sin parche al divulgarse. Composer en CI/CD abre vectores de cadena de suministro (incidente "Mini Shai-Hulud") con exfiltración de credenciales AWS.
3. **Fricción operativa del paradigma inmutable** (Prob: Muy Alta · Impacto: Alto). Hornear plugins en imagen resuelve la volatilidad de reinicios pero destruye la agilidad: cada actualización urgente exige ciclo completo de build/escaneo/deploy. Un equipo reducido no sostiene decenas de instancias → parálisis del time-to-market.
4. **Incumplimiento regulatorio SFC y Habeas Data** (Prob: Media · Impacto: Muy Alto). WordPress almacena datos de leads en texto plano; sin cifrado a nivel de aplicación se incumple la Circular Externa 007 de la SFC y la Ley 1581 de 2012.

---

## 1. Antipatrones y causas raíz en la centralización de WordPress

WordPress fue concebido para hosting compartido con sistema de archivos de lectura/escritura persistente, BD integrada de baja latencia y extensibilidad dinámica. Forzarlo a microservicios inmutables genera resistencia operativa severa.

- **Antipatrón "WordPress inmutable/stateless":** decenas de plugins empresariales (SEO, seguridad, rendimiento, caché, minificación CSS/JS, logs) exigen **escritura local constante**. Con sistema de archivos de solo lectura/efímero, fallan silenciosamente, consumen recursos regenerando activos o colapsan la capa de presentación.
- **Antipatrón "ilusión del plano de control unificado":** para estandarizar, el equipo suele construir una **"fat image"** con todos los plugins y activarlos por BD. Esto infla la superficie de ataque: una vulnerabilidad en un plugin de la marca A expone a la marca B (LFI, ejecuciones colaterales) porque el código vulnerable reside en el disco inmutable compartido **aunque el plugin esté inactivo**.

### Estrategias de mitigación

| Riesgo estructural | Causa raíz de arquitectura | Estrategia de mitigación |
|---|---|---|
| Incompatibilidad de plugins por sistema de archivos efímero | El ecosistema asume persistencia de disco para cachés, compilación de activos y logs | Montar **EFS** en rutas restrictivas y específicas (p. ej. `/wp-content/cache`), con control estricto de ejecución PHP en esos directorios |
| Expansión injustificada de superficie de ataque (fat images) | Horneado monolítico de todos los plugins en una imagen base | **Multi-stage builds** dinámicos → imágenes derivadas (child images) por inquilino con solo los binarios requeridos por la línea |
| Desvío del estándar corporativo de BD | MySQL/MariaDB exigido por WP vs estándar PostgreSQL | Someter y documentar una **excepción técnica formal (waiver)**; delegar administración a **AWS Aurora MySQL Serverless** |

> Nota: este informe de riesgos sugiere EFS en rutas acotadas para plugins que exigen escritura; el informe de validación recomienda hornear plugins en imagen inmutable + media offload a S3. La decisión definitiva (imagen inmutable pura vs híbrido con EFS acotado para cachés) debe cerrarse en la **PoC** — es un punto abierto del PRD.

---

## 2. Riesgos de adopción y operación

Las líneas (Ciencuadras, Proyectiva, Seguros Bolívar) operan hoy con alta autonomía técnica (análisis de mercado, píxeles de conversión, flujos en tiempo real). La centralización altera esa dinámica.

- **Expectativas desalineadas sobre la automatización de contenido:** marketing/UX asumen un comportamiento tipo Headless CMS (contenido como flujo de datos desacoplado). En la realidad de WordPress, contenido + configuración + opciones de plugins + metadatos convergen en las mismas tablas. La automatización total obligaría a clonaciones parciales/totales de BD que **sobrescribirían registros de producción** (transacciones, leads, perfiles creados durante la validación de Stage). Al enfrentar pérdidas de datos o intervención técnica constante, la adopción fracasa.
- **Cuello de botella del equipo central:** con inmutabilidad, hasta instalar un simple tracking pixel exige revisión → Composer/JFrog → build → deploy. Lo que tomaba 10 minutos entra a una cola de días. Esto incentiva **Shadow IT** (las líneas contratan plataformas externas de landing pages), anulando la consolidación.

### Estrategias de mitigación

| Riesgo de adopción | Causa raíz operacional | Estrategia de mitigación |
|---|---|---|
| Rechazo del área usuaria a la sincronización de contenido | La promoción automatizada genera pérdida de datos transaccionales y exige validación manual | Abandonar el objetivo de "promoción automática 100%". Configurar flujos de export/import asistidos a nivel de entidad vía API REST, limitando la promoción a entradas y bloques aislados |
| Colapso operativo del equipo WPMT | Dependencia exclusiva de un equipo central pequeño para compilar/desplegar ante cada necesidad | Canal de aprobación acelerada (**fast-track**) automatizado por DevSecOps: despliegue automático de un catálogo de plugins preauditados en < 30 min |
| Aparición de Shadow IT | Percepción de burocracia frente a la incapacidad de iterar rápido en entornos inmutables | Desacoplar analítica/marketing de la infraestructura WP con un **Tag Manager empresarial** controlado por mercadeo de forma independiente |

---

## 3. Riesgos técnicos y de deuda arquitectónica

- **Corrupción por serialización de PHP:** `wp_options` guarda configuración con serialización que codifica la **longitud exacta en bytes** (p. ej. `a:1:{s:24:"stage.segurosbolivar.com";}`). El search-replace de dominios/rutas sin recalcular el índice hace fallar `unserialize()` → pantallas blancas o pérdida total de diseño.
- **Colisión de IDs autoincrementales:** cada entidad depende de un `post_id` secuencial único. El desarrollo concurrente asegura colisiones (la página con ID 1050 en Stage choca con un registro que ya reclamó el 1050 en Prod). Los scripts no pueden resolverlo sin reconstruir recursivamente la jerarquía de metadatos.
- **Fragilidad de Gutenberg:** la estructura visual se guarda en `post_content` como JSON en comentarios HTML con **referencias rígidas a IDs de medios** (`<!-- wp:image {"id":142} -->`). Al promover, si la imagen no existe bajo el ID 142 en destino, el componente se rompe. Fallas de sanitización de este JSON han originado XSS y corrupción de BD.
- **Obsolescencia del ecosistema PHP:** obliga a mantener clústeres MySQL/MariaDB. La tabla `wp_options` (transients/sesiones) genera cuellos de botella de lectura/escritura que degradan la BD, forzando subsistemas de caché en memoria (Redis) a mantener perpetuamente.

### Estrategias de mitigación

| Riesgo técnico | Causa raíz de infraestructura | Estrategia de mitigación |
|---|---|---|
| Corrupción fatal de PHP durante el despliegue | Manipulación asimétrica de cadenas serializadas al reemplazar URLs sin recalcular longitudes (bytes) | Prohibir modificaciones directas a la BD vía SQL. Obligar herramientas que interpreten PHP (`wp-cli search-replace` con banderas especializadas) como único método autorizado de inyección |
| Colisión de IDs y enlaces rotos de medios en Gutenberg | El JSON anidado en `post_content` vincula estáticamente componentes a IDs no consistentes entre BD | Middlewares de pre-procesamiento (Node.js/Python) en el plano de control que analicen el JSON, concilien IDs de medios en Producción y reescriban los bloques antes de insertar |
| Degradación de BD por saturación de opciones | Diseño legado que usa `wp_options` (transaccional) para estado temporal, ahogando conexiones MySQL | Implementar de forma nativa y obligatoria **Amazon ElastiCache (Redis)** para sacar la presión transitoria fuera del disco |

---

## 4. Riesgos de datos y compliance regulatorio

El Grupo Bolívar opera en sector altamente regulado. Aplican la **Circular Externa 007 de 2018**, la **Circular Externa 029 de 2014** de la SFC y la **Ley 1581 de 2012 (Habeas Data)**.

- **Superficie de ataque:** 11,334 vulnerabilidades nuevas (+42% interanual); 91% en plugins de terceros; tiempo medio a explotación ~5 horas; 46% "Negative-Day" (sin parche al divulgarse). Las de omisión de autenticación son el 57% de los casos. El pipeline inmutable (identificar → esperar parche → modificar dependencias → build → escanear → desplegar) **no compite** con la ventana de 5 horas.
- **Cadena de suministro:** automatizar plugins con JFrog interactuando con Packagist/Composer expone a incidentes como "Mini Shai-Hulud" (mayo 2026), donde hooks de paquetes secuestrados ejecutan código arbitrario y exfiltran tokens, `.env` y credenciales AWS.
- **PII en texto plano:** los formularios de captura de leads guardan datos en `wp_postmeta` en texto plano, violando las directrices de la SFC sobre protección de datos en reposo. Un SQLi o el compromiso de un contenedor expone nombres, correos y teléfonos.

### Estrategias de mitigación

| Riesgo regulatorio / seguridad | Causa raíz | Estrategia de mitigación |
|---|---|---|
| Exfiltración de PII (Ley 1581 y SFC 007) | Plugins de formularios almacenan datos en texto plano sin cifrado a nivel de BD | **Desacoplar la captación:** integraciones vía Webhook para que los datos transiten directo al CRM corporativo, sin almacenarse en la BD de WordPress |
| Infección por explotación de "Negative-Days" | Imposibilidad del pipeline inmutable de reaccionar a la ventana de 5 horas | **WAF avanzado con "Virtual Patching"** frente al ALB, aislando patrones de ataque en tránsito antes de alcanzar los contenedores |
| Compromiso de AWS vía cadena de suministro | Ejecución de hooks de Composer que extraen secretos ambientales durante el build | Fortalecer JFrog con **cooldown policies** de 72 horas para paquetes nuevos y prohibir ejecución de scripts (`--no-scripts` en Composer) en AWS CodeBuild |

---

## 5. Costos ocultos de operación y licenciamiento

- **Explosión de licencias:** plugins críticos (control de versiones, offload a S3, seguridad) licencian por sitio/dominio. Con multi-instancia aislada, se compran licencias por marca (y por ambiente). 15 herramientas × 10 marcas = **300 licencias** a rastrear y pagar → batallas de CeCo.
- **Infraestructura "zombie":** la coexistencia en paralelo, sumada al miedo a perder SEO / rehacer redirects 301, prolonga el cutover → se financian clústeres redundantes, licencias duplicadas y OPEX dividido por periodos largos.
- **Inviabilidad del equipo reducido:** un equipo de 3-5 ingenieros para soporte transversal + CI/CD + incidentes + versiones colapsa dada la tasa de vulnerabilidades, la resolución manual de conflictos de BD y la absorción de solicitudes de mercadeo.

### Estrategias de mitigación

| Riesgo financiero | Causa raíz operacional | Estrategia de mitigación |
|---|---|---|
| Explosión OPEX por multiplicidad de licencias | Aislamiento estricto obliga a licencias Enterprise repetidas por inquilino | **Acuerdos de Licencia Empresarial (ELA)** multimarca anticipados; asignar CeCo en proporción al tráfico transaccional, no por prorrateo ciego |
| Hemorragia de costos por infraestructura "zombie" | Miedo a la disrupción SEO y a la migración histórica prolonga la coexistencia | **Sunset Windows** no negociables por mandato de la Junta de Gobierno TI; penalizar con sobrecargos a los CeCo rezagados |
| Inviabilidad del modelo de soporte centralizado | Subestimación del esfuerzo (LOE) de gestionar dependencias PHP inmutables a escala | Modelo de **responsabilidades compartidas**: el equipo central gestiona el plano de control (core, infra, seguridad); las líneas financian sus "Administradores Técnicos de Contenido" certificados |

---

## 6. Señales tempranas de alerta (gates del proyecto)

Arquitectura Empresarial, CISO y Finanzas deben establecer gates con criterios de cancelación automáticos. Si el proyecto exhibe alguno de estos comportamientos, se aborta o se pivota (p. ej. a SaaS especializado):

- **Gate funcional (PoC de promoción):** si la migración Stage → Prod produce errores de deserialización PHP, enlaces rotos en el JSON de Gutenberg, o exige desactivar validaciones de BD para forzar contenido → el requerimiento se considera **fallido de origen**.
- **Gate de cumplimiento (SFC/Habeas Data):** si la arquitectura retiene datos de prospectos localmente sin cifrado nativo y no puede delegarlos al CRM → **bloqueo inmediato** del paso a Producción.
- **Gate de rendimiento CI/CD (tiempo de mitigación):** simulacro de zero-day; si compilar + aprobar + escanear en JFrog + desplegar a todas las marcas toma **> 5 horas** → carece de la resiliencia obligatoria.
- **Gate financiero (TCO vs SaaS):** al sumar Fargate dedicado + BD múltiples + almacenamiento elástico + WAF inteligente + carga salarial del equipo, si el TCO **iguala o excede** una plataforma gestionada superior → se asume riesgo innecesario.

---

## Fuentes citadas

Contenido reformulado para cumplimiento de licencias. Referencias del informe original:

1. Repair WordPress Database (BlogVault): https://blogvault.net/repair-wordpress-database/
2. Elementor Claude Skill (Royal Plugins): https://royalplugins.com/skills/elementor-claude-skill/
3. What Does Serialized Data Mean in WordPress (Wbcom): https://wbcomdesigns.com/what-does-serialized-data-mean-in-wordpress/
4. WordPress Security Statistics 2025–2026 (HideMyWPGhost): https://hidemywpghost.com/wordpress-security-statistics-2025-2026-43-verified-data-points/
5. 43 WordPress Security Data Points (dev.to/cifi): https://dev.to/cifi/43-wordpress-security-data-points-that-should-change-how-you-build-sites-in-2026-fjl
6. Best WordPress Security Plugin for the AI Attack Era (Barreras IT): https://barreras-it.com/best-wordpress-security-plugin-ai-threats
7. Mini Shai-Hulud: intercom-php compromise (Cloudsmith): https://cloudsmith.com/blog/mini-shai-hulud-reaches-packagist-the-intercom-intercom-php-compromise-explained
8. HereWeGoAgain incident scanner (GitHub): https://github.com/Dragon-Lady/HereWeGoAgain-incident-scanner
9. `PRD-wordpress-multitenant-grupo-bolivar.md` (documento fundacional)
10. Keeping servers up as a single founder (HN): https://news.ycombinator.com/item?id=21461617
11. Cumplir la Circular 007 de la Superfinanciera (e-dea): https://www.e-dea.co/blog/circular-007-2018
12. Concepto 63895 de 2015 Superfinanciera (RedJurista): https://www.redjurista.com/Documents/concepto_63895_de_2015_superfinanciera_-_superintendencia_financiera.aspx
13. Requerimientos Seguridad y Ciberseguridad CCW (Superfinanciera): https://www.superfinanciera.gov.co/loader.php?lServicio=Tools2&lTipo=descargas&lFuncion=descargar&idFile=1070340
14. Industry Articles (Cubex Group): https://cubexgroup.com/industry-articles/
15. 2025 mid-year WordPress vulnerability report (Patchstack): https://patchstack.com/whitepaper/2025-mid-year-vulnerability-report/
16. Package Manager CWEs (Andrew Nesbitt): https://nesbitt.io/2026/05/04/package-manager-cwes.html
17. Plugin Reviews (wpONcall): https://wponcall.com/category/plugin-reviews/page/3/
18. WP Migrate DB Pro Changelog (Delicious Brains): https://deliciousbrains.com/wp-migrate-db-pro/doc/changelog/
19. Creating a Custom Table with PHP in WordPress (Delicious Brains): https://deliciousbrains.com/creating-custom-table-php-wordpress/
20. PHP Archives (Delicious Brains): https://deliciousbrains.com/tag/php/feed/
21. Releases (Respira for WordPress): https://www.respira.press/releases
22. Vulnerability Summary week of June 15, 2026 (CISA): https://www.cisa.gov/news-events/bulletins/sb26-173
23. Vulnerability Summary week of June 1, 2026 (CISA): https://www.cisa.gov/news-events/bulletins/sb26-159
24. Vulnerability Summary week of July 27, 2026 (CISA): https://www.cisa.gov/news-events/bulletins/sb26-215
25. WordPress Development Tutorial & Engineering Guide: https://helloaihub.vercel.app/guides/wordpress
26. Modules API reference (Valkey): https://valkey.io/topics/modules-api-ref/
27. Migrate WordPress without breaking anything (ServMask): https://blog.servmask.com/how-to-migrate-wordpress-to-a-new-host/
28. Enterprise WordPress Plugin Dependency Management: https://fachremyputra.com/enterprise-wordpress-plugin-dependency-management/
29. WordPress security in the age of negative-day exploits (Wordify): https://wordify.com/blog/wordpress-security-negative-day-exploits/
30. Seguridad en transacciones bancarias (Superfinanciera): https://www.superfinanciera.gov.co/publicaciones/10098531/
31. awesome-software-supply-chain-security (GitHub): https://github.com/bureado/awesome-software-supply-chain-security
32. What's New (Delicious Brains): https://deliciousbrains.com/wp-migrate-db-pro/whats-new/
