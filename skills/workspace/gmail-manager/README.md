# gmail-manager

Skill de línea de comandos (Python 3.12+, solo lectura) que lee el correo corporativo de Gmail
segmentado por línea de negocio y alimenta el second brain (`obsidian-manager`) con el contexto
relevante, clasificado por criticidad. No envía, borra ni modifica correos. Sin proceso residente:
cada corrida termina (pensado para cron/launchd cada 6 h).

## 1. Instalación

Reutiliza las librerías cliente de Google. Puedes usar el venv de `google-drive-manager` o crear uno:

```bash
python3 -m venv .venv-gmail
./.venv-gmail/bin/pip install -r requirements.txt   # desde el mirror JFrog
```

## 2. Credenciales OAuth

El scope es `gmail.readonly`. Necesitas un client OAuth de Google en
`~/.config/gmail-skill/credentials.json`:

- **Opción A (recomendada):** un client tipo *Aplicación de escritorio* (installed) — el flujo usa
  loopback con puerto aleatorio.
- **Opción B:** un client *web* con redirect `http://localhost:8080/callback` autorizado (el mismo
  que usa `google-drive-manager`). Apunta `GMAIL_CREDENTIALS_PATH` a ese `credentials.json`.

```bash
mkdir -p ~/.config/gmail-skill
# copia tu client OAuth:
cp ~/Downloads/client_secret_*.json ~/.config/gmail-skill/credentials.json
python3 scripts/gmail_cli.py auth   # autoriza en el navegador (solo lectura)
```

El token se guarda en `~/.config/gmail-skill/token.json` (0600), separado del de Drive.

## 3. Variables de entorno

| Variable | Default | Descripción |
|---|---|---|
| `GMAIL_CREDENTIALS_PATH` | `~/.config/gmail-skill/credentials.json` | Client OAuth. |
| `GMAIL_TOKEN_PATH` | `~/.config/gmail-skill/token.json` | Token (se crea en el primer login). |
| `GMAIL_STATE_PATH` | `~/.config/gmail-skill/state.json` | Estado incremental por etiqueta. |
| `OBSIDIAN_CLI` | ruta del repo | `obsidian_cli.py` para escribir al vault. |

## 4. Uso

Ver `SKILL.md` para la tabla de comandos. Resumen:

```bash
python3 scripts/gmail_cli.py --pretty labels                 # verifica etiquetas y mapeo
python3 scripts/gmail_cli.py --pretty scan --dry-run --max 20 # primer barrido en seco
python3 scripts/gmail_cli.py scan                            # barrido real (12 meses la 1ª vez)
python3 scripts/gmail_cli.py scan --incremental             # incremental (para el cron)
```

Salida JSON con conteos por etiqueta (`leidos`, `alta`, `media`, `ignorados`).

## 5. Cómo decide qué indexar

- **Alta** → nota en `proyectos/<línea>/` (decisiones, arquitectura, incidentes, infra, accesos por
  referencia, acuerdos, fechas límite, compromisos dirigidos a ti).
- **Media** → entrada breve en la bitácora del proyecto.
- **Baja** → ignorado.

Nunca se vuelca el cuerpo completo: solo snippet saneado + resumen + enlace al hilo. Los secretos/PII
se enmascaran antes de escribir.

## 6. Ejecución periódica

```cron
0 */6 * * * /ruta/.venv-gmail/bin/python /ruta/skills/workspace/gmail-manager/scripts/gmail_cli.py scan --incremental >> ~/.config/gmail-skill/scan.log 2>&1
```

En macOS también puede usarse un `launchd` `.plist` con `StartInterval 21600`.

## 7. Seguridad

- Solo lectura, sin borrado ni modificación.
- `credentials.json` / `token.json` / `state.json` nunca se versionan (en `.gitignore`), viven fuera
  del repo.
- Sin secretos hardcodeados; sin telemetría. Logs sin cuerpos de correos ni tokens.

## 8. Arquitectura

- `scripts/auth.py` — OAuth readonly (installed o web con callback fijo), refresh y persistencia.
- `scripts/gmail_client.py` — capa sobre Gmail API v1: labels, búsqueda paginada por `after:`,
  metadata+snippet, reintentos con backoff.
- `scripts/classifier.py` — reglas de criticidad, detección de compromiso, redacción de secretos/PII.
- `scripts/state.py` — estado incremental por etiqueta (12 m inicial / incremental con solape).
- `scripts/gmail_cli.py` — orquestación y escritura al vault vía `obsidian_cli.py`.
- `tests/` — 24 tests con dobles (sin red ni credenciales).
