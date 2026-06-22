---
name: aws-sso-refresh
description: Refresca credenciales temporales de AWS SSO (Soluciones Bolívar Identity Center) para cualquier perfil configurado en ~/.aws/credentials. Úsalo cuando el usuario diga que sus credenciales de AWS expiraron, necesite autenticarse a una cuenta AWS, quiera refrescar un perfil específico o pida ejecutar aws-refresh.
version: 1.0.0
author: HernanBetancurBolivar01
category: devops
tags: [aws, sso, credentials, iam, identity-center, autenticacion]
compatibility: [claude-code]
allowed-tools: [Bash, Read, Write]
examples:
  - prompt: "mis credenciales de AWS expiraron"
  - prompt: "refresca las credenciales de ciencuadras"
  - prompt: "necesito autenticarme a AWS en el perfil libertador"
  - prompt: "corre aws-refresh para not-prod"
  - prompt: "actualiza el perfil appsia-dev"
---

# AWS SSO Refresh

Refresca credenciales temporales de AWS SSO para los perfiles configurados en `~/.aws/credentials`. Cada línea de negocio tiene su propia carpeta en `cuentas/` con su `config.env`.

## Cuándo usar este skill

- El usuario dice que sus credenciales de AWS expiraron o tiene error `ExpiredToken`.
- Pide refrescar, actualizar o renovar un perfil AWS específico.
- Pide correr `aws-refresh` con o sin nombre de perfil.
- Necesita autenticarse al portal de Soluciones Bolívar para obtener credenciales temporales.

## Cuándo NO usar

- El usuario tiene credenciales permanentes (access keys fijas); esas no expiran y no necesitan refresh.
- El usuario trabaja con una cuenta AWS de otro proveedor SSO distinto a `solucionesbolivar.awsapps.com`.

## Workflow

### Ejecutar el refresh

```bash
bash skills/devops/aws-sso-refresh/scripts/aws-refresh.sh <nombre-perfil>
```

El script:
1. Abre el navegador con el portal de Soluciones Bolívar para login.
2. Lee `cuentas/<perfil>/config.env` para obtener `ACCOUNT_ID` y `ROLE_NAME`.
3. Si `config.env` está vacío, hace descubrimiento interactivo y guarda los valores.
4. Actualiza `~/.aws/credentials` con las nuevas credenciales temporales.

### Perfiles disponibles

Cada carpeta en `cuentas/` corresponde a un perfil en `~/.aws/credentials`:

| Carpeta | Perfil AWS | Estado config |
|---|---|---|
| `cuentas/ciencuadras/` | `ciencuadras` | Configurado |
| `cuentas/libertador/` | `libertador` | Pendiente |
| `cuentas/archibol/` | `archibol` | Pendiente |
| `cuentas/arkan/` | `arkan` | Pendiente |
| `cuentas/not-prod/` | `not-prod` | Pendiente |
| `cuentas/appsia-dev/` | `appsia-dev` | Pendiente |
| `cuentas/appsia-prod/` | `appsia-prod` | Pendiente |
| `cuentas/motor-stage/` | `motor-stage` | Pendiente |

### Agregar una nueva cuenta

1. Crear carpeta: `cuentas/<nombre-perfil>/`
2. Crear `config.env` con `ACCOUNT_ID` y `ROLE_NAME`.
3. La primera vez que corras `aws-refresh <perfil>` con `config.env` vacío, el script descubre y guarda los valores automáticamente.

## Recursos

- `scripts/aws-refresh.sh` — script principal de refresh.
- `cuentas/*/config.env` — configuración por línea de negocio.
- `~/.aws/.sso_vars` — URL del portal SSO y región (global, fuera del skill).

## Anti-patrones

- No hardcodear credenciales temporales en código; siempre usar el perfil AWS con `--profile`.
- No compartir `config.env` con `ACCOUNT_ID` en repos públicos si las cuentas son sensibles.
