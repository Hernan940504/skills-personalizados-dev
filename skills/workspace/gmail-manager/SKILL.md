---
name: gmail-manager
description: Lee de solo lectura el correo corporativo de Gmail y extrae contexto de negocio por
  línea de negocio hacia el second brain (obsidian-manager). Barre las etiquetas
  "Tribu Servicios Bolivar/<Línea>", clasifica cada correo por criticidad (alta/media/baja),
  detecta compromisos dirigidos al usuario, enmascara secretos/PII e indexa lo relevante. Primer
  barrido de 12 meses y luego incremental desde la última ejecución. Diseñado para cron/launchd
  cada 6 h, sin proceso residente. Úsalo cuando el usuario diga "revisa mi correo por línea de
  negocio", "barre los correos de Libertador/Proyectiva", "indexa mis compromisos del correo".
version: 1.0.0
author: Hernan940504
category: workspace
tags: [gmail, google-workspace, oauth2, readonly, second-brain, obsidian, cli, python]
compatibility: [claude-code, cursor, kiro, opencode]
allowed-tools: [Read, Bash]
examples:
  - prompt: "autentica el acceso de solo lectura a Gmail"
  - prompt: "lista las etiquetas de mi correo y su mapeo a proyectos"
  - prompt: "haz el primer barrido de los últimos 12 meses de mis líneas de negocio"
  - prompt: "revisa el correo nuevo de Proyectiva e indexa lo crítico"
---

# gmail-manager

CLI Python (solo lectura) que convierte el correo corporativo, segmentado por línea de negocio, en
notas del second brain. No envía, borra ni modifica correos.

## Requisitos

- Python 3.12+ y las librerías cliente de Google (`requirements.txt`, pinneadas; instalar desde JFrog).
  Reutilizable el venv de `google-drive-manager`.
- Un client OAuth de Google (`credentials.json`). Sirve el mismo client web con redirect
  `http://localhost:8080/callback` usado por `google-drive-manager`, o uno de tipo Desktop.
- Variables de entorno (opcionales, con defaults fuera del repo):
  - `GMAIL_CREDENTIALS_PATH` (default `~/.config/gmail-skill/credentials.json`)
  - `GMAIL_TOKEN_PATH` (default `~/.config/gmail-skill/token.json`)
  - `GMAIL_STATE_PATH` (default `~/.config/gmail-skill/state.json`)
  - `OBSIDIAN_CLI` (ruta a `obsidian_cli.py`; por defecto la del repo)

## Scope

Exclusivamente `https://www.googleapis.com/auth/gmail.readonly`. El skill no implementa envío ni
modificación; no hay borrado.

## Comandos

Los flags globales (`--pretty`) van **antes** del subcomando.

```bash
# Autenticar una vez (abre navegador; con client web imprime AUTH_URL para aprobar).
python3 scripts/gmail_cli.py auth

# Listar etiquetas y su mapeo a proyectos del vault.
python3 scripts/gmail_cli.py --pretty labels

# Primer barrido (12 meses) de todas las líneas, en seco (no escribe):
python3 scripts/gmail_cli.py --pretty scan --dry-run --max 20

# Barrido real de una etiqueta:
python3 scripts/gmail_cli.py scan --label "Tribu Servicios Bolivar/Libertador"

# Incremental (usa el estado previo): pensado para el cron cada 6 h.
python3 scripts/gmail_cli.py scan --incremental
```

## Mapeo etiqueta → proyecto del vault

| Etiqueta Gmail | Proyecto / tag |
|---|---|
| Tribu Servicios Bolivar/Ciencuadras | ciencuadras |
| Tribu Servicios Bolivar/Libertador | libertador |
| Tribu Servicios Bolivar/Proyectiva | proyectiva |
| Tribu Servicios Bolivar/Notificador | notificador-transversal |
| Tribu Servicios Bolivar/RC | relacionamiento-contextual |

## Criticidad

- **Alta** → nota en `proyectos/<línea>/`: decisiones, arquitectura, incidentes, infra, accesos
  (por referencia, sin el valor), acuerdos, fechas límite, y correos donde te dejan un compromiso.
- **Media** → entrada breve en la bitácora del proyecto.
- **Baja** → se ignora (newsletters, notificaciones automáticas de Jira/Datadog, promociones).

Antes de escribir, se enmascaran patrones de secretos/PII y nunca se vuelca el cuerpo completo (solo
el snippet saneado + resumen + enlace al hilo).

## Operación periódica (cada 6 h)

No hay daemon: lo dispara el scheduler del sistema. Ejemplo cron:

```cron
0 */6 * * * /ruta/venv/bin/python /ruta/skills/workspace/gmail-manager/scripts/gmail_cli.py scan --incremental >> ~/.config/gmail-skill/scan.log 2>&1
```

## Seguridad

- Solo lectura; sin borrado ni modificación.
- Credenciales/token/estado fuera del repo y en `.gitignore`.
- No se imprimen cuerpos de correos ni secretos en logs ni en la conversación.
