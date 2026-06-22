"""Primitivas compartidas para construir un .drawio nativo (XML mxGraph).

Convierte un modelo JSON normalizado en XML mxfile listo para abrir en
app.diagrams.net o draw.io desktop. Las paletas de shapes (C4, AWS, GCP,
OnPremise) viven en módulos `*_shapes.py` separados; este módulo solo se
encarga del XML, el layout y la validación.

Esquema del modelo JSON:
{
  "diagramType": "Context|Container|Component|Cloud",
  "title": "Título del diagrama",
  "scopeBoundary": "Nombre del límite del sistema (opcional)",
  "elements": [
    {
      "id": "ident_unico",
      "type": "<tipo del catálogo>",
      "name": "Nombre",
      "technology": "tecnología (opcional)",
      "description": "Responsabilidad",
      "external": false,
      "scope": true,
      "parent": "id_grupo_padre"  // opcional, anidamiento
    }
  ],
  "groups": [
    {
      "id": "grupo1",
      "type": "<tipo de grupo del catálogo>",
      "name": "VPC Production",
      "parent": "region1"  // opcional
    }
  ],
  "relationships": [
    {
      "source": "id_origen",
      "target": "id_destino",
      "description": "Propósito",
      "technology": "Protocolo",
      "async": false
    }
  ]
}
"""

from __future__ import annotations

import uuid
from html import escape
from typing import Iterable

BOX_W, BOX_H = 220, 130
COMPONENT_W, COMPONENT_H = 200, 110
CLOUD_W, CLOUD_H = 78, 78
H_GAP, V_GAP = 70, 90
TOP, LEFT = 60, 60
GROUP_PAD_SIDE = 30
GROUP_PAD_TOP = 50
GROUP_PAD_BOTTOM = 30
BOUNDARY_PAD_SIDE = 40
BOUNDARY_PAD_TOP = 60
BOUNDARY_PAD_BOTTOM = 40


class ModelError(ValueError):
    """Error semántico en el modelo JSON (id duplicado, relación rota, etc.)."""


def validate(model: dict, shape_catalog) -> None:
    """Valida el modelo contra un catálogo de shapes. Lanza ModelError si algo está mal."""
    elements = model.get("elements", []) or []
    groups = model.get("groups", []) or []
    relationships = model.get("relationships", []) or []

    seen_ids: set[str] = set()
    for el in elements:
        if "id" not in el or "type" not in el:
            raise ModelError(f"Elemento sin 'id' o 'type': {el!r}")
        if el["id"] in seen_ids:
            raise ModelError(f"id duplicado: {el['id']!r}")
        seen_ids.add(el["id"])
        if not shape_catalog.has_element(el["type"]):
            raise ModelError(
                f"type '{el['type']}' no existe en el catálogo "
                f"'{shape_catalog.name}' (elemento id={el['id']!r})"
            )

    for g in groups:
        if "id" not in g or "type" not in g:
            raise ModelError(f"Grupo sin 'id' o 'type': {g!r}")
        if g["id"] in seen_ids:
            raise ModelError(f"id duplicado entre elements/groups: {g['id']!r}")
        seen_ids.add(g["id"])
        if not shape_catalog.has_group(g["type"]):
            raise ModelError(
                f"Grupo type '{g['type']}' no existe en catálogo "
                f"'{shape_catalog.name}' (grupo id={g['id']!r})"
            )

    for el in elements + groups:
        parent = el.get("parent")
        if parent is not None and parent not in seen_ids:
            raise ModelError(
                f"'parent' apunta a id inexistente: {parent!r} en {el['id']!r}"
            )

    for r in relationships:
        for end in ("source", "target"):
            if r.get(end) not in seen_ids:
                raise ModelError(
                    f"Relación apunta a id inexistente: {r.get(end)!r}"
                )


def _vertex_label(name: str, stereotype: str, description: str | None) -> str:
    parts = [f"<b>{escape(name)}</b>"]
    if stereotype:
        parts.append(f'<font style="font-size:10px">{escape(stereotype)}</font>')
    if description:
        parts.append(f'<font style="font-size:10px">{escape(description)}</font>')
    return "<br>".join(parts)


