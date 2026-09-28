# Requirements — Skill `google-drive-manager`

| Campo | Valor |
|---|---|
| Producto | Skill reutilizable para operar Google Drive (Mi unidad + Shared Drives) |
| Ubicación skill | `skills/workspace/google-drive-manager/` |
| Categoría | `workspace` |
| Runtime | Python 3.12+ |
| Estado | En diseño — pendiente de aprobación antes de implementar |
| Clasificación | Interno (entorno financiero regulado) |

## Objetivo

Permitir que un agente (Kiro) se conecte a Google Drive vía OAuth 2.0 (installed app) y ejecute
operaciones de **descarga, subida, actualización y organización** de archivos, de forma idéntica
en **Mi unidad** y en **unidades compartidas (Shared Drives)**, invocables desde lenguaje natural,
con salida JSON parseable y controles de seguridad para entorno regulado.

## Glosario

- **Shared Drive**: unidad compartida de Google Workspace (antes Team Drive).
- **Ruta legible**: cadena tipo `"Unidad Compartida/Proyectos/2026"` que el CLI resuelve a un `fileId`.
- **Operación destructiva/masiva**: `trash`, reemplazo de contenido, o `move`/`rename` de más de 10 archivos.
- **Export**: conversión de un Google Doc/Sheet/Slide/Drawing a un formato descargable (docx, xlsx, pptx, pdf, csv, md).

## Convención EARS

- **Ubicuo**: "El sistema DEBE …"
- **Evento**: "CUANDO <evento>, el sistema DEBE …"
- **Estado**: "MIENTRAS <estado>, el sistema DEBE …"
- **Condicional**: "SI <condición>, ENTONCES el sistema DEBE …"
- **Opcional**: "DONDE <feature>, el sistema DEBE …"

---

## Historia 1 — Autenticación OAuth 2.0

**Como** agente, **quiero** autenticarme contra la Drive API con OAuth de escritorio y refresh automático, **para** operar en nombre del usuario sin re-login manual constante.

- 1.1 CUANDO se ejecute `drive_cli.py auth` sin token válido, el sistema DEBE iniciar el flujo OAuth 2.0 installed-app (loopback local) y guardar el token en la ruta configurada.
- 1.2 MIENTRAS exista un `token.json` con `refresh_token` válido, el sistema DEBE renovar el access token automáticamente sin intervención del usuario.
- 1.3 SI el token está expirado y no puede renovarse (refresh revocado), ENTONCES el sistema DEBE fallar con código de salida distinto de cero y un mensaje que instruya re-ejecutar `auth`.
- 1.4 El sistema DEBE leer las rutas de credenciales y token desde `GDRIVE_CREDENTIALS_PATH` y `GDRIVE_TOKEN_PATH`, con default fuera del repo (`~/.config/gdrive-skill/`).
- 1.5 El sistema DEBE usar el scope configurable, documentando la diferencia entre `drive.file` y `drive`, con `drive` como default justificado (organizar archivos existentes).
- 1.6 El sistema NUNCA DEBE registrar en logs el contenido de tokens ni de credenciales.

## Historia 2 — Descubrir unidades compartidas

**Como** agente, **quiero** listar las Shared Drives accesibles, **para** resolver rutas y dirigir operaciones a la unidad correcta.

- 2.1 CUANDO se ejecute `drives`, el sistema DEBE listar `id` y `name` de todas las unidades compartidas accesibles.
- 2.2 El sistema DEBE paginar completamente usando `nextPageToken` hasta agotar resultados.
- 2.3 El sistema DEBE emitir el resultado como JSON por defecto y en formato legible CON `--pretty`.

## Historia 3 — Listar y buscar

**Como** agente, **quiero** listar y buscar archivos por nombre, carpeta, tipo MIME, fecha de modificación o propietario, **para** localizar archivos antes de operarlos.

