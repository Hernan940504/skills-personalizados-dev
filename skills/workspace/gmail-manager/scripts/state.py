"""Estado incremental del barrido de correo, por etiqueta.

Persiste en ``~/.config/gmail-skill/state.json`` (override por ``GMAIL_STATE_PATH``) la marca de
tiempo de la última ejecución exitosa y una ventana acotada de ids ya vistos, para no reprocesar ni
duplicar notas. El primer barrido usa 12 meses; los siguientes, desde la última corrida con solape.
"""

from __future__ import annotations

import json
import os
import time
from pathlib import Path

_DEFAULT_STATE = Path.home() / ".config" / "gmail-skill" / "state.json"

SECONDS_PER_DAY = 86400
OVERLAP_SECONDS = 600  # 10 min de solape para no perder correos en el borde
SEEN_MAX = 2000  # tope de ids recordados por etiqueta (poda FIFO)


def state_path(env: dict[str, str] | None = None) -> Path:
    """Ruta del archivo de estado (override por ``GMAIL_STATE_PATH``)."""
    env = env if env is not None else dict(os.environ)
    return Path(env.get("GMAIL_STATE_PATH", str(_DEFAULT_STATE))).expanduser()


def load_state(path: Path) -> dict:
    """Carga el estado; devuelve estructura vacía si no existe o está corrupto."""
    if not path.exists():
        return {"labels": {}}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(data, dict) or "labels" not in data:
            return {"labels": {}}
        return data
    except (json.JSONDecodeError, OSError):
        return {"labels": {}}


def save_state(path: Path, state: dict) -> None:
    """Escribe el estado con permisos 0600, creando el directorio si falta."""
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(path)
    try:
        os.chmod(path, 0o600)
    except OSError:
        pass


def since_epoch_for(state: dict, label: str, *, since_months: int = 12,
                    now: float | None = None) -> int:
    """Calcula el epoch ``after:`` a consultar para una etiqueta.

    Primera vez: ``now - since_months``. Incremental: ``last_run - solape``.

    :param state: estado cargado.
    :param label: nombre de la etiqueta.
    :param since_months: meses hacia atrás en el primer barrido.
    :param now: epoch actual (inyectable en tests).
    :return: epoch entero para el filtro ``after:``.
    """
    now = now if now is not None else time.time()
    entry = state.get("labels", {}).get(label)
    if not entry or "last_run_epoch" not in entry:
        return int(now - since_months * 30 * SECONDS_PER_DAY)
    return int(entry["last_run_epoch"] - OVERLAP_SECONDS)


def is_seen(state: dict, label: str, message_id: str) -> bool:
    """Indica si un ``message_id`` ya fue procesado para esa etiqueta."""
    entry = state.get("labels", {}).get(label, {})
    return message_id in set(entry.get("seen", []))


def mark_seen(state: dict, label: str, message_id: str) -> None:
    """Registra un ``message_id`` como visto, con poda FIFO al tope ``SEEN_MAX``."""
    labels = state.setdefault("labels", {})
    entry = labels.setdefault(label, {"seen": []})
    seen = entry.setdefault("seen", [])
    if message_id not in seen:
        seen.append(message_id)
    if len(seen) > SEEN_MAX:
        del seen[: len(seen) - SEEN_MAX]


def complete_run(state: dict, label: str, *, now: float | None = None) -> None:
    """Marca la ejecución de una etiqueta como exitosa, fijando ``last_run_epoch``."""
    now = now if now is not None else time.time()
    labels = state.setdefault("labels", {})
    entry = labels.setdefault(label, {"seen": []})
    entry["last_run_epoch"] = int(now)
