# Requerimientos — gmail-manager

## Introducción

`gmail-manager` es un skill de línea de comandos (Python 3.12+, solo con las librerías cliente de
Google ya usadas por otros skills del repo) que lee de **solo lectura** el correo corporativo de
Gmail y extrae **contexto de negocio por línea de negocio** para alimentar el second brain
(`obsidian-manager`). No envía, borra ni modifica correos. Está diseñado para ejecutarse de forma
periódica (cron/launchd cada 6 h) con **bajo consumo en reposo** (no hay proceso residente: el
script corre, hace su trabajo y termina).

El correo está segmentado por etiquetas jerárquicas `Tribu Servicios Bolivar/<Línea>`:
`Ciencuadras`, `Libertador`, `Proyectiva`, `Notificador`, `RC` (Relacionamiento Contextual).

## Requerimiento 1 — Autenticación OAuth de solo lectura

**Historia:** como usuario, quiero autenticarme una vez con mi cuenta de Google y que el skill
reutilice el token, para no re-autorizar en cada ejecución.

Criterios (EARS):
- CUANDO no exista token válido, el sistema DEBERÁ ejecutar el flujo OAuth installed-app con el
  scope `https://www.googleapis.com/auth/gmail.readonly` y persistir el token con permisos `0600`.
- CUANDO el token esté expirado pero tenga refresh_token, el sistema DEBERÁ renovarlo sin
  intervención del usuario.
- El sistema DEBERÁ almacenar credenciales y token **fuera del repo** (`~/.config/gmail-skill/`),
  con rutas overridables por variables de entorno, y NUNCA versionarlos.
- El sistema NUNCA DEBERÁ registrar en logs el contenido de tokens ni credenciales.
- El scope DEBERÁ ser exclusivamente de solo lectura; el skill no implementa envío ni modificación.

## Requerimiento 2 — Descubrimiento y filtrado por etiqueta de línea de negocio

**Historia:** como usuario, quiero que solo se procesen los correos de mis líneas de negocio, no
todo el buzón (183k mensajes), para acotar ruido y volumen.

Criterios:
- El sistema DEBERÁ listar las etiquetas y operar únicamente sobre las hijas de
  `Tribu Servicios Bolivar/` (configurable).
- El sistema DEBERÁ mapear cada etiqueta a un proyecto/carpeta y tag del vault:
  Ciencuadras→ciencuadras, Libertador→libertador, Proyectiva→proyectiva,
  Notificador→notificador-transversal, RC→relacionamiento-contextual.
- CUANDO una etiqueta configurada no exista en la cuenta, el sistema DEBERÁ reportarlo y continuar
  con las demás (no fallar todo).

## Requerimiento 3 — Barrido inicial (12 meses) e incremental

**Historia:** como usuario, quiero un primer barrido de los últimos 12 meses y luego ejecuciones
incrementales que solo lean lo nuevo desde la última corrida.

Criterios:
- En la primera ejecución, el sistema DEBERÁ consultar mensajes con `after:` = hoy − 12 meses.
- El sistema DEBERÁ persistir un **estado** (`~/.config/gmail-skill/state.json`) con la marca de
  tiempo (epoch) de la última ejecución exitosa por etiqueta.
- En ejecuciones siguientes, el sistema DEBERÁ consultar solo mensajes con `after:` = última
  ejecución (menos un pequeño solape de seguridad), e ignorar lo ya procesado (por `messageId`).
- El sistema DEBERÁ ser idempotente: reprocesar un mensaje ya indexado NO DEBERÁ duplicar notas.

## Requerimiento 4 — Clasificación por criticidad e indexación selectiva

**Historia:** como usuario, quiero que solo se indexe lo valioso, clasificado por criticidad, sin
volcar el cuerpo completo de los correos.

Criterios:
- El sistema DEBERÁ clasificar cada correo en **alta / media / baja**:
  - **Alta** (se indexa como nota en `proyectos/<línea>/`): decisiones de arquitectura, incidentes/
    outages, cambios de infra, accesos (documentados por referencia, sin el valor), acuerdos,
    fechas límite, y **correos donde se menciona al usuario dejándole un compromiso/acción**.
  - **Media** (se resume como entrada en la bitácora/contexto del proyecto): actualizaciones de
    estado y coordinaciones relevantes.
  - **Baja** (se ignora): newsletters, notificaciones automáticas rutinarias (Jira/Datadog),
    promociones, social.
- El sistema NUNCA DEBERÁ indexar contraseñas, tokens, llaves ni PII sensible; si un correo los
  contiene, DEBERÁ documentarlos por referencia/enmascarados, nunca el valor.
- La nota de un correo de criticidad alta DEBERÁ contener: asunto, remitente, fecha, línea de
  negocio, un resumen (no el cuerpo completo), el compromiso detectado (si aplica) y un enlace al
  hilo en Gmail; con tags de la línea de negocio + `correo`.
- El sistema DEBERÁ escribir vía `obsidian-manager` (ingest/note) para heredar frontmatter, tags
  canónicos y wikilinks.

## Requerimiento 5 — Bajo consumo y operación periódica

**Historia:** como usuario, quiero que el skill no consuma memoria en reposo y corra cada 6 h.

Criterios:
- El sistema NO DEBERÁ dejar procesos residentes; cada corrida es un proceso que termina.
- El sistema DEBERÁ paginar la API y procesar en lotes acotados para no cargar todo en memoria.
- El sistema DEBERÁ proveer instrucciones/artefacto para programarlo cada 6 h (cron o launchd).
- El sistema DEBERÁ devolver salida JSON por stdout (resumen: por etiqueta, cuántos leídos,
  cuántos indexados alta/media, cuántos ignorados) y soportar `--dry-run`.

## Requerimiento 6 — Seguridad y cumplimiento

Criterios:
- Solo lectura; sin borrado permanente ni modificación.
- Sin secretos hardcodeados; credenciales por env/config fuera del repo.
- `credentials.json`, `token.json`, `state.json` en `.gitignore`.
- No imprimir cuerpos de correos ni PII en logs ni en la conversación.
