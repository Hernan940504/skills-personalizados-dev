#!/bin/bash
# search-domain-all-accounts.sh
# Busca el dominio MassiveCienCuadrasApp.ciencuadras.com en ACM y CloudFront
# en todas las cuentas proporcionadas via SSO.
set -euo pipefail

DOMAIN="MassiveCienCuadrasApp.ciencuadras.com"
SSO_REGION="us-east-1"
SSO_START_URL="https://solucionesbolivar.awsapps.com/start/"
RESULTS_FILE="/tmp/domain-search-results.txt"

ACCOUNTS=(
  565999949569
  691370287769
  505545527670
  290296201161
  38749957273
  935071422812
  55571516825
  437148509749
  722983015548
  694627937783
  397624050592
  892397120620
  857624955385
  272506905646
  130448862935
  996155636939
  966125231475
  674467843571
  982516576992
  467160885811
  507904767184
  658110252091
  906279163730
  709672348130
  826280447735
  775534688306
  464790332864
  858762616182
  610442843318
  243755603146
  944305913285
  14953646692
  145023099775
  180294192708
  12670877668
  213325653070
  901905860444
  149536466929
  383946777605
  805516213253
  751835846961
)

echo "=== Búsqueda de dominio: $DOMAIN ==="
echo "Cuentas a revisar: ${#ACCOUNTS[@]}"
echo ""
echo "" > "$RESULTS_FILE"

# ── Paso 1: Registrar cliente OIDC ──
echo "Conectando a AWS SSO ($SSO_START_URL)..."

CLIENT=$(aws sso-oidc register-client \
  --client-name "domain-search-$(hostname -s)" \
  --client-type "public" \
  --region "$SSO_REGION" \
  --output json)

CLIENT_ID=$(echo "$CLIENT" | python3 -c "import sys,json; print(json.load(sys.stdin)['clientId'])")
CLIENT_SECRET=$(echo "$CLIENT" | python3 -c "import sys,json; print(json.load(sys.stdin)['clientSecret'])")

# ── Paso 2: Iniciar autorización de dispositivo ──
DEVICE=$(aws sso-oidc start-device-authorization \
  --client-id "$CLIENT_ID" \
  --client-secret "$CLIENT_SECRET" \
  --start-url "$SSO_START_URL" \
  --region "$SSO_REGION" \
  --output json)

VERIFY_URL=$(echo "$DEVICE" | python3 -c "import sys,json; print(json.load(sys.stdin)['verificationUriComplete'])")
DEVICE_CODE=$(echo "$DEVICE" | python3 -c "import sys,json; print(json.load(sys.stdin)['deviceCode'])")
INTERVAL=$(echo "$DEVICE" | python3 -c "import sys,json; print(json.load(sys.stdin)['interval'])")
EXPIRES_IN=$(echo "$DEVICE" | python3 -c "import sys,json; print(json.load(sys.stdin)['expiresIn'])")

echo ""
echo "Abre este enlace en tu navegador y aprueba el acceso:"
echo "  $VERIFY_URL"
echo ""
open "$VERIFY_URL" 2>/dev/null || true
echo "Esperando que completes el login..."

# ── Paso 3: Esperar el token ──
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
  echo "Error: tiempo de espera agotado."
  exit 1
fi

# ── Paso 4: Buscar en cada cuenta ──
echo ""
echo "Iniciando búsqueda en ${#ACCOUNTS[@]} cuentas..."
echo "=========================================="

