#!/usr/bin/env python3
"""
Busca el dominio MassiveCienCuadrasApp.ciencuadras.com en ACM, CloudFront,
Route 53 y ALBs en todas las cuentas AWS proporcionadas via SSO.
"""
import subprocess
import json
import sys
import time
import os

DOMAIN = "MassiveCienCuadrasApp.ciencuadras.com"
SSO_REGION = "us-east-1"
SSO_START_URL = "https://solucionesbolivar.awsapps.com/start/"
RESULTS_FILE = "/tmp/domain-search-results.txt"

ACCOUNTS = [
    "565999949569",
    "691370287769",
    "505545527670",
    "290296201161",
    "038749957273",
    "935071422812",
    "055571516825",
    "437148509749",
    "722983015548",
    "694627937783",
    "397624050592",
    "892397120620",
    "857624955385",
    "272506905646",
    "130448862935",
    "996155636939",
    "966125231475",
    "674467843571",
    "982516576992",
    "467160885811",
    "507904767184",
    "658110252091",
    "906279163730",
    "709672348130",
    "826280447735",
    "775534688306",
    "464790332864",
    "858762616182",
    "610442843318",
    "243755603146",
    "944305913285",
    "014953646692",
    "145023099775",
    "180294192708",
    "012670877668",
    "213325653070",
    "901905860444",
    "149536466929",
    "383946777605",
    "805516213253",
    "751835846961",
]


def run_aws(args: list[str], env: dict | None = None) -> dict | None:
    """Execute an AWS CLI command and return parsed JSON or None on error."""
    cmd = ["aws"] + args + ["--output", "json"]
    merged_env = {**os.environ, **(env or {})}
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30, env=merged_env)
        if result.returncode == 0:
            return json.loads(result.stdout) if result.stdout.strip() else {}
        return None
    except (subprocess.TimeoutExpired, json.JSONDecodeError):
        return None


def get_sso_token() -> str:
    """Perform device authorization flow and return access token."""
    print(f"Conectando a AWS SSO ({SSO_START_URL})...")

    client = run_aws([
        "sso-oidc", "register-client",
        "--client-name", f"domain-search-{int(time.time())}",
        "--client-type", "public",
        "--region", SSO_REGION,
    ])
    if not client:
        print("Error: no se pudo registrar el cliente OIDC")
        sys.exit(1)

    client_id = client["clientId"]
    client_secret = client["clientSecret"]

    device = run_aws([
        "sso-oidc", "start-device-authorization",
        "--client-id", client_id,
        "--client-secret", client_secret,
        "--start-url", SSO_START_URL,
        "--region", SSO_REGION,
    ])
    if not device:
        print("Error: no se pudo iniciar la autorización")
        sys.exit(1)

    verify_url = device["verificationUriComplete"]
    device_code = device["deviceCode"]
    interval = device["interval"]
    expires_in = device["expiresIn"]

    print(f"\nAbre este enlace en tu navegador y aprueba el acceso:")
    print(f"  {verify_url}\n")
    subprocess.run(["open", verify_url], capture_output=True)
    print("Esperando que completes el login...")

    waited = 0
    while waited < expires_in:
        time.sleep(interval)
        waited += interval

        token_resp = run_aws([
            "sso-oidc", "create-token",
            "--client-id", client_id,
            "--client-secret", client_secret,
            "--grant-type", "urn:ietf:params:oauth:grant-type:device_code",
            "--device-code", device_code,
            "--region", SSO_REGION,
        ])

        if token_resp and "accessToken" in token_resp:
            print("✓ Login exitoso!")
            return token_resp["accessToken"]

    print("Error: tiempo de espera agotado.")
    sys.exit(1)


