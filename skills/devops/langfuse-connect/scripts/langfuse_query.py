#!/usr/bin/env python3
"""
langfuse_query.py — Consulta la API pública de Langfuse para validar el consumo de LLM
(modelo exacto, tokens de entrada/salida, costo y factor de amplificación por traza).

Sin dependencias externas (solo stdlib). Autenticación HTTP Basic (public_key:secret_key).

Credenciales por variables de entorno:
  LANGFUSE_HOST         p.ej. https://cloud.langfuse.com  o el self-hosted de MIA
  LANGFUSE_PUBLIC_KEY   pk-lf-...
  LANGFUSE_SECRET_KEY   sk-lf-...

Uso directo:
  export LANGFUSE_HOST=... LANGFUSE_PUBLIC_KEY=... LANGFUSE_SECRET_KEY=...
  python3 langfuse_query.py ping
  python3 langfuse_query.py validate --days 30
  python3 langfuse_query.py daily    --days 90
  python3 langfuse_query.py models   --days 30 --grep gemini
O vía wrapper:  bash scripts/langfuse.sh mia-ciencuadras validate --days 30
"""
import os, sys, json, base64, argparse, datetime, subprocess, urllib.request, urllib.parse, urllib.error
from collections import defaultdict

# ---------------------------------------------------------------- infra
def cfg():
    host = os.environ.get("LANGFUSE_HOST")
    pk   = os.environ.get("LANGFUSE_PUBLIC_KEY")
    sk   = os.environ.get("LANGFUSE_SECRET_KEY")
    missing = [k for k, v in [("LANGFUSE_HOST", host), ("LANGFUSE_PUBLIC_KEY", pk),
                              ("LANGFUSE_SECRET_KEY", sk)] if not v]
    if missing:
        sys.exit("Faltan variables: " + ", ".join(missing) +
                 "\nCárgalas (export ...) o usa: bash scripts/langfuse.sh <proyecto> <comando>")
    return host.rstrip("/"), pk, sk

def _curl_get(url, auth):
    """Transporte de respaldo vía curl (usa el trust store del sistema, incluida la CA
    corporativa como Netskope). Devuelve (status:int, body:str)."""
    try:
        out = subprocess.run(
            ["curl", "-sS", "--max-time", "90",
             "-H", "Authorization: Basic " + auth, "-H", "Accept: application/json",
             "-w", "\nHTTPSTATUS:%{http_code}", url],
            capture_output=True, text=True)
    except FileNotFoundError:
        sys.exit("Fallo TLS en Python y 'curl' no está disponible para el respaldo.")
    if out.returncode != 0:
        sys.exit(f"curl falló ({out.returncode}): {out.stderr.strip()[:300]}")
    body, _, status = out.stdout.rpartition("\nHTTPSTATUS:")
    return int(status or 0), body

def _req(host, pk, sk, path, params=None):
    url = host + path
    if params:
        url += "?" + urllib.parse.urlencode({k: v for k, v in params.items() if v is not None})
    auth = base64.b64encode(f"{pk}:{sk}".encode()).decode()
    req = urllib.request.Request(url, headers={"Authorization": "Basic " + auth,
                                               "Accept": "application/json"})
    status, body = None, None
    try:
        with urllib.request.urlopen(req, timeout=90) as r:
            status, body = r.status, r.read().decode()
    except urllib.error.HTTPError as e:
        status, body = e.code, e.read().decode()          # respuesta HTTP real (4xx/5xx)
    except urllib.error.URLError:
        status, body = _curl_get(url, auth)               # SSL/red -> respaldo curl
    if status and status >= 400:
        sys.exit(f"HTTP {status} en {path}\n{body[:400]}")
    try:
        return json.loads(body)
    except (json.JSONDecodeError, TypeError):
        sys.exit(f"Respuesta no-JSON de {path}:\n{(body or '')[:300]}")

def paginate(host, pk, sk, path, params):
    params = dict(params); params.setdefault("limit", 100)
    page, out = 1, []
    while True:
        params["page"] = page
        d = _req(host, pk, sk, path, params)
        data = d.get("data", [])
        out += data
        meta = d.get("meta", {}) or {}
        total_pages = meta.get("totalPages") or 1
        if page >= total_pages or not data:
            break
        page += 1
    return out