- 3.1 CUANDO se ejecute `list` o `search`, el sistema DEBE aceptar filtros por nombre, carpeta (`--parent`), tipo MIME, fecha de modificación y propietario.
- 3.2 El sistema DEBE permitir acotar el ámbito a Mi unidad (`--scope mydrive`), a una unidad compartida (`--drive <id|nombre>`) o a todas (`--scope all`).
- 3.3 El sistema DEBE incluir en TODA consulta `supportsAllDrives=True`, `includeItemsFromAllDrives=True` y el `corpora` correspondiente al ámbito.
- 3.4 El sistema DEBE paginar completamente con `nextPageToken`.
- 3.5 SI un filtro produce cero resultados, ENTONCES el sistema DEBE devolver una lista vacía con código de salida cero (no es error).

## Historia 4 — Descargar

**Como** agente, **quiero** descargar archivos binarios y exportar Google Docs/Sheets/Slides/Drawings, **para** obtener copias locales en el formato adecuado.

- 4.1 CUANDO el archivo sea binario, el sistema DEBE descargarlo directamente vía `files.get(alt=media)`.
- 4.2 CUANDO el archivo sea de tipo Google (Docs/Sheets/Slides/Drawings), el sistema DEBE exportarlo con `files.export` al formato elegido (`--export docx|xlsx|pptx|pdf|csv|md`), con un default razonable por tipo.
- 4.3 SI se solicita exportar a un formato no soportado por ese tipo Google, ENTONCES el sistema DEBE fallar con mensaje claro listando formatos válidos.
- 4.4 DONDE se indique `--recursive` sobre una carpeta, el sistema DEBE descargar el árbol completo conservando la estructura de subcarpetas.
- 4.5 El sistema DEBE usar descarga por chunks (`MediaIoBaseDownload`) para archivos grandes.
- 4.6 El sistema NUNCA DEBE registrar el contenido de los archivos descargados en logs.

## Historia 5 — Subir

**Como** agente, **quiero** subir archivos con estrategia simple o resumable, **para** cargar contenido de cualquier tamaño de forma fiable.

- 5.1 CUANDO el archivo pese ≤ 5 MB, el sistema DEBE usar subida simple; CUANDO pese > 5 MB, el sistema DEBE usar subida resumable.
- 5.2 DONDE se indique `--convert`, el sistema DEBE convertir el archivo al formato Google equivalente al crearlo.
- 5.3 SI ya existe un archivo con el mismo nombre en el destino, ENTONCES el sistema DEBE detenerse y preguntar la estrategia: `new`, `replace` o `version`; con `--on-conflict` la decisión puede pre-seleccionarse.
- 5.4 El sistema DEBE incluir `supportsAllDrives=True` para subir tanto a Mi unidad como a unidades compartidas.
- 5.5 DONDE se indique `--dry-run`, el sistema DEBE reportar qué subiría y a dónde SIN ejecutar la subida.

## Historia 6 — Actualizar

**Como** agente, **quiero** actualizar el contenido o los metadatos de un archivo existente, **para** versionar sin crear duplicados.

- 6.1 CUANDO se ejecute `update --content`, el sistema DEBE reemplazar el contenido del mismo `fileId` (nueva revisión), no crear un archivo nuevo.
- 6.2 CUANDO se ejecute `update --metadata`, el sistema DEBE actualizar nombre, descripción y/o propiedades sin tocar el contenido.
- 6.3 El reemplazo de contenido es operación destructiva: SI no se pasa confirmación (`--yes`) ni `--dry-run`, ENTONCES el sistema DEBE requerir confirmación explícita antes de ejecutar.

## Historia 7 — Organizar

**Como** agente, **quiero** crear carpetas, mover, renombrar, copiar, y enviar/restaurar de papelera, **para** organizar Drive incluyendo reglas por lote.

