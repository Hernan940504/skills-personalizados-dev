#!/usr/bin/env python3
"""
generate-drawio.py — Convierte un modelo C4 en JSON a un archivo .drawio nativo.

El archivo resultante usa el esquema de colores y la notación oficial del modelo C4
(https://c4model.com) con formas estándar de draw.io, de modo que abre directamente
en app.diagrams.net / draw.io desktop sin necesidad de librerías de shapes extra.

Uso:
    python3 generate-drawio.py <modelo.json> [salida.drawio]

Si se omite la salida, se escribe `diagrama_arquitectura.drawio` en el directorio actual.

Esquema del modelo JSON (ver templates/c4-model.example.json):
{
  "diagramType": "Context|Container|Component|Dynamic|Deployment",
  "title": "Título visible del diagrama",
  "scopeBoundary": "Nombre del límite del sistema (opcional)",
  "elements": [
    {
      "id": "ident_unico",
      "type": "person|system|container|database|queue|component",
      "name": "Nombre",
      "technology": "Java, Spring MVC",   // opcional; ignorado en person/system
      "description": "Responsabilidad en una frase",
      "external": false,                  // true => sistema/persona fuera de alcance
      "scope": true                       // true => va dentro de scopeBoundary
    }
  ],
  "relationships": [
    {
      "source": "id_origen",
      "target": "id_destino",
      "description": "Propósito de la interacción",
      "technology": "HTTPS/REST",         // protocolo/tecnología (opcional)
      "async": false                      // true => flecha punteada (evento/cola)
    }
  ]
}
"""

import json
import sys
import uuid
from html import escape

# --- Paleta y estilo canónico C4 -------------------------------------------------
# Colores derivados del esquema de Structurizr / c4model.com.
STYLES = {
    "person":            dict(fill="#08427B", stroke="#052E56", font="#FFFFFF", rounded=40),
    "person_ext":        dict(fill="#686868", stroke="#4D4D4D", font="#FFFFFF", rounded=40),
    "system":            dict(fill="#1168BD", stroke="#0B4884", font="#FFFFFF", rounded=8),
    "system_ext":        dict(fill="#999999", stroke="#6B6B6B", font="#FFFFFF", rounded=8),
    "container":         dict(fill="#438DD5", stroke="#2E6295", font="#FFFFFF", rounded=8),
    "queue":             dict(fill="#438DD5", stroke="#2E6295", font="#FFFFFF", rounded=8),
    "component":         dict(fill="#85BBF0", stroke="#5D82A8", font="#000000", rounded=8),
}

# Etiqueta de tipo (estereotipo C4) que se muestra bajo el nombre.
STEREOTYPE = {
    "person": "Person",
    "system": "Software System",
    "container": "Container",
    "queue": "Container",
    "database": "Container",
    "component": "Component",
}

BOX_W, BOX_H = 220, 130          # tamaño uniforme de cada caja
H_GAP, V_GAP = 70, 150           # separación entre cajas
TOP, LEFT = 60, 60               # márgenes
B_PAD_SIDE, B_PAD_TOP, B_PAD_BOTTOM = 40, 60, 40  # padding del boundary


def _style_key(el):
    t = el["type"]
    if t == "person":
        return "person_ext" if el.get("external") else "person"
    if t == "system":
        return "system_ext" if el.get("external") else "system"
    if t == "database":
        return "container"   # las BD usan color de container + forma cilindro
    return t if t in STYLES else "container"


def _vertex_style(el):
    s = STYLES[_style_key(el)]
    base = (f"whiteSpace=wrap;html=1;fontColor={s['font']};"
            f"fillColor={s['fill']};strokeColor={s['stroke']};"
            "align=center;verticalAlign=middle;fontSize=12;metaEdit=1;")
    if el["type"] == "database":
        # Cilindro para bases de datos.
        return ("shape=cylinder3;boundedLbl=1;backgroundOutline=1;size=15;"
                "direction=north;" + base)
    return f"rounded=1;arcSize={s['rounded']};{base}"


def _vertex_value(el):
    """Devuelve HTML crudo; el escapado XML del atributo se hace al emitir."""
    name = el.get("name", el["id"])
    kind = STEREOTYPE.get(el["type"], el["type"].capitalize())
    if el.get("external"):
        kind += ", External"
    tech = el.get("technology")
    if el["type"] in ("container", "component", "queue", "database") and tech:
        stereo = f"[{kind}: {tech}]"
    else:
        stereo = f"[{kind}]"
    html = f'<b>{name}</b><br><font style="font-size:10px">{stereo}</font>'
    desc = el.get("description", "")
    if desc:
        html += f'<br><br><font style="font-size:10px">{desc}</font>'
    return html


def _edge_style(rel):
    dashed = "1" if rel.get("async") else "0"
    return (f"endArrow=block;endFill=1;html=1;fontSize=10;fontColor=#404040;"
            f"strokeColor=#707070;dashed={dashed};rounded=0;"
            "labelBackgroundColor=#FFFFFF;edgeStyle=orthogonalEdgeStyle;")


def _edge_value(rel):
    """Devuelve HTML crudo; el escapado XML del atributo se hace al emitir."""
    desc = rel.get("description", "")
    tech = rel.get("technology")
    if tech:
        return f'{desc}<br><font style="font-size:9px">[{tech}]</font>'
    return desc