def window(days, frm, to):
    end = datetime.datetime.strptime(to, "%Y-%m-%d") if to else datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None)
    start = datetime.datetime.strptime(frm, "%Y-%m-%d") if frm else end - datetime.timedelta(days=days)
    iso = lambda d: d.strftime("%Y-%m-%dT%H:%M:%SZ")
    return start, end, iso(start), iso(end)

def money(v): return "${:,.2f}".format(v or 0)
def num(v):   return "{:,.0f}".format(v or 0)

# ---------------------------------------------------------------- data
def fetch_daily(host, pk, sk, iso_start, iso_end):
    """/api/public/metrics/daily -> filas por día con usage[] por modelo."""
    return paginate(host, pk, sk, "/api/public/metrics/daily",
                    {"fromTimestamp": iso_start, "toTimestamp": iso_end})

def aggregate_models(rows):
    per = defaultdict(lambda: {"in": 0, "out": 0, "total": 0, "obs": 0, "cost": 0.0})
    traces = obs_total = 0
    cost_total = 0.0
    per_day = []
    for row in rows:
        t = row.get("countTraces", 0) or 0
        o = row.get("countObservations", 0) or 0
        c = row.get("totalCost", 0) or 0
        traces += t; obs_total += o; cost_total += c
        per_day.append({"date": row.get("date"), "traces": t, "obs": o, "cost": c})
        for u in row.get("usage", []) or []:
            m = u.get("model") or "(sin modelo)"
            p = per[m]
            p["in"]    += u.get("inputUsage", 0) or 0
            p["out"]   += u.get("outputUsage", 0) or 0
            p["total"] += u.get("totalUsage", 0) or 0
            p["obs"]   += u.get("countObservations", 0) or 0
            p["cost"]  += u.get("totalCost", 0) or 0
    return per, traces, obs_total, cost_total, per_day

# ---------------------------------------------------------------- commands
def cmd_ping(a):
    host, pk, sk = cfg()
    d = _req(host, pk, sk, "/api/public/projects")
    projs = d.get("data", d)
    print("✓ Conexión OK a", host)
    if isinstance(projs, list):
        for p in projs:
            print("   proyecto:", p.get("name"), "|", p.get("id"))

def cmd_daily(a):
    host, pk, sk = cfg()
    s, e, iss, ise = window(a.days, a.frm, a.to)
    rows = fetch_daily(host, pk, sk, iss, ise)
    print(f"# Ventana {iss} -> {ise}  ({len(rows)} días con datos)")
    print(f"{'fecha':12s} {'trazas':>9s} {'generac.':>9s} {'costo USD':>12s}")
    _, _, _, _, per_day = aggregate_models(rows)
    for d in sorted(per_day, key=lambda x: x["date"] or ""):
        print(f"{(d['date'] or '')[:10]:12s} {num(d['traces']):>9s} {num(d['obs']):>9s} {money(d['cost']):>12s}")

def cmd_models(a):
    host, pk, sk = cfg()
    s, e, iss, ise = window(a.days, a.frm, a.to)
    rows = fetch_daily(host, pk, sk, iss, ise)
    per, traces, obs, cost, _ = aggregate_models(rows)
    items = sorted(per.items(), key=lambda kv: -kv[1]["cost"])
    if a.grep:
        items = [x for x in items if a.grep.lower() in x[0].lower()]
    print(f"# Modelos {iss} -> {ise}")
    print(f"{'modelo':38s} {'generac.':>10s} {'tok in':>13s} {'tok out':>13s} {'costo USD':>12s}")
    for m, p in items:
        print(f"{m[:38]:38s} {num(p['obs']):>10s} {num(p['in']):>13s} {num(p['out']):>13s} {money(p['cost']):>12s}")

