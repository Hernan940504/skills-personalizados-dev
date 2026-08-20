#!/usr/bin/env python3
"""CLI de un prompt suelto contra la Gemini API, con salida determinista.

Uso:
    ./gemini-run.py "tu prompt"
    echo "tu prompt" | ./gemini-run.py
    ./gemini-run.py --raw "tu prompt"          # imprime el JSON completo

La API key sale de GEMINI_API_KEY o, si no está, del archivo .gemini-key junto
al script (gitignoreado). La key actual pertenece al proyecto Sandbox-Arquitectura
(426927376059): ahí se mide y se factura el consumo, no en ciencuadras-ia-prod.

Config por entorno:
    GEMINI_API_KEY   API key (formato AIza... o AQ....)
    GEMINI_MODEL     default: gemini-2.5-flash-lite

Nota: temperature=0 + seed=0 dan determinismo best-effort, no garantizado. El
backend puede cambiar de versión entre llamadas. No lo uses como oráculo exacto.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.request

MODEL = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash-lite")
TEMPERATURE = 0.0
SEED = 0

KEY_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".gemini-key")
ENDPOINT = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"


def api_key() -> str:
    key = os.environ.get("GEMINI_API_KEY", "").strip()
    if key:
        return key
    try:
        with open(KEY_FILE) as f:
            key = f.read().strip()
    except OSError:
        key = ""
    if not key:
        sys.exit(f"error: definí GEMINI_API_KEY o poné la key en {KEY_FILE}")
    return key


def generate(prompt: str, system: str | None, max_tokens: int, retries: int = 6) -> dict:
    body = {
        "contents": [{"role": "user", "parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": TEMPERATURE,
            "seed": SEED,
            "topP": 1.0,
            "maxOutputTokens": max_tokens,
        },
    }
    if system:
        body["systemInstruction"] = {"parts": [{"text": system}]}

    req = urllib.request.Request(
        ENDPOINT.format(model=MODEL),
        data=json.dumps(body).encode(),
        headers={"x-goog-api-key": api_key(), "Content-Type": "application/json; charset=utf-8"},
        method="POST",
    )

    for attempt in range(retries):
        try:
            with urllib.request.urlopen(req, timeout=120) as resp:
                return json.load(resp)
        except urllib.error.HTTPError as e:
            detail = e.read().decode(errors="replace")
            # 503/429 son capacidad, no credenciales: flash-lite los tira seguido.
            if e.code in (429, 503) and attempt < retries - 1:
                wait = 2 ** attempt
                print(f"[{e.code}] modelo saturado, reintento en {wait}s...", file=sys.stderr)
                time.sleep(wait)
                continue
            hint = ""
            if e.code in (401, 403):
                hint = "\nhint: key inválida o restringida para generativelanguage.googleapis.com"
            elif e.code == 404:
                hint = f"\nhint: el modelo '{MODEL}' no existe o no está disponible para esta key."
            elif e.code == 400:
                hint = "\nhint: request malformado; revisá el prompt o --max-tokens."
            sys.exit(f"error HTTP {e.code}: {detail}{hint}")
        except urllib.error.URLError as e:
            sys.exit(f"error de red: {e.reason}")

    sys.exit("error: el modelo sigue saturado tras varios reintentos.")


def extract_text(data: dict) -> str:
    candidates = data.get("candidates") or []
    if not candidates:
        blocked = data.get("promptFeedback", {}).get("blockReason")
        sys.exit(f"sin respuesta del modelo{f' (bloqueado: {blocked})' if blocked else ''}")

    cand = candidates[0]
    text = "".join(p.get("text", "") for p in cand.get("content", {}).get("parts") or [])

    if not text:
        reason = cand.get("finishReason", "desconocido")
        if reason == "MAX_TOKENS":
            sys.exit("error: se agotó maxOutputTokens antes de emitir texto. Subí --max-tokens")
        sys.exit(f"error: respuesta vacía (finishReason: {reason})")
    return text


def main() -> None:
    ap = argparse.ArgumentParser(description=f"Prompt suelto a {MODEL} (temperature=0, seed=0).")
    ap.add_argument("prompt", nargs="*", help="El prompt. Si se omite, se lee de stdin.")
    ap.add_argument("-s", "--system", help="System instruction.")
    ap.add_argument("--max-tokens", type=int, default=8192)
    ap.add_argument("--raw", action="store_true", help="Imprime el JSON completo de la respuesta.")
    args = ap.parse_args()

    prompt = " ".join(args.prompt).strip() or sys.stdin.read().strip()
    if not prompt:
        sys.exit("error: prompt vacío")

    data = generate(prompt, args.system, args.max_tokens)
    print(json.dumps(data, indent=2, ensure_ascii=False) if args.raw else extract_text(data))


if __name__ == "__main__":
    main()