def _edge_label(description: str, technology: str | None) -> str:
    desc = escape(description or "")
    if technology:
        return f'{desc}<br><font style="font-size:9px">[{escape(technology)}]</font>'
    return desc


def _edge_style(rel: dict) -> str:
    dashed = "1" if rel.get("async") else "0"
    return (
        "endArrow=block;endFill=1;html=1;fontSize=10;fontColor=#404040;"
        f"strokeColor=#707070;dashed={dashed};rounded=0;"
        "labelBackgroundColor=#FFFFFF;edgeStyle=orthogonalEdgeStyle;"
    )


def _xml_attr(value: str) -> str:
    return escape(value, quote=True)


def _children_of(parent_id: str | None, items: Iterable[dict]) -> list[dict]:
    return [it for it in items if it.get("parent") == parent_id]


def _layout_rank_based(model: dict, shape_catalog) -> tuple[dict, tuple | None, int]:
    """Layout C4: actores arriba, foco en medio (boundary), externos abajo.

    Devuelve (posiciones_por_id, boundary_box | None, canvas_width).
    """
    elements = model.get("elements", [])
    rows: dict[int, list[dict]] = {0: [], 1: [], 2: []}
    for el in elements:
        rows[shape_catalog.rank(el)].append(el)

    max_cols = max((len(r) for r in rows.values()), default=1) or 1
    canvas_w = LEFT * 2 + max_cols * BOX_W + (max_cols - 1) * H_GAP

    scope_present = (
        any(e.get("scope") for e in elements) and bool(model.get("scopeBoundary"))
    )

    positions: dict[str, tuple[float, float, float, float]] = {}
    boundary_box: tuple[float, float, float, float] | None = None
    y = float(TOP)
    for rank in (0, 1, 2):
        row = rows[rank]
        if not row:
            continue
        is_scope_row = rank == 1 and scope_present
        if is_scope_row:
            y += BOUNDARY_PAD_TOP
        row_w = len(row) * BOX_W + (len(row) - 1) * H_GAP
        x = (canvas_w - row_w) / 2
        row_left = x
        for el in row:
            positions[el["id"]] = (x, y, BOX_W, BOX_H)
            x += BOX_W + H_GAP
        if is_scope_row:
            boundary_box = (
                row_left - BOUNDARY_PAD_SIDE,
                y - BOUNDARY_PAD_TOP,
                row_w + 2 * BOUNDARY_PAD_SIDE,
                BOX_H + BOUNDARY_PAD_TOP + BOUNDARY_PAD_BOTTOM,
            )
            y += BOUNDARY_PAD_BOTTOM
        y += BOX_H + V_GAP
    return positions, boundary_box, int(canvas_w)