def cmd_validate(a):
    host, pk, sk = cfg()
    s, e, iss, ise = window(a.days, a.frm, a.to)
    rows = fetch_daily(host, pk, sk, iss, ise)
    per, traces, obs, cost, per_day = aggregate_models(rows)

    print("=" * 72)
    print(f"VALIDACIÓN LANGFUSE  ·  {iss[:10]} -> {ise[:10]}")
    print("=" * 72)
    print(f"Trazas (conversaciones): {num(traces)}")
    print(f"Generaciones LLM:        {num(obs)}")
    amp = (obs / traces) if traces else 0
    print(f"Amplificación (gen/traza): {amp:.2f}")
    print(f"Costo total:             {money(cost)}")

    # split gemini vs otros
    def is_gem(m): return "gemini" in m.lower()
    gem = {"obs": 0, "in": 0, "out": 0, "cost": 0.0}
    oth = {"obs": 0, "in": 0, "out": 0, "cost": 0.0}
    for m, p in per.items():
        tgt = gem if is_gem(m) else oth
        for k in ("obs", "in", "out", "cost"):
            tgt[k] += p[k]
    print("\n-- Por familia de modelo --")
    print(f"{'familia':16s} {'generac.':>10s} {'tok in':>13s} {'tok out':>13s} {'costo USD':>12s}")
    print(f"{'Gemini':16s} {num(gem['obs']):>10s} {num(gem['in']):>13s} {num(gem['out']):>13s} {money(gem['cost']):>12s}")
    print(f"{'Otros (GPT…)':16s} {num(oth['obs']):>10s} {num(oth['in']):>13s} {num(oth['out']):>13s} {money(oth['cost']):>12s}")

    print("\n-- Detalle por modelo --")
    print(f"{'modelo':38s} {'generac.':>10s} {'tok total':>14s} {'costo USD':>12s}")
    for m, p in sorted(per.items(), key=lambda kv: -kv[1]["cost"]):
        print(f"{m[:38]:38s} {num(p['obs']):>10s} {num(p['total']):>14s} {money(p['cost']):>12s}")

    # amplificación primera vs segunda mitad del periodo
    days_sorted = sorted([d for d in per_day if d["date"]], key=lambda x: x["date"])
    if len(days_sorted) >= 4:
        h = len(days_sorted) // 2
        def amp_of(seg):
            tt = sum(d["traces"] for d in seg); oo = sum(d["obs"] for d in seg)
            return (oo / tt) if tt else 0, tt, oo
        a1, t1, o1 = amp_of(days_sorted[:h])
        a2, t2, o2 = amp_of(days_sorted[h:])
        print("\n-- Amplificación en el tiempo (gen/traza) --")
        print(f"  1ª mitad ({days_sorted[0]['date'][:10]}…): {a1:.2f}   ({num(o1)} gen / {num(t1)} trazas)")
        print(f"  2ª mitad (…{days_sorted[-1]['date'][:10]}): {a2:.2f}   ({num(o2)} gen / {num(t2)} trazas)")
        if a1:
            print(f"  cambio: {100*(a2-a1)/a1:+.0f}%")

    if a.gcp_calls:
        print("\n-- Confrontación con GCP --")
        print(f"  Llamadas Gemini (GCP, GenerateContent): {num(a.gcp_calls)}")
        print(f"  Generaciones Gemini (Langfuse):         {num(gem['obs'])}")
        if gem["obs"]:
            print(f"  Cobertura Langfuse/GCP: {100*gem['obs']/a.gcp_calls:.0f}%  (ideal ~100% si toda llamada pasa por Langfuse)")

# ---------------------------------------------------------------- main
def main():
    ap = argparse.ArgumentParser(description="Consulta Langfuse para validar consumo de LLM de MIA.")
    sub = ap.add_subparsers(dest="cmd", required=True)
    def common(p):
        p.add_argument("--days", type=int, default=30, help="ventana en días (por defecto 30)")
        p.add_argument("--from", dest="frm", help="fecha inicio YYYY-MM-DD (anula --days)")
        p.add_argument("--to", help="fecha fin YYYY-MM-DD")
    p = sub.add_parser("ping", help="probar credenciales/conexión");
    p = sub.add_parser("daily", help="serie diaria de trazas/generaciones/costo"); common(p)
    p = sub.add_parser("models", help="tabla por modelo"); common(p); p.add_argument("--grep", help="filtrar modelos por texto")
    p = sub.add_parser("validate", help="informe de validación (modelo, tokens, costo, amplificación)")
    common(p); p.add_argument("--gcp-calls", type=int, help="nº de llamadas Gemini en GCP para confrontar")
    args = ap.parse_args()
    {"ping": cmd_ping, "daily": cmd_daily, "models": cmd_models, "validate": cmd_validate}[args.cmd](args)

if __name__ == "__main__":
    main()
