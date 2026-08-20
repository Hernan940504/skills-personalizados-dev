# gcp-connect

> Conecta y cambia entre proyectos de GCP usando configuraciones nombradas de gcloud. Equivalente GCP del skill `aws-sso-refresh`.

## Propósito

Gestiona el acceso local a múltiples proyectos de Google Cloud sin editar a mano `gcloud config`. Cada línea de negocio vive en `proyectos/<nombre>/config.env`; el script autentica tu cuenta, crea/activa la configuración de gcloud del proyecto y fija project, región y zona. Soporta login de usuario (OAuth), service accounts (`KEY_FILE`) y Application Default Credentials (`--adc`).

## Pre-requisitos

- Google Cloud SDK (`gcloud`) instalado y en el `PATH` — https://cloud.google.com/sdk/docs/install
- `python3` (usado para parsear la salida JSON de gcloud)
- Una cuenta de Google con acceso a los proyectos, o un JSON de service account

## Ejemplos de prompts que lo activan

- "conéctame al proyecto de GCP de archibol"
- "cambia mi gcloud al proyecto de ciencuadras"
- "mis credenciales de GCP expiraron, reauthentication required"
- "corre gcp-connect --adc para mi proyecto"

## Uso directo

```bash
# Conectar / cambiar de proyecto (descubre y guarda la primera vez)
bash scripts/gcp-connect.sh <nombre-proyecto>

# Además configurar ADC para SDKs locales
bash scripts/gcp-connect.sh --adc <nombre-proyecto>

# Sin argumentos: lista los proyectos configurados
bash scripts/gcp-connect.sh
```

## Cómo extenderlo

- **Nuevos proyectos**: copia `proyectos/_ejemplo/config.env` a `proyectos/<nombre>/config.env`, o deja que el descubrimiento interactivo lo cree.
- **Service accounts**: define `KEY_FILE` con la ruta absoluta del JSON (no lo commitees).
- **Región/zona por defecto**: rellena `REGION`/`ZONE` en el `config.env` del proyecto.
