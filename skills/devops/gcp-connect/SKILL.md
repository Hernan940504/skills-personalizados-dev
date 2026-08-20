---
name: gcp-connect
description: Configura y activa configuraciones de gcloud para conectarte a proyectos de GCP. Autentica tu cuenta de Google (OAuth) o una service account, crea/activa una configuración nombrada por proyecto, fija project, región y zona, y opcionalmente refresca ADC. Úsalo cuando el usuario quiera conectarse a un proyecto GCP, cambiar de proyecto, autenticarse en gcloud, renovar credenciales de GCP expiradas (reauthentication required) o correr gcp-connect.
version: 1.0.0
author: Hernan940504
category: devops
tags: [gcp, gcloud, google-cloud, autenticacion, adc, service-account, iam]
compatibility: [claude-code, cursor, kiro, opencode]
allowed-tools: [Bash, Read, Write]
examples:
  - prompt: "conéctame al proyecto de GCP de archibol"
  - prompt: "cambia mi gcloud al proyecto de ciencuadras"
  - prompt: "necesito autenticarme en GCP"
  - prompt: "mis credenciales de GCP expiraron, reauthentication required"
  - prompt: "corre gcp-connect para mi proyecto y configura ADC"
---

# GCP Connect

Conecta y cambia entre proyectos de GCP usando **configuraciones nombradas de gcloud** (una por línea de negocio). Cada proyecto tiene su carpeta en `proyectos/` con su `config.env`. Es el equivalente GCP del skill `aws-sso-refresh`: allí un perfil AWS ≈ aquí una configuración de gcloud.

## Cuándo usar este skill

- El usuario quiere conectarse a un proyecto de GCP o cambiar el proyecto activo de gcloud.
- Pide autenticarse en Google Cloud (`gcloud auth login`) o dice que no tiene cuenta activa.
- Sus credenciales de GCP expiraron: error `reauthentication required`, `invalid_grant` o "problem refreshing your current auth tokens".
- Necesita configurar Application Default Credentials (ADC) para correr SDKs/librerías localmente.
- Pide correr `gcp-connect` con o sin nombre de proyecto.

## Cuándo NO usar

- El usuario trabaja con **AWS**; usa `aws-sso-refresh`.
- Solo quiere **evaluar/diseñar** una arquitectura GCP (no autenticarse); usa `cloud-well-architected-review` o los skills `docs-*`.
- Ya tiene credenciales de service account inyectadas por el entorno (CI con Workload Identity) y no necesita gestionar configuraciones locales.

## Modelo mental (AWS → GCP)

| AWS (`aws-sso-refresh`) | GCP (este skill) |
|---|---|
| Perfil en `~/.aws/credentials` | Configuración de `gcloud config configurations` |
| `cuentas/<perfil>/config.env` (ACCOUNT_ID, ROLE_NAME) | `proyectos/<nombre>/config.env` (PROJECT_ID, ACCOUNT, REGION, ZONE, KEY_FILE) |
| Device-code SSO (Identity Center) | OAuth de Google (`gcloud auth login`) o service account |
| Credenciales temporales por rol (~1h) | Access tokens auto-refrescados por gcloud; reauth según política de sesión de la org |

## Workflow

### Conectar / cambiar de proyecto

```bash
bash skills/devops/gcp-connect/scripts/gcp-connect.sh <nombre-proyecto>
```

El script:
1. Verifica que `gcloud` esté instalado.
2. Si el proyecto no usa service account, asegura una cuenta de usuario autenticada (`gcloud auth login`); si el token expiró (reauth de la org), re-loguea.
3. Lee `proyectos/<nombre>/config.env` para `PROJECT_ID`, `ACCOUNT`, `REGION`, `ZONE`.
4. Si `PROJECT_ID` está vacío, hace **descubrimiento interactivo** (`gcloud projects list`), te deja elegir y guarda los valores.
5. Crea/activa una configuración de gcloud llamada como el proyecto y fija `account`, `project`, `compute/region` y `compute/zone`.
6. Verifica el acceso con `gcloud projects describe`.

### Configurar también ADC (SDKs locales)

```bash
bash skills/devops/gcp-connect/scripts/gcp-connect.sh --adc <nombre-proyecto>
```

Añade `gcloud auth application-default login` y fija el quota-project. Úsalo cuando el código local use librerías cliente de Google Cloud.

### Conectar varios de una vez

```bash
bash skills/devops/gcp-connect/scripts/gcp-connect.sh archibol ciencuadras
```

Crea/actualiza la configuración de cada uno y deja **activo el primero** de la lista.

### Agregar un proyecto nuevo

1. Opción rápida: corre `gcp-connect.sh <nombre-nuevo>` — con `config.env` inexistente o vacío, el script descubre y guarda.
2. Opción manual: crea `proyectos/<nombre>/config.env` copiando `proyectos/_ejemplo/config.env` y completa `PROJECT_ID` (y opcionalmente `ACCOUNT`, `REGION`, `ZONE`, `KEY_FILE`).

### Service account (automatización)

Si un proyecto se conecta con una service account, pon la ruta absoluta del JSON en `KEY_FILE` dentro de su `config.env`. El script activará esa SA en vez de pedir login de usuario.

## Recursos

- `scripts/gcp-connect.sh` — script principal de conexión/activación.
- `proyectos/<nombre>/config.env` — configuración por línea de negocio (creada por descubrimiento).
- `proyectos/_ejemplo/config.env` — plantilla documentada de los campos disponibles.

## Anti-patrones

- No hardcodear tokens de acceso ni project IDs sensibles en código; usar la configuración de gcloud (`--configuration <nombre>` o la activa).
- No commitear archivos de llaves de service account (`KEY_FILE`) al repo; referéncialos por ruta fuera del control de versiones.
- No usar `gcloud auth application-default login` como sustituto del login de usuario para el CLI: ADC es para SDKs, no para autenticar `gcloud` en sí.
- No dejar la configuración `default` como cajón de sastre: una configuración nombrada por proyecto evita cambiar de contexto por error.
