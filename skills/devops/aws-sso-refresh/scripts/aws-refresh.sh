#!/bin/bash
# aws-refresh.sh — Refresca credenciales temporales de AWS SSO
# Uso: aws-refresh.sh [perfil1] [perfil2] ...
# Ejemplo: aws-refresh.sh ciencuadras not-prod

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
CUENTAS_DIR="$SKILL_DIR/cuentas"
VARS_FILE="$HOME/.aws/.sso_vars"

if [ ! -f "$VARS_FILE" ]; then
  echo "Error: no se encontró $VARS_FILE con la configuración del portal SSO."
  exit 1
fi

source "$VARS_FILE"

PROFILES=("${@:-ciencuadras}")

# ── Paso 1: Registrar cliente OIDC ───────────────────────────────────────────
echo "Conectando a AWS SSO ($SSO_START_URL)..."

CLIENT=$(aws sso-oidc register-client \
  --client-name "aws-refresh-$(hostname -s)" \
  --client-type "public" \
  --region "$SSO_REGION" \
  --output json)

CLIENT_ID=$(echo "$CLIENT"     | python3 -c "import sys,json; print(json.load(sys.stdin)['clientId'])")
CLIENT_SECRET=$(echo "$CLIENT" | python3 -c "import sys,json; print(json.load(sys.stdin)['clientSecret'])")

# ── Paso 2: Iniciar autorización de dispositivo ──────────────────────────────
DEVICE=$(aws sso-oidc start-device-authorization \
  --client-id "$CLIENT_ID" \
  --client-secret "$CLIENT_SECRET" \
  --start-url "$SSO_START_URL" \
  --region "$SSO_REGION" \
  --output json)

VERIFY_URL=$(echo "$DEVICE"  | python3 -c "import sys,json; print(json.load(sys.stdin)['verificationUriComplete'])")
DEVICE_CODE=$(echo "$DEVICE" | python3 -c "import sys,json; print(json.load(sys.stdin)['deviceCode'])")
INTERVAL=$(echo "$DEVICE"    | python3 -c "import sys,json; print(json.load(sys.stdin)['interval'])")
EXPIRES_IN=$(echo "$DEVICE"  | python3 -c "import sys,json; print(json.load(sys.stdin)['expiresIn'])")

echo ""
echo "Abre este enlace en tu navegador y aprueba el acceso:"
echo "  $VERIFY_URL"
echo ""
open "$VERIFY_URL" 2>/dev/null || true
echo "Esperando que completes el login..."

# ── Paso 3: Esperar el token ──────────────────────────────────────────────────
ACCESS_TOKEN=""
WAITED=0

while [ "$WAITED" -lt "$EXPIRES_IN" ]; do
  sleep "$INTERVAL"
  WAITED=$((WAITED + INTERVAL))

  TOKEN_RESP=$(aws sso-oidc create-token \
    --client-id "$CLIENT_ID" \
    --client-secret "$CLIENT_SECRET" \
    --grant-type "urn:ietf:params:oauth:grant-type:device_code" \
    --device-code "$DEVICE_CODE" \
    --region "$SSO_REGION" \
    --output json 2>/dev/null || echo "PENDING")

  if [ "$TOKEN_RESP" != "PENDING" ]; then
    ACCESS_TOKEN=$(echo "$TOKEN_RESP" | python3 -c "import sys,json; print(json.load(sys.stdin)['accessToken'])")
    echo "✓ Login exitoso!"
    break
  fi
done

if [ -z "$ACCESS_TOKEN" ]; then
  echo "Error: tiempo de espera agotado. Ejecuta el script de nuevo."
  exit 1
fi

