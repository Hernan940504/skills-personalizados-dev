# Requirements — Skill `obsidian-manager`

| Campo | Valor |
|---|---|
| Producto | Skill reutilizable para operar un vault de Obsidian como *second brain* |
| Ubicación skill | `skills/workspace/obsidian-manager/` |
| Categoría | `workspace` |
| Runtime | Python 3.12+ (solo stdlib; sin dependencias externas) |
| Estado | En diseño — pendiente de aprobación antes de implementar |
| Clasificación | Interno (entorno financiero regulado) |

## Objetivo

Permitir que un agente (Kiro) construya y mantenga un **second brain** en un vault local de
Obsidian: crear y actualizar notas Markdown con frontmatter YAML, tags y wikilinks; buscar por
texto/tag/link; navegar backlinks y notas huérfanas; **ingerir** archivos externos (p. ej. los
descargados con `google-drive-manager`) como notas; registrar el **día a día** (daily note),
**pendientes/tareas** y **contexto de proyectos**. Todo vía un CLI Python con salida JSON
parseable y controles de seguridad para entorno regulado.

Este skill es la **capa de conocimiento** del second brain. La orquestación con otras
capacidades del repo (Drive, Sheets, Langfuse, etc.) se resuelve por composición, no por
acoplamiento: ver Historia 9 y `design.md` §Orquestación.

## Glosario

- **Vault**: carpeta raíz del second brain de Obsidian (conjunto de archivos `.md` + adjuntos).
- **Nota**: archivo `.md` con frontmatter YAML opcional y cuerpo Markdown.
- **Frontmatter**: bloque YAML entre `---` al inicio de la nota (tags, aliases, fechas, campos propios).
- **Wikilink**: enlace interno de Obsidian con la forma `[[Nombre de nota]]` o `[[nota|alias]]`.
- **Backlink**: nota que enlaza (vía wikilink) a una nota dada.
- **Nota huérfana**: nota sin backlinks entrantes y sin wikilinks salientes.
- **Daily note**: nota diaria con nombre `YYYY-MM-DD` para capturar el trabajo del día.
- **Ingesta**: convertir un archivo/texto externo ya presente en disco en una nota del vault.
- **Fuente**: una capacidad del repo (otro skill) registrada como origen de material para el brain.
- **Operación destructiva/masiva**: sobrescribir el cuerpo de una nota existente, enviar notas a
  la papelera del vault (`.trash/`), o cualquier operación por lote sobre más de 10 notas.

## Convención EARS

- **Ubicuo**: "El sistema DEBE …"
- **Evento**: "CUANDO <evento>, el sistema DEBE …"
- **Estado**: "MIENTRAS <estado>, el sistema DEBE …"
- **Condicional**: "SI <condición>, ENTONCES el sistema DEBE …"
- **Opcional**: "DONDE <feature>, el sistema DEBE …"

---

## Historia 1 — Inicializar y resolver el vault

**Como** usuario, **quiero** inicializar un vault de second brain y que el skill lo resuelva desde una ruta configurable, **para** empezar sin tener un vault previo.

- 1.1 CUANDO se ejecute `init [ruta]`, el sistema DEBE crear la estructura base del vault: carpetas `inbox/`, `proyectos/`, `daily/`, `referencias/`, `plantillas/`, `.trash/`, y un `index.md` raíz.
- 1.2 SI la ruta destino ya contiene un vault (existe `.obsidian/` o `index.md`), ENTONCES el sistema DEBE no sobrescribir y reportar que ya está inicializado (salida idempotente, código 0).
- 1.3 El sistema DEBE resolver la ruta del vault desde `OBSIDIAN_VAULT_PATH`, con default fuera del repo (`~/second-brain`).
- 1.4 SI una operación distinta de `init` se ejecuta y el vault no existe, ENTONCES el sistema DEBE fallar con código de no encontrado e instruir ejecutar `init`.
- 1.5 El sistema DEBE crear una carpeta `.obsidian/` mínima para que Obsidian reconozca el vault, sin sobrescribir configuración existente del usuario.

