# Plan de implementación — gmail-manager

- [ ] 1. Estructura del skill y dependencias
  - Crear `skills/workspace/gmail-manager/` con `scripts/`, `tests/`, `requirements.txt`
    (google-api-python-client, google-auth, google-auth-oauthlib, google-auth-httplib2, pinneadas),
    `SKILL.md`, `README.md`.
  - Añadir `credentials.json`, `token.json`, `state.json` de gmail al `.gitignore`.
  - _Req: 1, 6_

- [ ] 2. Autenticación (`auth.py`)
  - Portar el patrón de `google-drive-manager/scripts/auth.py` con scope `gmail.readonly`, rutas
    `~/.config/gmail-skill/`, refresh y persistencia 0600.
  - _Req: 1_

- [ ] 3. Cliente Gmail (`gmail_client.py`)
  - `list_labels`, filtro `Tribu Servicios Bolivar/*`, `search_messages` paginado con `after`,
    `get_message` (metadata+snippet), armado de enlace al hilo. Reintentos con backoff.
  - _Req: 2, 3, 5_

- [ ] 4. Estado incremental (`state.py`)
  - Leer/escribir `state.json`; cálculo de `after` (12m inicial / incremental con solape); poda de `seen`.
  - _Req: 3_

- [ ] 5. Clasificador (`classifier.py`)
  - Reglas alta/media/baja configurables; detección de compromiso dirigido al usuario; `redact()`
    de secretos/PII. Sin cuerpo completo.
  - _Req: 4, 6_

- [ ] 6. CLI (`gmail_cli.py`)
  - Subcomandos `auth`, `labels`, `scan` (--label, --since-months, --incremental, --dry-run, --max);
    flags globales; salida JSON; escritura al vault invocando `obsidian_cli.py`.
  - _Req: 2, 3, 4, 5_

- [ ] 7. Tests con mocks (sin red ni credenciales)
  - Auth (refresh/persistencia), clasificador (casos alta/media/baja + compromiso + redacción),
    estado (12m/incremental/idempotencia), cliente (paginación con dobles), CLI (dry-run, JSON).
  - _Req: todos_

- [ ] 8. Documentación y operación periódica
  - `SKILL.md` (validado contra reglas del repo), `README.md` (setup OAuth, mapeo etiqueta→proyecto,
    criterios de criticidad, ejemplo cron/launchd cada 6 h).
  - _Req: 5, 6_

- [ ] 9. Verificación end-to-end acotada
  - `labels` real; `scan --dry-run --max` pequeño sobre una etiqueta para validar clasificación
    antes del barrido completo.
  - _Req: 2, 3, 4_