- 7.1 CUANDO se ejecute `organize mkdir a/b/c`, el sistema DEBE crear la ruta anidada completa, reutilizando carpetas existentes.
- 7.2 CUANDO se ejecute `organize move`, el sistema DEBE mover entre carpetas y entre unidades (ajustando `addParents`/`removeParents` con `supportsAllDrives=True`).
- 7.3 El sistema DEBE soportar `rename`, `copy`, `trash` y `restore`.
- 7.4 DONDE se indique una regla por lote (p. ej. "mover todos los PDF de X a X/PDF"), el sistema DEBE resolver el conjunto y aplicar la operación a cada elemento.
- 7.5 El sistema NUNCA DEBE implementar borrado permanente (`files.delete`) ni vaciado de papelera.
- 7.6 SI la operación es destructiva o masiva (>10 elementos, `trash`, reemplazo), ENTONCES el sistema DEBE requerir confirmación explícita, y DONDE se pase `--dry-run` DEBE mostrar el plan sin ejecutar.

## Historia 8 — Resolución de rutas legibles

**Como** agente, **quiero** convertir rutas legibles a `fileId`, **para** operar sin conocer IDs.

- 8.1 CUANDO se pase una ruta tipo `"Unidad/Carpeta/Sub"`, el sistema DEBE resolverla al `fileId` correspondiente, distinguiendo raíz de Mi unidad vs. Shared Drive.
- 8.2 SI un segmento de ruta tiene nombres duplicados, ENTONCES el sistema DEBE devolver los candidatos (id + ruta) y pedir desambiguación en lugar de elegir arbitrariamente.
- 8.3 SI un segmento no existe, ENTONCES el sistema DEBE fallar con mensaje que indique el segmento faltante.

---

## Requisitos no funcionales

### RNF-1 Resiliencia
- El sistema DEBE reintentar con backoff exponencial + jitter ante HTTP 429, 500 y 503, con máximo de reintentos configurable.
- El sistema DEBE aplicar un timeout por operación y fallar rápido en transacciones cortas.

### RNF-2 Salida e interfaz
- Toda salida del CLI DEBE ser JSON por defecto; `--pretty` produce salida legible.
- El sistema DEBE usar códigos de salida definidos: `0` éxito; `2` error de uso/argumentos; `3` permisos insuficientes; `4` no encontrado; `5` cuota excedida; `6` conflicto no resuelto; `7` auth requerida.

### RNF-3 Seguridad (entorno regulado)
- `credentials.json` y `token.json` NUNCA se versionan: DEBEN estar en `.gitignore`.
- Sin secretos hardcodeados. Sin telemetría externa.
- Logging estructurado SIN contenido de archivos ni tokens; los identificadores sensibles se registran enmascarados.
- Confirmación explícita antes de cualquier operación destructiva o masiva; `--dry-run` disponible en toda operación que modifique estado.
- Scopes mínimos configurables; `drive` justificado y documentado frente a `drive.file`.

### RNF-4 Compatibilidad de unidades
- TODA operación DEBE funcionar igual en Mi unidad y en Shared Drives usando `supportsAllDrives=True` (y `includeItemsFromAllDrives=True` en listados).

### RNF-5 Testing
- Los tests DEBEN ejecutarse sin credenciales reales ni llamadas de red, mockeando el servicio de la Drive API.
- Cobertura mínima sobre la lógica de negocio (cliente, reintentos, resolución de rutas, decisión simple/resumable, mapeo MIME).

---

## Criterios de aceptación globales

- [ ] Petición en lenguaje natural "descarga la carpeta Contratos de la unidad compartida Legal como PDF" se ejecuta correctamente (resolución de ruta + export recursivo).
- [ ] Todas las operaciones funcionan igual en Mi unidad y en Shared Drives.
- [ ] `--dry-run` disponible en todas las operaciones que modifican estado.
- [ ] Los tests pasan sin credenciales reales.
- [ ] `credentials.json`/`token.json` están en `.gitignore` y fuera del repo por default.
- [ ] No existe ninguna ruta de código que llame a `files.delete` ni vacíe la papelera.
- [ ] La salida por defecto es JSON parseable; `--pretty` produce salida humana.