## Historia 2 — Crear y actualizar notas

**Como** agente, **quiero** crear y actualizar notas con frontmatter, tags y wikilinks, **para** capturar conocimiento estructurado.

- 2.1 CUANDO se ejecute `note create`, el sistema DEBE crear un `.md` con frontmatter YAML (título, fecha de creación, tags, aliases) y cuerpo, en la carpeta indicada (default `inbox/`).
- 2.2 El sistema DEBE derivar un nombre de archivo seguro (slug) desde el título, evitando colisiones de nombres.
- 2.3 SI ya existe una nota con el mismo nombre destino, ENTONCES el sistema DEBE detenerse y ofrecer estrategia: `new` (sufijo), `skip` o `overwrite`; `overwrite` es destructivo y requiere confirmación.
- 2.4 CUANDO se ejecute `note append`, el sistema DEBE añadir contenido al final del cuerpo sin tocar el frontmatter (operación no destructiva).
- 2.5 CUANDO se ejecute `note update --frontmatter`, el sistema DEBE fusionar/actualizar campos del frontmatter conservando el cuerpo.
- 2.6 CUANDO se ejecute `note update --body` (reemplazo de cuerpo), por ser destructivo el sistema DEBE requerir `--yes` o `--dry-run`.
- 2.7 El sistema DEBE preservar el frontmatter YAML válido al reescribir (round-trip sin perder campos ni orden significativo).

## Historia 3 — Buscar y listar

**Como** agente, **quiero** buscar notas por texto, tag, carpeta o link, **para** localizar conocimiento antes de operarlo.

- 3.1 CUANDO se ejecute `search --text`, el sistema DEBE buscar coincidencias en el cuerpo y/o frontmatter y devolver ruta, título y fragmento de contexto.
- 3.2 CUANDO se ejecute `search --tag`, el sistema DEBE devolver las notas que tengan ese tag (en frontmatter `tags:` o inline `#tag`).
- 3.3 CUANDO se ejecute `search --links-to <nota>`, el sistema DEBE devolver las notas que enlazan a esa nota (backlinks).
- 3.4 El sistema DEBE permitir acotar por carpeta (`--folder`) y limitar resultados (`--limit`, default 200, marcando `truncated` si hay más).
- 3.5 SI un filtro produce cero resultados, ENTONCES el sistema DEBE devolver lista vacía con código 0 (no es error).

## Historia 4 — Grafo: backlinks y huérfanas

**Como** agente, **quiero** navegar la estructura de enlaces del vault, **para** mantener el brain conectado y detectar conocimiento aislado.

- 4.1 CUANDO se ejecute `graph backlinks <nota>`, el sistema DEBE listar las notas que enlazan a ella.
- 4.2 CUANDO se ejecute `graph orphans`, el sistema DEBE listar notas sin backlinks entrantes ni wikilinks salientes.
- 4.3 CUANDO se ejecute `graph outlinks <nota>`, el sistema DEBE listar los wikilinks salientes, distinguiendo los que apuntan a notas inexistentes (enlaces rotos).
- 4.4 El sistema DEBE resolver wikilinks por nombre de nota y por alias declarado en frontmatter.

## Historia 5 — Ingesta de material externo

**Como** agente, **quiero** ingerir archivos/texto ya presentes en disco como notas del vault, **para** alimentar el brain con material de otras fuentes sin acoplarme a ellas.

- 5.1 CUANDO se ejecute `ingest <ruta-local>`, el sistema DEBE crear una nota a partir del archivo, con frontmatter que registre origen (`source`), fecha de ingesta y tags indicados.
- 5.2 El sistema DEBE aceptar texto por stdin (`ingest -`) para material que no está en un archivo.
- 5.3 CUANDO el archivo sea Markdown, el sistema DEBE preservar su contenido y fusionar (no duplicar) frontmatter existente con el generado.
- 5.4 CUANDO el archivo NO sea texto (p. ej. PDF/imagen), el sistema DEBE copiarlo a `referencias/adjuntos/` y crear una nota-índice que lo enlace, sin intentar parsear binario.
- 5.5 El sistema DEBE permitir asignar la nota a un proyecto (`--project`) y añadir wikilinks a notas de contexto indicadas (`--link`).
- 5.6 DONDE se indique `--dry-run`, el sistema DEBE reportar qué nota crearía y dónde SIN escribir.