def _rank(el):
    """Asigna fila vertical: actores arriba, alcance en medio, externos abajo."""
    t = el["type"]
    if t == "person":
        return 2 if el.get("external") else 0
    if t == "system" and el.get("external"):
        return 2
    return 1  # containers, components, dbs, queues y sistema en foco


def build_xml(model):
    elements = model.get("elements", [])
    rels = model.get("relationships", [])
    ids = {e["id"] for e in elements}

    # --- validación temprana ---
    seen = set()
    for e in elements:
        if "id" not in e or "type" not in e:
            raise ValueError(f"Elemento sin 'id' o 'type': {e}")
        if e["id"] in seen:
            raise ValueError(f"id duplicado: {e['id']}")
        seen.add(e["id"])
        if e["type"] not in STEREOTYPE:
            raise ValueError(f"type inválido '{e['type']}' en {e['id']}")
    for r in rels:
        for end in ("source", "target"):
            if r.get(end) not in ids:
                raise ValueError(f"Relación apunta a id inexistente: {r.get(end)!r}")

    # --- agrupar por rango y ordenar ---
    rows = {0: [], 1: [], 2: []}
    for e in elements:
        rows[_rank(e)].append(e)

    scope_present = any(e.get("scope") for e in elements) and model.get("scopeBoundary")

    # ancho total para centrar filas
    max_cols = max((len(r) for r in rows.values()), default=1) or 1
    canvas_w = LEFT * 2 + max_cols * BOX_W + (max_cols - 1) * H_GAP

    positions = {}   # id -> (x, y)
    boundary_box = None
    y = TOP
    for rank in (0, 1, 2):
        row = rows[rank]
        if not row:
            continue
        is_scope_row = rank == 1 and scope_present
        if is_scope_row:
            y += B_PAD_TOP
        row_w = len(row) * BOX_W + (len(row) - 1) * H_GAP
        x = (canvas_w - row_w) / 2
        row_left, row_right = x, x + row_w
        for el in row:
            positions[el["id"]] = (x, y)
            x += BOX_W + H_GAP
        if is_scope_row:
            boundary_box = (row_left - B_PAD_SIDE, y - B_PAD_TOP,
                            row_w + 2 * B_PAD_SIDE, BOX_H + B_PAD_TOP + B_PAD_BOTTOM)
            y += B_PAD_BOTTOM
        y += BOX_H + V_GAP

    # --- emitir XML ---
    cells = []
    # boundary primero (queda detrás)
    if boundary_box:
        bx, by, bw, bh = boundary_box
        bval = escape(f'{model["scopeBoundary"]}<br>'
                      '<font style="font-size:10px">[System]</font>', quote=True)
        cells.append(
            f'<mxCell id="boundary" value="{bval}" '
            'style="rounded=1;arcSize=3;html=1;dashed=1;dashPattern=8 4;strokeColor=#444444;'
            'fillColor=none;verticalAlign=top;align=left;fontColor=#444444;fontStyle=2;'
            'spacingTop=6;spacingLeft=8;" vertex="1" parent="1">'
            f'<mxGeometry x="{bx:.0f}" y="{by:.0f}" width="{bw:.0f}" height="{bh:.0f}" as="geometry"/></mxCell>')

    for el in elements:
        ex, ey = positions[el["id"]]
        cells.append(
            f'<mxCell id="{escape(el["id"], quote=True)}" value="{escape(_vertex_value(el), quote=True)}" '
            f'style="{_vertex_style(el)}" vertex="1" parent="1">'
            f'<mxGeometry x="{ex:.0f}" y="{ey:.0f}" width="{BOX_W}" height="{BOX_H}" as="geometry"/></mxCell>')

    for i, r in enumerate(rels):
        cells.append(
            f'<mxCell id="rel{i}" value="{escape(_edge_value(r), quote=True)}" style="{_edge_style(r)}" '
            f'edge="1" parent="1" source="{escape(r["source"], quote=True)}" target="{escape(r["target"], quote=True)}">'
            '<mxGeometry relative="1" as="geometry"/></mxCell>')

    diagram_name = escape(model.get("title", model.get("diagramType", "C4 Diagram")))
    body = "\n        ".join(cells)
    return (
        '<mxfile host="app.diagrams.net" type="device">\n'
        f'  <diagram id="{uuid.uuid4().hex[:12]}" name="{diagram_name}">\n'
        '    <mxGraphModel dx="1200" dy="800" grid="1" gridSize="10" guides="1" '
        'tooltips="1" connect="1" arrows="1" fold="1" page="1" pageScale="1" '
        'pageWidth="1600" pageHeight="1200" math="0" shadow="0">\n'
        '      <root>\n'
        '        <mxCell id="0"/>\n'
        '        <mxCell id="1" parent="0"/>\n'
        f'        {body}\n'
        '      </root>\n'
        '    </mxGraphModel>\n'
        '  </diagram>\n'
        '</mxfile>\n'
    )


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    in_path = sys.argv[1]
    out_path = sys.argv[2] if len(sys.argv) > 2 else "diagrama_arquitectura.drawio"
    with open(in_path, encoding="utf-8") as f:
        model = json.load(f)
    xml = build_xml(model)
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(xml)
    n_el = len(model.get("elements", []))
    n_rel = len(model.get("relationships", []))
    print(f"OK  {out_path}  ({model.get('diagramType', '?')}: "
          f"{n_el} elementos, {n_rel} relaciones)")


if __name__ == "__main__":
    main()