def get_account_creds(access_token: str, account_id: str) -> dict | None:
    """Get temporary credentials for an account via SSO."""
    roles = run_aws([
        "sso", "list-account-roles",
        "--account-id", account_id,
        "--access-token", access_token,
        "--region", SSO_REGION,
    ])

    if not roles or not roles.get("roleList"):
        return None

    preferred = ["ViewOnlyAccess", "ReadOnlyAccess", "SecurityAudit"]
    role_name = None
    for pref in preferred:
        for r in roles["roleList"]:
            if r["roleName"] == pref:
                role_name = pref
                break
        if role_name:
            break

    if not role_name:
        role_name = roles["roleList"][0]["roleName"]

    creds = run_aws([
        "sso", "get-role-credentials",
        "--account-id", account_id,
        "--role-name", role_name,
        "--access-token", access_token,
        "--region", SSO_REGION,
    ])

    if not creds or "roleCredentials" not in creds:
        return None

    rc = creds["roleCredentials"]
    return {
        "role": role_name,
        "AWS_ACCESS_KEY_ID": rc["accessKeyId"],
        "AWS_SECRET_ACCESS_KEY": rc["secretAccessKey"],
        "AWS_SESSION_TOKEN": rc["sessionToken"],
    }


def search_acm(env: dict, account_id: str) -> list[str]:
    """Search ACM certificates in us-east-1 for the domain."""
    findings = []
    certs = run_aws(["acm", "list-certificates", "--region", "us-east-1"], env=env)
    if not certs:
        return findings

    for cert in certs.get("CertificateSummaryList", []):
        domain_name = cert.get("DomainName", "").lower()
        if DOMAIN.lower() in domain_name:
            findings.append(f"  ✓ ACM: {cert['DomainName']} | ARN: {cert['CertificateArn']}")
            continue
        # Check SANs by describing the cert
        detail = run_aws([
            "acm", "describe-certificate",
            "--certificate-arn", cert["CertificateArn"],
            "--region", "us-east-1",
        ], env=env)
        if detail:
            sans = detail.get("Certificate", {}).get("SubjectAlternativeNames", [])
            for san in sans:
                if DOMAIN.lower() in san.lower():
                    findings.append(f"  ✓ ACM (SAN): {san} | ARN: {cert['CertificateArn']}")
                    break

    return findings


def search_cloudfront(env: dict) -> list[str]:
    """Search CloudFront distributions for the domain as CNAME."""
    findings = []
    distros = run_aws(["cloudfront", "list-distributions"], env=env)
    if not distros:
        return findings

    items = distros.get("DistributionList", {}).get("Items", []) or []
    for d in items:
        aliases = d.get("Aliases", {}).get("Items", []) or []
        for alias in aliases:
            if DOMAIN.lower() in alias.lower():
                cert = d.get("ViewerCertificate", {})
                cert_arn = cert.get("ACMCertificateArn", cert.get("Certificate", "N/A"))
                findings.append(
                    f"  ✓ CloudFront: {d['Id']} | Alias: {alias} | Cert: {cert_arn}"
                )

    return findings


def search_route53(env: dict) -> list[str]:
    """Search Route 53 for records matching the domain."""
    findings = []
    zones = run_aws(["route53", "list-hosted-zones"], env=env)
    if not zones:
        return findings

    for zone in zones.get("HostedZones", []):
        if "ciencuadras.com" in zone.get("Name", "").lower():
            zone_id = zone["Id"].split("/")[-1]
            records = run_aws([
                "route53", "list-resource-record-sets",
                "--hosted-zone-id", zone_id,
            ], env=env)
            if not records:
                continue
            for r in records.get("ResourceRecordSets", []):
                if DOMAIN.lower() in r.get("Name", "").lower():
                    findings.append(
                        f"  ✓ Route53: {r['Name']} | Type: {r['Type']} | Zone: {zone_id}"
                    )

    return findings