# ── Paso 4: Refrescar cada perfil ────────────────────────────────────────────
for TARGET_PROFILE in "${PROFILES[@]}"; do
  echo ""
  echo "── Perfil: $TARGET_PROFILE ──"

  CONFIG_FILE="$CUENTAS_DIR/$TARGET_PROFILE/config.env"
  ACCOUNT_ID=""
  ROLE_NAME=""

  # Leer config.env del perfil si existe
  if [ -f "$CONFIG_FILE" ]; then
    source "$CONFIG_FILE"
  fi

  # Si faltan valores, hacer descubrimiento interactivo
  if [ -z "$ACCOUNT_ID" ] || [ -z "$ROLE_NAME" ]; then
    echo "Primera vez para '$TARGET_PROFILE'. Descubriendo cuentas disponibles..."

    ACCOUNTS=$(aws sso list-accounts \
      --access-token "$ACCESS_TOKEN" \
      --region "$SSO_REGION" \
      --output json)

    echo ""
    echo "$ACCOUNTS" | python3 -c "
import sys, json
accounts = json.load(sys.stdin)['accountList']
for i, a in enumerate(accounts, 1):
    print(f'  [{i}] {a[\"accountName\"]:45s} {a[\"accountId\"]}')
"
    read -rp "Selecciona el número de cuenta para '$TARGET_PROFILE': " SEL_ACCOUNT
    ACCOUNT_ID=$(echo "$ACCOUNTS" | python3 -c "
import sys, json
accounts = json.load(sys.stdin)['accountList']
print(accounts[$((SEL_ACCOUNT - 1))]['accountId'])
")

    ROLES=$(aws sso list-account-roles \
      --account-id "$ACCOUNT_ID" \
      --access-token "$ACCESS_TOKEN" \
      --region "$SSO_REGION" \
      --output json)

    ROLE_COUNT=$(echo "$ROLES" | python3 -c "import sys,json; print(len(json.load(sys.stdin)['roleList']))")

    if [ "$ROLE_COUNT" -eq 1 ]; then
      ROLE_NAME=$(echo "$ROLES" | python3 -c "import sys,json; print(json.load(sys.stdin)['roleList'][0]['roleName'])")
      echo "Rol detectado automáticamente: $ROLE_NAME"
    else
      echo ""
      echo "$ROLES" | python3 -c "
import sys, json
roles = json.load(sys.stdin)['roleList']
for i, r in enumerate(roles, 1):
    print(f'  [{i}] {r[\"roleName\"]}')
"
      read -rp "Selecciona el número de rol: " SEL_ROLE
      ROLE_NAME=$(echo "$ROLES" | python3 -c "
import sys, json
roles = json.load(sys.stdin)['roleList']
print(roles[$((SEL_ROLE - 1))]['roleName'])
")
    fi

    # Guardar en config.env del perfil
    mkdir -p "$CUENTAS_DIR/$TARGET_PROFILE"
    cat > "$CONFIG_FILE" <<EOF
ACCOUNT_ID=$ACCOUNT_ID
ROLE_NAME=$ROLE_NAME
EOF
    echo "Configuración guardada en $CONFIG_FILE"
  fi

  # Obtener credenciales temporales
  CREDS=$(aws sso get-role-credentials \
    --account-id "$ACCOUNT_ID" \
    --role-name  "$ROLE_NAME" \
    --access-token "$ACCESS_TOKEN" \
    --region "$SSO_REGION" \
    --output json)

  AK=$(echo "$CREDS" | python3 -c "import sys,json; print(json.load(sys.stdin)['roleCredentials']['accessKeyId'])")
  SK=$(echo "$CREDS" | python3 -c "import sys,json; print(json.load(sys.stdin)['roleCredentials']['secretAccessKey'])")
  ST=$(echo "$CREDS" | python3 -c "import sys,json; print(json.load(sys.stdin)['roleCredentials']['sessionToken'])")
  EX=$(echo "$CREDS" | python3 -c "import sys,json; print(json.load(sys.stdin)['roleCredentials']['expiration'])")

  aws configure set aws_access_key_id     "$AK" --profile "$TARGET_PROFILE"
  aws configure set aws_secret_access_key "$SK" --profile "$TARGET_PROFILE"
  aws configure set aws_session_token     "$ST" --profile "$TARGET_PROFILE"

  EXPIRY=$(python3 -c "import datetime; print(datetime.datetime.fromtimestamp($EX/1000).strftime('%Y-%m-%d %H:%M:%S'))")
  echo "✓ Credenciales actualizadas  |  expiran: $EXPIRY"
done

echo ""
echo "Listo."