def _layout_nested(model: dict, shape_catalog) -> dict[str, tuple]:
    """Layout para diagramas con grupos anidados (cloud).

    Calcula tamaño de cada grupo en función de sus hijos, en grid simple.
    Devuelve {id: (x, y, w, h)} en coordenadas absolutas; los grupos se emiten
    como vertices con `container=1` y los hijos referencian al padre por id en
    el atributo `parent` del mxCell. Las coordenadas de los hijos quedan
    relativas al padre cuando hay anidamiento.
    """
    elements = model.get("elements", [])
    groups = model.get("groups", []) or []
    all_items = {it["id"]: it for it in elements + groups}

    leaf_w = shape_catalog.element_size()
    leaf_box_w, leaf_box_h = leaf_w

    def size_of(node_id: str | None) -> tuple[float, float]:
        children = _children_of(node_id, elements) + _children_of(node_id, groups)
        if not children:
            return float(leaf_box_w), float(leaf_box_h)
        widths: list[float] = []
        heights: list[float] = []
        for ch in children:
            if ch["id"] in {g["id"] for g in groups}:
                cw, chh = size_of(ch["id"])
            else:
                cw, chh = leaf_box_w, leaf_box_h
            widths.append(cw)
            heights.append(chh)
        # grid: ceil(sqrt(n)) columnas
        n = len(children)
        cols = max(1, int(n**0.5 + 0.999))
        rows_n = (n + cols - 1) // cols
        max_w_per_col = max(widths)
        max_h_per_row = max(heights)
        total_w = cols * max_w_per_col + (cols - 1) * H_GAP + 2 * GROUP_PAD_SIDE
        total_h = (
            rows_n * max_h_per_row
            + (rows_n - 1) * V_GAP
            + GROUP_PAD_TOP
            + GROUP_PAD_BOTTOM
        )
        return total_w, total_h

    positions: dict[str, tuple[float, float, float, float]] = {}

    def place(node_id: str | None, origin_x: float, origin_y: float) -> None:
        children = _children_of(node_id, elements) + _children_of(node_id, groups)
        if not children:
            return
        n = len(children)
        cols = max(1, int(n**0.5 + 0.999))
        sizes = []
        for ch in children:
            if ch["id"] in {g["id"] for g in groups}:
                sizes.append(size_of(ch["id"]))
            else:
                sizes.append((leaf_box_w, leaf_box_h))
        max_w = max(s[0] for s in sizes)
        max_h = max(s[1] for s in sizes)
        for i, ch in enumerate(children):
            col = i % cols
            row = i // cols
            w, h = sizes[i]
            # Anchor child within its cell (centered horizontally, top-aligned).
            cell_x = origin_x + GROUP_PAD_SIDE + col * (max_w + H_GAP)
            cell_y = origin_y + GROUP_PAD_TOP + row * (max_h + V_GAP)
            cx = cell_x + (max_w - w) / 2
            cy = cell_y
            positions[ch["id"]] = (cx, cy, w, h)
            if ch["id"] in {g["id"] for g in groups}:
                place(ch["id"], cx, cy)

    # Roots: items sin parent.
    roots = _children_of(None, elements) + _children_of(None, groups)
    # Placeable roots como un super-grupo virtual.
    n = len(roots)
    cols = max(1, int(n**0.5 + 0.999))
    sizes = []
    for ch in roots:
        if ch["id"] in {g["id"] for g in groups}:
            sizes.append(size_of(ch["id"]))
        else:
            sizes.append((leaf_box_w, leaf_box_h))
    if sizes:
        max_w = max(s[0] for s in sizes)
        max_h = max(s[1] for s in sizes)
        for i, ch in enumerate(roots):
            col = i % cols
            row = i // cols
            w, h = sizes[i]
            cell_x = LEFT + col * (max_w + H_GAP)
            cell_y = TOP + row * (max_h + V_GAP)
            cx = cell_x + (max_w - w) / 2
            cy = cell_y
            positions[ch["id"]] = (cx, cy, w, h)
            if ch["id"] in {g["id"] for g in groups}:
                place(ch["id"], cx, cy)

    return positions