def search_alb(env: dict) -> list[str]:
    """Search ALB/ELB listeners for certificates with the domain."""
    findings = []
    lbs = run_aws(["elbv2", "describe-load-balancers", "--region", "us-east-1"], env=env)
    if not lbs:
        return findings

    for lb in lbs.get("LoadBalancers", []):
        lb_arn = lb["LoadBalancerArn"]
        listeners = run_aws([
            "elbv2", "describe-listeners",
            "--load-balancer-arn", lb_arn,
            "--region", "us-east-1",
        ], env=env)
        if not listeners:
            continue
        for listener in listeners.get("Listeners", []):
            for cert in listener.get("Certificates", []):
                cert_arn = cert.get("CertificateArn", "")
                if cert_arn:
                    cert_detail = run_aws([
                        "acm", "describe-certificate",
                        "--certificate-arn", cert_arn,
                        "--region", "us-east-1",
                    ], env=env)
                    if cert_detail:
                        sans = cert_detail.get("Certificate", {}).get("SubjectAlternativeNames", [])
                        domain_name = cert_detail.get("Certificate", {}).get("DomainName", "")
                        if DOMAIN.lower() in domain_name.lower() or any(DOMAIN.lower() in s.lower() for s in sans):
                            findings.append(
                                f"  ✓ ALB: {lb['LoadBalancerName']} | Listener: {listener.get('Port')} | Cert: {cert_arn}"
                            )

    return findings


def main():
    print(f"=== Búsqueda de dominio: {DOMAIN} ===")
    print(f"Cuentas a revisar: {len(ACCOUNTS)}\n")

    access_token = get_sso_token()

    all_results = []
    print(f"\nIniciando búsqueda en {len(ACCOUNTS)} cuentas...")
    print("=" * 60)

    for acct in ACCOUNTS:
        print(f"\n── Cuenta: {acct} ──")

        creds = get_account_creds(access_token, acct)
        if not creds:
            print("  ⚠ Sin acceso o sin roles disponibles")
            all_results.append(f"CUENTA={acct} | SIN ACCESO")
            continue

        print(f"  Rol: {creds['role']}")
        env = {
            "AWS_ACCESS_KEY_ID": creds["AWS_ACCESS_KEY_ID"],
            "AWS_SECRET_ACCESS_KEY": creds["AWS_SECRET_ACCESS_KEY"],
            "AWS_SESSION_TOKEN": creds["AWS_SESSION_TOKEN"],
            "AWS_DEFAULT_REGION": "us-east-1",
        }

        # Buscar en ACM
        print("  Buscando en ACM...")
        acm_findings = search_acm(env, acct)
        for f in acm_findings:
            print(f)
            all_results.append(f"CUENTA={acct} | {f.strip()}")

        # Buscar en CloudFront
        print("  Buscando en CloudFront...")
        cf_findings = search_cloudfront(env)
        for f in cf_findings:
            print(f)
            all_results.append(f"CUENTA={acct} | {f.strip()}")

        # Buscar en Route 53
        print("  Buscando en Route 53...")
        r53_findings = search_route53(env)
        for f in r53_findings:
            print(f)
            all_results.append(f"CUENTA={acct} | {f.strip()}")

        # Buscar en ALBs
        print("  Buscando en ALBs...")
        alb_findings = search_alb(env)
        for f in alb_findings:
            print(f)
            all_results.append(f"CUENTA={acct} | {f.strip()}")

        if not (acm_findings or cf_findings or r53_findings or alb_findings):
            print("  — No se encontró el dominio en esta cuenta")

    print("\n" + "=" * 60)
    print("RESUMEN DE RESULTADOS:")
    print("=" * 60)

    positive = [r for r in all_results if "✓" in r]
    if positive:
        for r in positive:
            print(r)
    else:
        print("No se encontraron coincidencias del dominio en ninguna cuenta.")

    # Guardar resultados
    with open(RESULTS_FILE, "w") as f:
        f.write("\n".join(all_results))
    print(f"\nResultados guardados en: {RESULTS_FILE}")


if __name__ == "__main__":
    main()
