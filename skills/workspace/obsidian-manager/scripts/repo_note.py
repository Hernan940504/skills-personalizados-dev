"""Generador de notas de repositorio para el second brain.

Transforma los archivos fuente de un repositorio (OpenAPI ``api_spec.yaml``, ``build.gradle`` o
``pom.xml`` o ``package.json``, y ``README.md``) en una nota Markdown con frontmatter, endpoints,
integraciones/dependencias y correlación con la infraestructura. Es determinista y sin red: recibe
los archivos ya presentes en disco (los baja el agente vía la API de GitHub y los deja en una
carpeta), y produce el ``.md`` listo para ingerir con ``obsidian_cli.py``.

Diseño (por qué no llama a GitHub): mantener el script sin credenciales ni red (RNF-1/RNF-3 del
skill). La obtención de archivos es responsabilidad de quien tiene el acceso autenticado (el
agente por MCP, o un `gh`/token si se usa fuera). El script solo parsea y formatea.

Uso:
    python3 repo_note.py <repo_dir> <repo_full_name> --out <nota.md> \
        [--ecs <servicio>] [--tags a,b,c] [--project ciencuadras]

``<repo_dir>`` debe contener los archivos que existan del repo (cualquiera puede faltar):
``api_spec.yaml``/``openapi.yaml``/``swagger.json``, ``build.gradle``/``pom.xml``/``package.json``,
``README.md``, ``serverless.yml``, ``application.yaml``/``application.yml``/``.properties``.

Solo biblioteca estándar.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

# --- Detección de integraciones por dependencias (build.gradle / pom / package.json) ---------

# patrón de dependencia -> (categoría, etiqueta legible, recurso AWS asociado)
_DEP_SIGNALS: list[tuple[str, str, str, str]] = [
    (r"mysql-connector|mysql:mysql|com\.mysql", "datos", "MySQL (Aurora)", "www-rds-production-cluster"),
    (r"postgresql|postgres", "datos", "PostgreSQL", "RDS PostgreSQL"),
    (r"spring-boot-starter-data-jpa|hibernate", "datos", "JPA/Hibernate (ORM)", "-"),
    (r"elasticsearch|elastic\.clients|elastic-search", "datos", "ElasticSearch", "ES / pipeline logstash"),
    (r"redis|jedis|lettuce|redis-module", "datos", "Redis", "ElastiCache (Valkey)"),
    (r"dynamodb|aws-java-sdk-dynamodb|software\.amazon\.awssdk:dynamodb", "datos", "DynamoDB", "DynamoDB"),
    (r"aws-java-sdk-sqs|awssdk:sqs|amazon-sqs", "mensajeria", "SQS", "SQS"),
    (r"aws-java-sdk-sns|awssdk:sns", "mensajeria", "SNS", "SNS"),
    (r"aws-java-sdk-s3|awssdk:s3|amazon-s3", "datos", "S3", "S3"),
    (r"ssm-store|awssdk:ssm|simplesystemsmanagement", "config", "Parameter Store (SSM)", "SSM"),
    (r"secretsmanager", "config", "Secrets Manager", "Secrets Manager"),
    (r"firebase", "externo", "Firebase", "-"),
    (r"retrofit|okhttp|webclient|spring-boot-starter-webflux|feign", "http", "Cliente HTTP a otros servicios", "ms-internal ALB"),
    (r"kafka", "mensajeria", "Kafka", "-"),
    (r"mongodb|mongo-java", "datos", "MongoDB", "MongoDB"),
    (r"mapstruct", "util", "MapStruct (mapeo DTO)", "-"),
    (r"lombok", "util", "Lombok", "-"),
]

# Libs comunes de Ciencuadras (JFrog) que indican capacidades compartidas.
_COMMON_LIBS = [
    "ssm-store", "logger-module", "redis-module", "common-utilities", "elastic-search",
    "locations-tools", "commons-java-lib", "commons-node-lib",
]


def parse_dependencies(text: str) -> dict[str, list[str]]:
    """Extrae señales de integración desde un archivo de dependencias (gradle/pom/package.json).

    :param text: contenido del archivo de dependencias.
    :return: dict con categorías -> lista de etiquetas legibles (sin duplicar).
    """
    found: dict[str, list[str]] = {}
    for pattern, category, label, _aws in _DEP_SIGNALS:
        if re.search(pattern, text, re.IGNORECASE):
            found.setdefault(category, [])
            if label not in found[category]:
                found[category].append(label)
    return found


def aws_resources(text: str) -> list[str]:
    """Devuelve los recursos AWS inferidos de las dependencias, sin duplicar."""
    res: list[str] = []
    for pattern, _cat, label, aws in _DEP_SIGNALS:
        if aws != "-" and re.search(pattern, text, re.IGNORECASE):
            entry = f"{label} → {aws}"
            if entry not in res:
                res.append(entry)
    return res


def common_libs(text: str) -> list[str]:
    """Detecta las libs comunes CC presentes en el archivo de dependencias."""
    return [lib for lib in _COMMON_LIBS if lib in text]


def detect_stack(deps_text: str, filename: str) -> str:
    """Infiere el stack del repo a partir del archivo de dependencias."""
    if "build.gradle" in filename or "pom.xml" in filename:
        boot = re.search(r"springframework\.boot['\"]?\s+version\s+['\"]([0-9.]+)", deps_text)
        java = re.search(r"sourceCompatibility\s*=\s*['\"]?([0-9]+)", deps_text)
        parts = ["Java"]
        if java:
            parts[0] = f"Java {java.group(1)}"
        parts.append("Spring Boot" + (f" {boot.group(1)}" if boot else ""))
        return ", ".join(parts) + (" (Gradle)" if "gradle" in filename else " (Maven)")
    if "package.json" in filename:
        return "Node.js / TypeScript"
    return "desconocido"


# --- OpenAPI --------------------------------------------------------------------------------

_HTTP_METHODS = {"get", "post", "put", "delete", "patch"}


def parse_openapi_paths(spec: dict[str, Any]) -> list[dict[str, str]]:
    """Extrae endpoints de un OpenAPI ya parseado (dict).

    :param spec: OpenAPI como dict.
    :return: lista de ``{method, path, summary, request, response}``.
    """
    endpoints: list[dict[str, str]] = []
    paths = spec.get("paths", {})
    for path, methods in paths.items():
        if not isinstance(methods, dict):
            continue
        for method, op in methods.items():
            if method.lower() not in _HTTP_METHODS or not isinstance(op, dict):
                continue
            endpoints.append({
                "method": method.upper(),
                "path": path,
                "summary": op.get("summary") or op.get("operationId") or "",
                "request": _ref_name(_request_schema(op)),
                "response": _ref_name(_response_schema(op)),
            })
    return endpoints


def _request_schema(op: dict[str, Any]) -> str | None:
    body = op.get("requestBody", {})
    try:
        return body["content"]["application/json"]["schema"].get("$ref")
    except (KeyError, AttributeError, TypeError):
        return None


def _response_schema(op: dict[str, Any]) -> str | None:
    responses = op.get("responses", {})
    for code in ("200", 200, "201", 201):
        resp = responses.get(code)
        if isinstance(resp, dict):
            try:
                return resp["content"]["application/json"]["schema"].get("$ref")
            except (KeyError, AttributeError, TypeError):
                continue
    return None


def _ref_name(ref: str | None) -> str:
    """Devuelve el nombre corto de un ``$ref`` de OpenAPI, o cadena vacía."""
    if not ref:
        return ""
    return ref.rsplit("/", 1)[-1]


def is_proxy_spec(endpoints: list[dict[str, str]]) -> bool:
    """Indica si el OpenAPI es un proxy genérico ``{proxy+}`` (endpoints reales en el código)."""
    if not endpoints:
        return False
    return all("{proxy" in e["path"] or "proxy+" in e["path"] for e in endpoints)


# --- Generación de la nota ------------------------------------------------------------------


def build_note(
    repo_dir: Path, repo_full_name: str, *, ecs: str | None, tags: list[str], project: str
) -> str:
    """Construye el cuerpo Markdown de la nota del repo a partir de sus archivos.

    :param repo_dir: carpeta con los archivos fuente del repo.
    :param repo_full_name: ``org/repo``.
    :param ecs: servicio ECS asociado (opcional).
    :param tags: tags para el frontmatter.
    :param project: proyecto del vault.
    :return: nota Markdown (frontmatter + cuerpo).
    """
    repo_name = repo_full_name.rsplit("/", 1)[-1]
    deps_file, deps_text = _read_first(repo_dir, ["build.gradle", "pom.xml", "package.json"])
    readme = _read_optional(repo_dir, "README.md")
    spec, spec_name = _read_openapi(repo_dir)

    stack = detect_stack(deps_text, deps_file) if deps_text else "desconocido"
    deps = parse_dependencies(deps_text) if deps_text else {}
    aws = aws_resources(deps_text) if deps_text else []
    libs = common_libs(deps_text) if deps_text else []

    endpoints = parse_openapi_paths(spec) if spec else []
    proxy = is_proxy_spec(endpoints)

    fm = {
        "title": f"Repo — {repo_name}",
        "repo": repo_full_name,
        "stack": stack,
        "fecha": "generado por repo_note.py",
        "tags": ["github", "ciencuadras", "repo"] + tags,
        "project": project,
    }
    if ecs:
        fm["servicio_ecs"] = ecs

    lines: list[str] = [f"# {repo_name}", ""]

    # Descripción desde el README (primer párrafo tras un encabezado de descripción).
    desc = _extract_description(readme)
    if desc:
        lines += ["## Función", desc, ""]

    lines += ["## Stack", stack, ""]

    # Endpoints — prioridad: OpenAPI con rutas reales > sección del README (rica) > tabla mínima > fallback.
    readme_section = extract_readme_endpoints_section(readme)
    if endpoints and not proxy:
        lines += ["## Endpoints", "",
                  "_Fuente: OpenAPI (`api_spec.yaml`)._", "",
                  "| Método | Ruta | Función | Request | Response |",
                  "|---|---|---|---|---|"]
        for e in sorted(endpoints, key=lambda x: (x["path"], x["method"])):
            lines.append(
                f"| {e['method']} | `{e['path']}` | {e['summary']} | {e['request'] or '—'} | {e['response'] or '—'} |"
            )
        lines.append("")
        # Si además el README documenta endpoints con más detalle, se incorpora tras la tabla.
        if readme_section:
            lines += ["### Detalle de endpoints (del README)", "", readme_section, ""]
    elif readme_section:
        # OpenAPI ausente o proxy genérico: la mejor fuente es el README, incrustado tal cual.
        nota = ("_Fuente: README del repo. El OpenAPI usa proxy genérico `{proxy+}`._"
                if proxy else "_Fuente: README del repo (sin OpenAPI de rutas)._")
        lines += ["## Endpoints", "", nota, "", readme_section, ""]
    elif proxy:
        lines += ["## Endpoints",
                  "El OpenAPI usa proxy genérico `{proxy+}` y el README no documenta rutas; "
                  "los endpoints reales están en el código (controllers). Ver repo.", ""]
    elif deps_text and "package.json" in deps_file:
        lines += ["## Endpoints",
                  "Repo Node/Lambda — endpoints definidos por `serverless.yml`/handlers (ver repo).", ""]
    else:
        lines += ["## Endpoints", "Sin OpenAPI ni sección de endpoints en README "
                  "(lib/infra/frontend o endpoints en código).", ""]

    # Integraciones
    lines += ["## Integraciones e interacciones (evidencia: dependencias)", ""]
    if aws:
        lines += ["**Recursos / infra:**"] + [f"- {a}" for a in aws] + [""]
    http = deps.get("http")
    externos = deps.get("externo")
    if http:
        lines += ["**Consume otros servicios (HTTP):** " + ", ".join(http), ""]
    if externos:
        lines += ["**Sistemas externos:** " + ", ".join(externos), ""]
    if libs:
        lines += ["**Libs comunes CC (JFrog):** " + ", ".join(libs), ""]
    if not (aws or http or externos or libs):
        lines += ["_No se detectaron integraciones por dependencias (revisar código si aplica)._", ""]

    # Correlación con infra
    lines += ["## Correlación con infra"]
    if ecs:
        lines.append(f"- **ECS**: `{ecs}`. Ver [[contexto-aws-cuenta-legada-ciencuadras-290296201161]].")
    lines.append("- Inventario general de repos: [[repositorios-github-ciencuadras-y-comunes]].")
    lines += ["", "## Enlaces",
              "[[_indice|Índice de repos]] · [[_contexto-ciencuadras]] · "
              "[[contexto-aws-cuenta-legada-ciencuadras-290296201161]]"]

    body = "\n".join(lines) + "\n"
    return _dump_frontmatter(fm) + body


# --- Helpers de lectura ---------------------------------------------------------------------


def _read_first(repo_dir: Path, names: list[str]) -> tuple[str, str]:
    """Devuelve ``(nombre, contenido)`` del primer archivo que exista, o ``('', '')``."""
    for name in names:
        p = repo_dir / name
        if p.exists():
            return name, p.read_text(encoding="utf-8", errors="replace")
    return "", ""


def _read_optional(repo_dir: Path, name: str) -> str:
    p = repo_dir / name
    return p.read_text(encoding="utf-8", errors="replace") if p.exists() else ""


def _read_openapi(repo_dir: Path) -> tuple[dict[str, Any] | None, str]:
    """Lee y parsea el OpenAPI del repo (yaml mínimo o json). Devuelve ``(spec|None, nombre)``."""
    for name in ("api_spec.yaml", "openapi.yaml", "openapi.yml", "swagger.json", "api_spec.json"):
        p = repo_dir / name
        if not p.exists():
            continue
        text = p.read_text(encoding="utf-8", errors="replace")
        if name.endswith(".json"):
            try:
                return json.loads(text), name
            except json.JSONDecodeError:
                return None, name
        parsed = _mini_yaml_openapi(text)
        return parsed, name
    return None, ""


def _mini_yaml_openapi(text: str) -> dict[str, Any] | None:
    """Parser YAML mínimo enfocado en extraer ``paths`` y sus métodos/summary/refs.

    No es un parser YAML general: reconoce la estructura de un OpenAPI de API Gateway
    (rutas en 2 espacios, métodos en 4, campos en 6+). Suficiente para el inventario.
    """
    lines = text.replace("\r\n", "\n").split("\n")
    paths: dict[str, Any] = {}
    in_paths = False
    cur_path = None
    cur_method = None
    for raw in lines:
        if raw.strip().startswith("#") or not raw.strip():
            continue
        indent = len(raw) - len(raw.lstrip(" "))
        stripped = raw.strip()
        if indent == 0:
            in_paths = stripped.rstrip(":") == "paths"
            continue
        if not in_paths:
            continue
        if indent == 2 and stripped.endswith(":"):
            cur_path = stripped[:-1].strip().strip("'\"")
            paths[cur_path] = {}
            cur_method = None
        elif indent == 4 and stripped.endswith(":") and cur_path is not None:
            method = stripped[:-1].strip()
            if method in _HTTP_METHODS:
                cur_method = method
                paths[cur_path][method] = {"responses": {}}
            else:
                cur_method = None
        elif cur_path is not None and cur_method is not None:
            m = re.match(r"(summary|operationId):\s*(.+)$", stripped)
            if m:
                key = "summary" if m.group(1) == "summary" else "operationId"
                paths[cur_path][cur_method][key] = m.group(2).strip().strip("'\"")
    if not paths:
        return None
    return {"paths": paths}


def _extract_description(readme: str) -> str:
    """Extrae el primer párrafo de descripción del README.

    Tolera encabezados con formato variado: ``## Descripción``, ``>## Descripción:``,
    ``-- Descripción --``. Devuelve el texto limpio del primer párrafo.
    """
    if not readme:
        return ""
    # Encabezado "Descripción" con posibles > : y adornos, hasta el siguiente heading/línea de guiones.
    m = re.search(
        r"#+\s*>?\s*Descripci[oó]n\s*:?\s*\n+(.+?)(\n\s*\n|\n-- |\n#|\n>|\Z)",
        readme, re.IGNORECASE | re.DOTALL,
    )
    if m and m.group(1).strip():
        return _clean_paragraph(m.group(1))
    # fallback: primer párrafo tras el título H1.
    m = re.search(r"^#\s+.+?\n+(.+?)(\n\s*\n|\n##|\Z)", readme, re.DOTALL)
    if m and m.group(1).strip():
        return _clean_paragraph(m.group(1))
    return ""


def _clean_paragraph(text: str) -> str:
    """Colapsa espacios y quita líneas de adorno (``--``) de un párrafo."""
    cleaned = re.sub(r"-{2,}", " ", text)
    return " ".join(cleaned.split())


def extract_readme_endpoints_section(readme: str) -> str:
    """Extrae la sección de "Endpoints" del README tal cual (preservando su riqueza).

    Devuelve el bloque Markdown entre el encabezado "Endpoints" y el siguiente encabezado de
    sección de primer nivel del README (Gestión de Logs / Versionamiento / Autores / Seguridad
    posterior / etc.), normalizando los separadores de adorno.

    :param readme: contenido del README.
    :return: bloque Markdown de endpoints, o cadena vacía si no hay sección.
    """
    if not readme:
        return ""
    # Localiza el encabezado de Endpoints (tolerando > antes o después de #, :, adornos).
    start = re.search(r"(?:>\s*)?#+\s*(?:>\s*)?Endpoints\s*:?\s*\n", readme, re.IGNORECASE)
    if not start:
        return ""
    rest = readme[start.end():]
    # Corta en la siguiente sección de nivel "mayor" conocida (el > puede ir antes o después de #).
    stop = re.search(
        r"\n(?:>\s*)?#+\s*(?:>\s*)?(Gesti[oó]n de Logs|Versionamiento|Autores|Licencia|"
        r"Contribuciones|Dependencias|Pruebas|Seguridad)\b",
        rest, re.IGNORECASE,
    )
    section = rest[: stop.start()] if stop else rest
    # Normaliza líneas de adorno "-- ----" a separadores limpios y recorta.
    section = re.sub(r"\n-{2,}[ -]*\n", "\n\n", section)
    section = re.sub(r"\n{3,}", "\n\n", section).strip()
    # Cota de tamaño para no incrustar READMEs gigantes completos (deja el enlace al repo).
    max_chars = 12000
    if len(section) > max_chars:
        section = section[:max_chars].rstrip() + "\n\n… (sección truncada; ver README del repo)"
    return section


def _dump_frontmatter(fm: dict[str, Any]) -> str:
    """Serializa el frontmatter YAML (compatible con frontmatter.py del skill)."""
    out = ["---"]
    for k, v in fm.items():
        if isinstance(v, list):
            out.append(f"{k}: [{', '.join(str(x) for x in v)}]")
        else:
            out.append(f"{k}: {v}")
    out.append("---")
    return "\n".join(out) + "\n"


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(prog="repo_note", description="Genera nota de repo para el brain")
    parser.add_argument("repo_dir")
    parser.add_argument("repo_full_name")
    parser.add_argument("--out", required=True)
    parser.add_argument("--ecs")
    parser.add_argument("--tags", default="")
    parser.add_argument("--project", default="ciencuadras")
    args = parser.parse_args(argv)

    tags = [t.strip() for t in args.tags.split(",") if t.strip()]
    note = build_note(Path(args.repo_dir), args.repo_full_name,
                      ecs=args.ecs, tags=tags, project=args.project)
    Path(args.out).write_text(note, encoding="utf-8")
    # Reporta un resumen a stdout (JSON) para el agente.
    print(json.dumps({"out": args.out, "bytes": len(note)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
