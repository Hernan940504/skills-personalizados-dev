#!/usr/bin/env bash
# Descubre proveedor cloud e IaC del proyecto para anclar el assessment.
# stdout: PROVIDER=, AZURE_DETECTED=, IAC=  (parseable)
# stderr: inventario legible.   Códigos PROVIDER: aws | gcp | hibrido | unknown
#
# La detección de proveedor mira IaC, manifiestos de dependencias y código fuente.
# Excluye documentación (.md) a propósito: un repo que solo *habla* de AWS/GCP en
# su doc no es una arquitectura desplegada en ese proveedor.

set -euo pipefail
ROOT="${1:-.}"

# ¿existe al menos un archivo que matchee la expresión find?
has() { find "$ROOT" -type f "$@" -not -path '*/.git/*' -not -path '*/node_modules/*' 2>/dev/null | head -1 | grep -q .; }

# grep recursivo, case-insensitive, ERE (alternancia portable), restringido a globs
# concretos: NUNCA busca en '*' para evitar falsos positivos de la documentación.
grep_in() {
  local pat="$1"; shift
  local inc=() g
  for g in "$@"; do inc+=(--include="$g"); done
  grep -rqiIE "$pat" "$ROOT" "${inc[@]}" --exclude-dir=.git --exclude-dir=node_modules 2>/dev/null
}

AWS=false; GCP=false; AZURE=false; IAC=()

# --- Tipos de IaC presentes (por nombre de archivo, preciso) ---
has -name '*.tf'                                   && IAC+=("terraform")
has -name 'cdk.json'                               && IAC+=("cdk")
has -name 'Pulumi.yaml'                            && IAC+=("pulumi")
has -name 'serverless.y*ml'                        && IAC+=("serverless")
{ has -name 'Dockerfile' || has -name 'docker-compose*.y*ml'; }            && IAC+=("docker")
{ has -name 'Chart.yaml' || grep_in '^kind:[[:space:]]' '*.yaml' '*.yml'; } && IAC+=("kubernetes")
{ has -path '*adr*' -name '*.md' || has -path '*decisions*' -name '*.md'; } && IAC+=("adr")
grep_in 'AWSTemplateFormatVersion' '*.yaml' '*.yml' '*.json'               && IAC+=("cloudformation")

# --- Proveedor: solo señales de infra/código, nunca documentación ---
{ grep_in 'provider "aws"' '*.tf' \
  || grep_in 'AWS::' '*.yaml' '*.yml' '*.json' \
  || grep_in '@aws-sdk|"aws-sdk"|aws-cdk-lib' 'package.json' \
  || grep_in 'boto3|aws-sdk' 'requirements.txt' 'pyproject.toml' 'Pipfile' \
  || grep_in 'boto3' '*.py' \
  || grep_in 'aws-sdk-go' 'go.mod'; } && AWS=true

{ grep_in 'provider "google"' '*.tf' \
  || grep_in '@google-cloud/|"google-cloud' 'package.json' \
  || grep_in 'google-cloud' 'requirements.txt' 'pyproject.toml' 'Pipfile' \
  || grep_in 'cloud.google.com/go' 'go.mod'; } && GCP=true

{ grep_in 'provider "azurerm"' '*.tf' \
  || has -name '*.bicep' \
  || grep_in 'schema.management.azure.com' '*.json' \
  || grep_in '@azure/|azure-sdk|azure-identity|azure-mgmt' 'package.json' 'requirements.txt' 'pyproject.toml' 'Pipfile'; } && AZURE=true

if   $AWS && $GCP; then PROVIDER=hibrido
elif $AWS;         then PROVIDER=aws
elif $GCP;         then PROVIDER=gcp
else                    PROVIDER=unknown
fi

IAC_CSV=$(IFS=,; echo "${IAC[*]:-}")
echo "PROVIDER=$PROVIDER"
echo "AZURE_DETECTED=$AZURE"
echo "IAC=$IAC_CSV"

# --- Feedback humano (stderr) ---
echo "[cloud-war] Proveedor: $PROVIDER | IaC: ${IAC_CSV:-ninguno} | Azure: $AZURE" >&2
$AZURE && echo "[cloud-war] AVISO: señales de Azure — fuera de cobertura del skill (solo AWS/GCP)." >&2
[ "$PROVIDER" = unknown ] && echo "[cloud-war] No se detectó proveedor por infra; pide al usuario la descripción." >&2
exit 0