def build_xml(model: dict, shape_catalog) -> str:
    """Construye el XML mxfile a partir del modelo y un catálogo de shapes.

    El catálogo debe exponer:
      - name: str
      - has_element(type) -> bool
      - has_group(type) -> bool
      - element_style(el) -> str (mxGraph style string)
      - group_style(g) -> str
      - element_stereotype(el) -> str
      - element_size() -> (w, h) por defecto para layouts grid
      - rank(el) -> int (0|1|2) para layout C4
      - use_nested_layout() -> bool
    """
    validate(model, shape_catalog)

    elements = model.get("elements", [])
    groups = model.get("groups", []) or []
    relationships = model.get("relationships", []) or []

    if shape_catalog.use_nested_layout() or groups:
        positions = _layout_nested(model, shape_catalog)
        boundary_box = None
        canvas_w = max(
            (positions[i][0] + positions[i][2] for i in positions),
            default=800,
        )
        canvas_w = int(canvas_w + LEFT)
    else:
        positions, boundary_box, canvas_w = _layout_rank_based(model, shape_catalog)

    cells: list[str] = []

    if boundary_box is not None:
        bx, by, bw, bh = boundary_box
        label = (
            f"{escape(model['scopeBoundary'])}<br>"
            '<font style="font-size:10px">[System]</font>'
        )
        cells.append(
            f'<mxCell id="boundary" value="{_xml_attr(label)}" '
            'style="rounded=1;arcSize=3;html=1;dashed=1;dashPattern=8 4;'
            'strokeColor=#444444;fillColor=none;verticalAlign=top;align=left;'
            'fontColor=#444444;fontStyle=2;spacingTop=6;spacingLeft=8;" '
            'vertex="1" parent="1">'
            f'<mxGeometry x="{bx:.0f}" y="{by:.0f}" '
            f'width="{bw:.0f}" height="{bh:.0f}" as="geometry"/>'
            "</mxCell>"
        )

    group_ids = {g["id"] for g in groups}

    def parent_xml_id(item: dict) -> str:
        return item.get("parent") or "1"

    def relative_xy(item: dict) -> tuple[float, float, float, float]:
        x, y, w, h = positions[item["id"]]
        parent = item.get("parent")
        if parent and parent in positions:
            px, py, _, _ = positions[parent]
            return x - px, y - py, w, h
        return x, y, w, h

    # Emitir grupos primero (los hijos referencian su id como parent).
    for g in groups:
        gx, gy, gw, gh = relative_xy(g)
        label = shape_catalog.group_label(g)
        cells.append(
            f'<mxCell id="{_xml_attr(g["id"])}" value="{_xml_attr(label)}" '
            f'style="{shape_catalog.group_style(g)}" vertex="1" '
            f'parent="{_xml_attr(parent_xml_id(g))}">'
            f'<mxGeometry x="{gx:.0f}" y="{gy:.0f}" '
            f'width="{gw:.0f}" height="{gh:.0f}" as="geometry"/>'
            "</mxCell>"
        )

    # Elementos.
    for el in elements:
        ex, ey, ew, eh = relative_xy(el)
        label = _vertex_label(
            name=el.get("name", el["id"]),
            stereotype=shape_catalog.element_stereotype(el),
            description=el.get("description"),
        )
        cells.append(
            f'<mxCell id="{_xml_attr(el["id"])}" value="{_xml_attr(label)}" '
            f'style="{shape_catalog.element_style(el)}" vertex="1" '
            f'parent="{_xml_attr(parent_xml_id(el))}">'
            f'<mxGeometry x="{ex:.0f}" y="{ey:.0f}" '
            f'width="{ew:.0f}" height="{eh:.0f}" as="geometry"/>'
            "</mxCell>"
        )

    # Relaciones.
    for i, r in enumerate(relationships):
        label = _edge_label(r.get("description", ""), r.get("technology"))
        cells.append(
            f'<mxCell id="rel{i}" value="{_xml_attr(label)}" '
            f'style="{_edge_style(r)}" edge="1" parent="1" '
            f'source="{_xml_attr(r["source"])}" '
            f'target="{_xml_attr(r["target"])}">'
            '<mxGeometry relative="1" as="geometry"/>'
            "</mxCell>"
        )

    diagram_name = escape(
        model.get("title", model.get("diagramType", "Architecture diagram"))
    )
    page_w = max(canvas_w, 1600)
    page_h = 1200
    body = "\n        ".join(cells)
    return (
        '<mxfile host="app.diagrams.net" type="device">\n'
        f'  <diagram id="{uuid.uuid4().hex[:12]}" name="{diagram_name}">\n'
        '    <mxGraphModel dx="1200" dy="800" grid="1" gridSize="10" guides="1" '
        'tooltips="1" connect="1" arrows="1" fold="1" page="1" pageScale="1" '
        f'pageWidth="{page_w}" pageHeight="{page_h}" math="0" shadow="0">\n'
        "      <root>\n"
        '        <mxCell id="0"/>\n'
        '        <mxCell id="1" parent="0"/>\n'
        f"        {body}\n"
        "      </root>\n"
        "    </mxGraphModel>\n"
        "  </diagram>\n"
        "</mxfile>\n"
    )