## Historia 6 — Daily note (día a día)

**Como** usuario, **quiero** registrar el trabajo del día en una nota diaria, **para** capturar el flujo de trabajo del repo de forma continua.

- 6.1 CUANDO se ejecute `daily`, el sistema DEBE crear o abrir la nota `daily/YYYY-MM-DD.md` con secciones base (Trabajado, Pendientes, Notas), sin sobrescribir contenido existente.
- 6.2 CUANDO se ejecute `daily --add "<texto>"`, el sistema DEBE añadir una entrada con timestamp a la sección "Trabajado" del día actual.
- 6.3 El sistema DEBE permitir asociar la entrada a un proyecto (`--project`) generando el wikilink correspondiente.
- 6.4 El sistema DEBE usar la fecha actual del sistema y aceptar `--date YYYY-MM-DD` para registrar en otro día.

## Historia 7 — Pendientes / tareas

**Como** usuario, **quiero** gestionar pendientes en el vault, **para** que el second brain sea también la fuente de qué falta por hacer.

- 7.1 CUANDO se ejecute `task add "<texto>"`, el sistema DEBE registrar una tarea como checkbox Markdown (`- [ ]`) en la nota de pendientes del proyecto indicado o en una nota global `pendientes.md`.
- 7.2 CUANDO se ejecute `task list`, el sistema DEBE recolectar y devolver todas las tareas abiertas (`- [ ]`) del vault, con su nota origen y proyecto.
- 7.3 CUANDO se ejecute `task done "<texto>"` (o por índice), el sistema DEBE marcar la tarea como completada (`- [x]`) conservando el texto.
- 7.4 El sistema DEBE permitir filtrar tareas por proyecto (`--project`) y por estado (abiertas/cerradas).

## Historia 8 — Contexto de proyectos

**Como** usuario, **quiero** una nota de contexto por proyecto, **para** consolidar decisiones, enlaces y estado de cada iniciativa (alineado con `lineas_negocio/`).

- 8.1 CUANDO se ejecute `project create <nombre>`, el sistema DEBE crear `proyectos/<slug>/_contexto.md` con frontmatter (nombre, estado, tags) y secciones (Resumen, Decisiones, Enlaces, Pendientes).
- 8.2 CUANDO se ejecute `project note <nombre> --add "<texto>"`, el sistema DEBE añadir una entrada fechada a la sección indicada del contexto del proyecto.
- 8.3 CUANDO se ejecute `project list`, el sistema DEBE listar los proyectos con su estado leído del frontmatter.
- 8.4 El sistema DEBE enlazar automáticamente (wikilink) las notas ingeridas/creadas con `--project` a la nota de contexto del proyecto.

## Historia 9 — Orquestación de fuentes (composición de skills)

**Como** usuario, **quiero** que "cada skill nuevo del repo sea una nueva capacidad del brain", **para** alimentarlo sin reescribir este skill cada vez.

- 9.1 El sistema DEBE mantener un registro de fuentes (`fuentes.json`/`config`) donde cada fuente declara: nombre, skill invocado, comando y cómo mapear su salida a `ingest`.
- 9.2 CUANDO se ejecute `sources list`, el sistema DEBE listar las fuentes registradas y su estado (declarada, no verificada).
- 9.3 CUANDO se ejecute `sources sync <fuente>` (orquestación), el sistema DEBE invocar el CLI del skill fuente por su ruta, tomar su salida y pasarla a `ingest`, con `--dry-run` disponible.
- 9.4 El sistema NO DEBE codificar conocimiento específico de cada skill fuente en su lógica central: el mapeo vive en el registro de fuentes (desacoplamiento por configuración).
- 9.5 SI el skill fuente no existe o falla, ENTONCES el sistema DEBE reportar el error de esa fuente sin corromper el vault (fallo aislado por fuente).

