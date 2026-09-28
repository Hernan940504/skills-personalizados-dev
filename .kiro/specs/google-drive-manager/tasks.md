# Tasks — Skill `google-drive-manager`

Cada tarea incluye sus tests con mocks de la API (sin red, sin credenciales reales). Se implementa
tarea por tarea; ninguna se marca completada hasta que sus tests pasen.

- [ ] 1. Scaffolding del skill
  - Crear `skills/workspace/google-drive-manager/` con `scripts/`, `tests/`.
  - Añadir `requirements.txt` con dependencias pinneadas (design §8).
  - Añadir patrones `credentials.json` y `token.json` al `.gitignore` del repo.
  - _Requisitos: RNF-3, 8_

- [ ] 2. `mime_map.py` — mapeo de exportación/conversión
  - `EXPORT_MAP`, `DEFAULT_EXPORT`, `CONVERT_MAP` y helpers `resolve_export(google_mime, fmt)` y `default_export(google_mime)`.
  - Tests: default por tipo, formato inválido levanta error listando válidos, conversión de subida.
  - _Requisitos: 4.2, 4.3, 5.2_

- [ ] 3. `auth.py` — credenciales y token
  - `load_settings()` (env vars + defaults), constantes de scope, `get_credentials()` (válido/refresh/flujo nuevo), persistencia `0600`.
  - Tests: refresh cuando expira, flujo nuevo cuando no hay token, error tipado cuando refresh revocado; sin loguear token.
  - _Requisitos: 1.1–1.6, RNF-3_

- [ ] 4. `drive_client.py` — núcleo: `_execute` + reintentos + errores tipados
  - Backoff exponencial + jitter sobre 429/500/503; clasificación de `HttpError` a excepciones tipadas.
  - Tests: reintenta y luego éxito; agota reintentos → `QuotaExceededError`; 403-permiso vs 403-quota; 404 → `NotFoundError`.
  - _Requisitos: RNF-1, manejo de errores (design §4)_

- [ ] 5. `drive_client.py` — paginación y `drives`/`list`/`search`
  - `_paginate` con `nextPageToken`; inyección de `supportsAllDrives`, `includeItemsFromAllDrives`, `corpora`; `list_shared_drives`, `search` con filtros y ámbito.
  - Tests: pagina 3 páginas y concatena; verifica que los flags de all-drives y `corpora` van en la query; filtros construyen el `q` esperado; cero resultados → lista vacía.
  - _Requisitos: 2.1–2.3, 3.1–3.5, RNF-4_

- [ ] 6. `drive_client.py` — descarga y export
  - `download_file` (media por chunks), `export_file` (formato + default), `download_folder_recursive` (estructura preservada).
  - Tests: binario usa get_media; Google usa export con MIME correcto; recursivo recrea árbol (con FS mockeado/tmp); nunca loguea contenido.
  - _Requisitos: 4.1–4.6_

- [ ] 7. `drive_client.py` — subida y actualización
  - `upload` con selección simple/resumable por umbral 5 MB, `--convert`, detección de conflicto por nombre; `update_content`, `update_metadata`.
  - Tests: ≤5 MB simple / >5 MB resumable; conflicto devuelve señal para preguntar; convert setea MIME Google; update_content reusa fileId (no crea nuevo).
  - _Requisitos: 5.1–5.5, 6.1–6.3_

- [ ] 8. `drive_client.py` — organización y resolución de rutas
  - `mkdir_p` anidado (reutiliza existentes), `move` (add/removeParents entre unidades), `rename`, `copy`, `trash`, `restore`, `resolve_path` con desambiguación.
  - Verificar ausencia de `files.delete`/`emptyTrash`.
  - Tests: mkdir anidado crea sólo faltantes; move ajusta parents con supportsAllDrives; ruta duplicada devuelve candidatos; segmento faltante → error; no existe llamada a delete.
  - _Requisitos: 7.1–7.6, 8.1–8.3, RNF-3_

- [ ] 9. `drive_cli.py` — capa CLI
  - Subparsers de todos los comandos; flags globales `--pretty/--dry-run/--yes/--scope/--drive/--log-level`; serialización JSON; códigos de salida (design §4); bloqueo de destructivas sin `--yes`/`--dry-run`.
  - Reglas por lote en `organize` (p. ej. mover todos los PDF de X a X/PDF).
  - Tests: dispatch de subcomandos, JSON vs `--pretty`, exit codes por tipo de error, dry-run no ejecuta, destructiva sin confirmación se rechaza.
  - _Requisitos: 3.2, 5.3, 6.3, 7.4, 7.6, RNF-2, RNF-3_

- [ ] 10. `SKILL.md`
  - Frontmatter (`name`, `description` con frases de activación, `version`, `category: workspace`, `tags`, `compatibility`, `examples`).
  - Body: cuándo usar / cuándo no, workflow por subcomando, cómo parsear la salida JSON, reglas de seguridad y confirmación.
  - _Requisitos: objetivo global, criterios de aceptación_

- [ ] 11. `README.md` (setup humano)
  - Crear proyecto GCP, habilitar Drive API, configurar pantalla de consentimiento OAuth (interna si es Workspace), descargar `credentials.json`, primer `auth`.
  - Config de env vars, scopes (`drive` vs `drive.file`), nota JFrog, ejemplos de uso por subcomando (incluye "descargar carpeta X de Shared Drive Legal como PDF").
  - _Requisitos: criterios de aceptación globales_

- [ ] 12. Verificación final
  - Ejecutar toda la suite de tests sin credenciales; confirmar exit codes y ausencia de rutas de borrado permanente; validar el `SKILL.md` contra las reglas del repo.
  - _Requisitos: RNF-5, criterios de aceptación globales_
