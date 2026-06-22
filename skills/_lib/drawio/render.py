#!/usr/bin/env python3
"""CLI unificado: convierte un modelo JSON en un archivo .drawio nativo.

Uso:
    python3 -m drawio.render <flavor> <modelo.json> [salida.drawio]
    python3 render.py        <flavor> <modelo.json> [salida.drawio]

Flavors disponibles:
    c4       — modelo C4 (Context/Container/Component) con paleta Structurizr.
    aws      — íconos oficiales AWS (mxgraph.aws4.*) con grupos VPC/AZ/Region.
    gcp      — íconos oficiales GCP (mxgraph.gcp2.*) con grupos Project/Region/VPC.
    onprem   — equipamiento on-premise (red/datacenter) con shapes nativos.

Si se omite la salida se escribe `diagrama_arquitectura.drawio` en el directorio actual.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

# Permitir ejecución como script suelto (sin estar en sys.path).
if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from drawio import core, c4_shapes, aws_shapes, gcp_shapes, onprem_shapes
else:
    from . import core, c4_shapes, aws_shapes, gcp_shapes, onprem_shapes

CATALOGS = {
    "c4":     c4_shapes.Catalog,
    "aws":    aws_shapes.Catalog,
    "gcp":    gcp_shapes.Catalog,
    "onprem": onprem_shapes.Catalog,
}


def render(flavor: str, model: dict) -> str:
    if flavor not in CATALOGS:
        raise SystemExit(
            f"Flavor inválido: {flavor!r}. Disponibles: {', '.join(CATALOGS)}"
        )
    catalog = CATALOGS[flavor]
    try:
        return core.build_xml(model, catalog)
    except core.ModelError as e:
        raise SystemExit(f"Modelo inválido: {e}") from e


def main(argv: list[str]) -> int:
    if len(argv) < 3:
        print(__doc__)
        return 1
    flavor = argv[1]
    in_path = Path(argv[2])
    out_path = Path(argv[3]) if len(argv) > 3 else Path("diagrama_arquitectura.drawio")

    with in_path.open(encoding="utf-8") as f:
        model = json.load(f)

    xml = render(flavor, model)
    out_path.write_text(xml, encoding="utf-8")

    n_el = len(model.get("elements", []))
    n_gr = len(model.get("groups", []) or [])
    n_rel = len(model.get("relationships", []))
    dtype = model.get("diagramType", "?")
    print(
        f"OK  {out_path}  ({flavor}/{dtype}: "
        f"{n_el} elementos, {n_gr} grupos, {n_rel} relaciones)"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