for ACCT in "${ACCOUNTS[@]}"; do
  echo ""
  echo "── Cuenta: $ACCT ──"

  # Intentar obtener roles disponibles
  ROLES=$(aws sso list-account-roles \
    --account-id "$ACCT" \
    --access-token "$ACCESS_TOKEN" \
    --region "$SSO_REGION" \
    --output json 2>/dev/null || echo "NO_ACCESS")

  if [ "$ROLES" = "NO_ACCESS" ]; then
    echo "  ⚠ Sin acceso a esta cuenta"
    echo "CUENTA=$ACCT | SIN ACCESO" >> "$RESULTS_FILE"
    continue
  fi

  # Tomar el primer rol disponible (preferir ViewOnlyAccess o ReadOnlyAccess)
  ROLE_NAME=$(echo "$ROLES" | python3 -c "
import sys, json
roles = json.load(sys.stdin)['roleList']
preferred = ['ViewOnlyAccess', 'ReadOnlyAccess', 'SecurityAudit']
for p in preferred:
    for r in roles:
        if r['roleName'] == p:
            print(r['roleName'])
            sys.exit(0)
if roles:
    print(roles[0]['roleName'])
else:
    print('NONE')
")

  if [ "$ROLE_NAME" = "NONE" ]; then
    echo "  ⚠ No hay roles disponibles"
    echo "CUENTA=$ACCT | SIN ROLES" >> "$RESULTS_FILE"
    continue
  fi

  echo "  Rol: $ROLE_NAME"

  # Obtener credenciales
  CREDS=$(aws sso get-role-credentials \
    --account-id "$ACCT" \
    --role-name "$ROLE_NAME" \
    --access-token "$ACCESS_TOKEN" \
    --region "$SSO_REGION" \
    --output json 2>/dev/null || echo "CRED_ERROR")

  if [ "$CREDS" = "CRED_ERROR" ]; then
    echo "  ⚠ Error obteniendo credenciales"
    echo "CUENTA=$ACCT | ERROR CREDENCIALES" >> "$RESULTS_FILE"
    continue
  fi

  export AWS_ACCESS_KEY_ID=$(echo "$CREDS" | python3 -c "import sys,json; print(json.load(sys.stdin)['roleCredentials']['accessKeyId'])")
  export AWS_SECRET_ACCESS_KEY=$(echo "$CREDS" | python3 -c "import sys,json; print(json.load(sys.stdin)['roleCredentials']['secretAccessKey'])")
  export AWS_SESSION_TOKEN=$(echo "$CREDS" | python3 -c "import sys,json; print(json.load(sys.stdin)['roleCredentials']['sessionToken'])")

  # ── Buscar en ACM (us-east-1) ──
  echo "  Buscando en ACM (us-east-1)..."
  ACM_CERTS=$(aws acm list-certificates --region us-east-1 --output json 2>/dev/null || echo '{"CertificateSummaryList":[]}')
  MATCHES=$(echo "$ACM_CERTS" | python3 -c "
import sys, json
certs = json.load(sys.stdin).get('CertificateSummaryList', [])
domain = '$DOMAIN'.lower()
for c in certs:
    dn = c.get('DomainName', '').lower()
    sans = [s.lower() for s in c.get('SubjectAlternativeNames', [])]
    if domain in dn or domain in ' '.join(sans) or any(domain in s for s in sans):
        print(f\"    ✓ ACM MATCH: {c['DomainName']} | ARN: {c['CertificateArn']}\")
" 2>/dev/null || true)

  if [ -n "$MATCHES" ]; then
    echo "$MATCHES"
    echo "CUENTA=$ACCT | ACM | $MATCHES" >> "$RESULTS_FILE"
  fi

  # ── Buscar en CloudFront ──
  echo "  Buscando en CloudFront..."
  CF_DISTROS=$(aws cloudfront list-distributions --output json 2>/dev/null || echo '{"DistributionList":{"Items":[]}}')
  CF_MATCHES=$(echo "$CF_DISTROS" | python3 -c "
import sys, json
data = json.load(sys.stdin)
items = data.get('DistributionList', {}).get('Items', []) or []
domain = '$DOMAIN'.lower()
for d in items:
    aliases = d.get('Aliases', {}).get('Items', []) or []
    for alias in aliases:
        if domain in alias.lower():
            cert = d.get('ViewerCertificate', {})
            cert_arn = cert.get('ACMCertificateArn', cert.get('Certificate', 'N/A'))
            print(f\"    ✓ CloudFront MATCH: {d['Id']} | Alias: {alias} | Cert: {cert_arn}\")
" 2>/dev/null || true)

  if [ -n "$CF_MATCHES" ]; then
    echo "$CF_MATCHES"
    echo "CUENTA=$ACCT | CLOUDFRONT | $CF_MATCHES" >> "$RESULTS_FILE"
  fi

  # ── Buscar en Route 53 ──
  echo "  Buscando en Route 53..."
  ZONES=$(aws route53 list-hosted-zones --output json 2>/dev/null || echo '{"HostedZones":[]}')
  ZONE_IDS=$(echo "$ZONES" | python3 -c "
import sys, json
zones = json.load(sys.stdin).get('HostedZones', [])
for z in zones:
    if 'ciencuadras.com' in z.get('Name', '').lower():
        print(z['Id'].split('/')[-1])
" 2>/dev/null || true)

  for ZID in $ZONE_IDS; do
    RECORDS=$(aws route53 list-resource-record-sets --hosted-zone-id "$ZID" --output json 2>/dev/null || echo '{"ResourceRecordSets":[]}')
    R53_MATCHES=$(echo "$RECORDS" | python3 -c "
import sys, json
records = json.load(sys.stdin).get('ResourceRecordSets', [])
domain = '$DOMAIN'.lower()
for r in records:
    if domain in r.get('Name', '').lower():
        print(f\"    ✓ Route53 MATCH: {r['Name']} | Type: {r['Type']} | Zone: $ZID\")
" 2>/dev/null || true)

    if [ -n "$R53_MATCHES" ]; then
      echo "$R53_MATCHES"
      echo "CUENTA=$ACCT | ROUTE53 | $R53_MATCHES" >> "$RESULTS_FILE"
    fi
  done

  # Limpiar env vars
  unset AWS_ACCESS_KEY_ID AWS_SECRET_ACCESS_KEY AWS_SESSION_TOKEN
done

echo ""
echo "=========================================="
echo "RESUMEN DE RESULTADOS:"
echo "=========================================="
grep -v "^$" "$RESULTS_FILE" | grep -v "SIN ACCESO\|SIN ROLES\|ERROR" || echo "No se encontraron coincidencias directas."
echo ""
echo "Archivo completo de resultados: $RESULTS_FILE"
