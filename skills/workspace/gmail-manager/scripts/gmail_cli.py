"""CLI de gmail-manager: barrido de correo por línea de negocio hacia el second brain.

Subcomandos:
- ``auth``   — autentica/renueva el token OAuth (solo lectura).
- ``labels`` — lista las etiquetas de la cuenta (y marca las de línea de negocio).
- ``scan``   — barre los mensajes (12 meses inicial o incremental), clasifica por criticidad e
               indexa los relevantes al vault vía ``obsidian_cli.py``.

Salida JSON por stdout. No imprime cuerpos de correos ni secretos. No hay proceso residente: cada
corrida termina (pensado para cron/launchd cada 6 h).
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import auth as auth_mod  # noqa: E402
import classifier as classifier_mod  # noqa: E402
import gmail_client as gc  # noqa: E402
import state as state_mod  # noqa: E402

# Mapeo etiqueta de línea de negocio → proyecto del vault.
LABEL_TO_PROJECT = {
    "Tribu Servicios Bolivar/Ciencuadras": "ciencuadras",
    "Tribu Servicios Bolivar/Libertador": "libertador",
    "Tribu Servicios Bolivar/Proyectiva": "proyectiva",
    "Tribu Servicios Bolivar/Notificador": "notificador-transversal",
    "Tribu Servicios Bolivar/RC": "relacionamiento-contextual",
}

OBSIDIAN_CLI = os.environ.get(
    "OBSIDIAN_CLI",
    str(Path(__file__).resolve().parents[2] / "obsidian-manager" / "scripts" / "obsidian_cli.py"),
)


def _slug(text: str, maxlen: int = 60) -> str:
    import re
    s = re.sub(r"[^a-zA-Z0-9]+", "-", text.lower()).strip("-")
    return s[:maxlen] or "correo"


def _user_email(service) -> str:
    try:
        return gc.get_profile(service).get("emailAddress", "")
    except Exception:
        return ""


def _write_thread_note(project: str, thread: dict, cls: classifier_mod.Classification,
                       body: str, *, dry_run: bool) -> bool:
    """Crea UNA nota de hilo en el proyecto. No escribe si el cuerpo está vacío.

    :return: True si se escribió (o se habría escrito en dry-run con cuerpo válido).
    """
    if not body.strip():
        return False
    fecha = datetime.now().strftime("%Y-%m-%d")
    title = f"Correo {fecha} {classifier_mod.redact(thread.get('subject', ''))}"[:90]
    if dry_run:
        return True
    cmd = [
        sys.executable, OBSIDIAN_CLI, "ingest", "-",
        "--title", title, "--folder", f"proyectos/{project}",
        "--project", project, "--tag", "correo", "--yes",
    ]
    res = subprocess.run(cmd, input=body, text=True, capture_output=True, check=False)
    return res.returncode == 0


def _cmd_auth(args) -> dict:
    settings = auth_mod.load_settings()
    auth_mod.get_credentials(settings)
    return {"authenticated": True, "token_path": str(settings.token_path)}


def _cmd_labels(args) -> dict:
    settings = auth_mod.load_settings()
    creds = auth_mod.get_credentials(settings, allow_interactive=False)
    service = gc.build_service(creds)
    labels = gc.list_labels(service)
    biz = gc.business_labels(labels)
    return {
        "total": len(labels),
        "business": [l["name"] for l in biz],
        "mapped": {n: LABEL_TO_PROJECT.get(n) for n in [l["name"] for l in biz]},
    }


def _cmd_scan(args) -> dict:
    settings = auth_mod.load_settings()
    creds = auth_mod.get_credentials(settings, allow_interactive=False)
    service = gc.build_service(creds)
    user_email = _user_email(service)

    labels = gc.list_labels(service)
    biz = {l["name"]: l["id"] for l in gc.business_labels(labels)}
    wanted = [args.label] if args.label else list(LABEL_TO_PROJECT.keys())

    st_path = state_mod.state_path()
    st = state_mod.load_state(st_path)
    summary: dict = {"per_label": {}, "dry_run": args.dry_run}

    # Se procesa POR HILO, no por mensaje: un threadId se indexa una sola vez en toda la corrida
    # (en la primera etiqueta donde aparezca), con UNA nota rica que resume el hilo por su mensaje
    # de mayor criticidad. Así un hilo largo o un correo con varias etiquetas no genera duplicados.
    threads_done: set[str] = set()

    for label_name in wanted:
        project = LABEL_TO_PROJECT.get(label_name)
        if not project or label_name not in biz:
            summary["per_label"][label_name] = {"error": "etiqueta no encontrada o sin mapeo"}
            continue
        after = state_mod.since_epoch_for(st, label_name, since_months=args.since_months)
        counts = {"hilos": 0, "alta": 0, "media": 0, "ignorados": 0,
                  "hilos_repetidos": 0, "sin_contenido": 0}
        try:
            # 1) Recolectar los threadIds distintos de la etiqueta (por sus mensajes).
            seen_threads_label: set[str] = set()
            for i, mid in enumerate(gc.search_message_ids(service, biz[label_name], after)):
                if args.max and len(seen_threads_label) >= args.max:
                    break
                meta = gc.get_message_meta(service, mid)
                tid = meta.get("threadId") or mid
                seen_threads_label.add(tid)

            # 2) Procesar cada hilo una sola vez.
            for tid in seen_threads_label:
                if tid in threads_done or state_mod.is_seen(st, label_name, tid):
                    counts["hilos_repetidos"] += 1
                    continue
                threads_done.add(tid)
                counts["hilos"] += 1
                thread = gc.get_thread(service, tid)
                cls, best_msg = classifier_mod.classify_thread(thread, user_email=user_email)
                if cls.level == "baja" or (args.only_high and cls.level != "alta"):
                    counts["ignorados"] += 1
                    if not args.dry_run:
                        state_mod.mark_seen(st, label_name, tid)
                    continue
                body = classifier_mod.summarize_thread(thread, cls, best_msg)
                wrote = _write_thread_note(project, thread, cls, body, dry_run=args.dry_run)
                if not wrote:
                    counts["sin_contenido"] += 1  # no se crea nota vacía
                else:
                    counts[cls.level] += 1
                if not args.dry_run:
                    state_mod.mark_seen(st, label_name, tid)
            if not args.dry_run:
                state_mod.complete_run(st, label_name)
        except Exception as exc:  # noqa: BLE001 - se reporta por etiqueta y se sigue
            summary["per_label"][label_name] = {**counts, "error": type(exc).__name__}
            continue
        summary["per_label"][label_name] = counts

    if not args.dry_run:
        state_mod.save_state(st_path, st)
    summary["total_hilos"] = sum(
        v.get("hilos", 0) for v in summary["per_label"].values() if isinstance(v, dict)
    )
    return summary


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="gmail_cli", description="Barrido de Gmail al second brain")
    p.add_argument("--pretty", action="store_true")
    sub = p.add_subparsers(dest="command", required=True)

    sub.add_parser("auth", help="autentica/renueva el token OAuth (solo lectura)")
    sub.add_parser("labels", help="lista etiquetas y su mapeo a proyectos")

    s = sub.add_parser("scan", help="barre correos e indexa por criticidad")
    s.add_argument("--label", default=None, help="una etiqueta específica (default: todas)")
    s.add_argument("--since-months", type=int, default=12, help="meses del primer barrido")
    s.add_argument("--incremental", action="store_true", help="usa el estado previo (informativo)")
    s.add_argument("--dry-run", action="store_true", help="no escribe al vault ni al estado")
    s.add_argument("--only-high", action="store_true",
                   help="solo escribe notas de criticidad alta (omite la bitácora de media)")
    s.add_argument("--max", type=int, default=0, help="tope de mensajes por etiqueta (0 = sin tope)")
    return p


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    if not hasattr(args, "dry_run"):
        args.dry_run = False
    try:
        if args.command == "auth":
            result = _cmd_auth(args)
        elif args.command == "labels":
            result = _cmd_labels(args)
        elif args.command == "scan":
            result = _cmd_scan(args)
        else:
            raise ValueError(f"comando desconocido: {args.command}")
    except Exception as exc:  # noqa: BLE001
        print(json.dumps({"error": type(exc).__name__, "message": str(exc)}), file=sys.stderr)
        return 1
    print(json.dumps(result, ensure_ascii=False, indent=2 if args.pretty else None))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