> **Decisión de diseño (ver `design.md`):** la capa de ingesta (`ingest`) es agnóstica del origen.
> La orquestación (`sources sync`) es un adaptador delgado guiado por configuración. El agente
> (Kiro) también puede encadenar skills manualmente sin pasar por `sources`.

---

## Requisitos no funcionales

### RNF-1 Sin dependencias externas
- El sistema DEBE implementarse solo con la biblioteca estándar de Python 3.12+ (parseo de
  frontmatter YAML propio o mínimo, sin paquetes de terceros), para no añadir dependencias que
  requieran mirror JFrog ni auditoría de supply chain. SI en el futuro se requiere una dependencia,
  DEBE pinnearse exacta y documentarse.

### RNF-2 Salida e interfaz
- Toda salida del CLI DEBE ser JSON por defecto; `--pretty` produce salida legible.
- Los flags globales (`--pretty`, `--dry-run`, `--yes`, `--log-level`) DEBEN aceptarse antes o
  después del subcomando.
- El sistema DEBE usar códigos de salida definidos: `0` éxito; `2` uso/argumentos; `3` permisos
  (p. ej. vault de solo lectura); `4` no encontrado (vault o nota); `6` conflicto o confirmación
  requerida.

### RNF-3 Seguridad (entorno regulado)
- El sistema NUNCA DEBE escribir fuera del vault resuelto: toda ruta destino DEBE canonicalizarse
  (`realpath`) y validarse que queda dentro del vault (prevención de path traversal).
- El sistema DEBE rechazar rutas con `..` o absolutas que escapen del vault.
- El contenido del vault es del usuario: el sistema NO DEBE registrar en logs el cuerpo de las
  notas ni datos personales; solo rutas y metadatos no sensibles.
- Sin secretos hardcodeados. Sin telemetría externa. Sin llamadas de red (operación 100% local).
- El sistema NUNCA DEBE implementar borrado permanente: solo mover a `.trash/` del vault (reversible).
- Confirmación explícita (`--yes`) o `--dry-run` en toda operación destructiva o masiva.

### RNF-4 Integridad del vault
- El round-trip de frontmatter DEBE preservar los campos y valores válidos existentes.
- El sistema DEBE escribir de forma atómica (archivo temporal + `os.replace`) para no dejar notas a medias ante fallo.
- El sistema DEBE normalizar saltos de línea y encoding UTF-8.

### RNF-5 Testing
- Los tests DEBEN ejecutarse sin red y sobre un vault temporal (`tmp_path`), sin tocar el vault real del usuario.
- Cobertura mínima sobre la lógica: parseo/serialización de frontmatter, slug/colisiones, resolución
  de wikilinks y backlinks, detección de huérfanas, ingesta (texto/binario), validación de path traversal.

---

## Criterios de aceptación globales

- [ ] `init` crea un vault válido reconocible por Obsidian y es idempotente.
- [ ] Se puede crear una nota, ingerir un `.md` descargado de Drive y verlo enlazado a un proyecto.
- [ ] `daily --add` y `task add`/`task list`/`task done` funcionan de punta a punta sobre un vault temporal.
- [ ] `graph orphans` y `graph backlinks` reflejan correctamente los wikilinks del vault.
- [ ] `sources sync` invoca un skill fuente (mockeado en test) y crea notas por composición, sin lógica específica del skill en el núcleo.
- [ ] Ninguna operación escribe fuera del vault (test de path traversal).
- [ ] No existe ninguna ruta de código que borre archivos de forma permanente.
- [ ] La salida por defecto es JSON parseable; `--pretty` produce salida humana.
- [ ] Los tests pasan sin dependencias externas ni red.
