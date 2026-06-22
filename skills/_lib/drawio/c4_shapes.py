"""Catálogo de shapes y estereotipos del modelo C4 (Structurizr).

Colores oficiales c4model.com / Structurizr. Usa formas estándar de draw.io
(rectángulos redondeados + cilindro) para que el .drawio renderice idéntico
en cualquier instalación sin depender de librerías externas.
"""

from __future__ import annotations

from html import escape

PALETTE = {
    "person":     dict(fill="#08427B", stroke="#052E56", font="#FFFFFF", rounded=40),
    "person_ext": dict(fill="#686868", stroke="#4D4D4D", font="#FFFFFF", rounded=40),
    "system":     dict(fill="#1168BD", stroke="#0B4884", font="#FFFFFF", rounded=8),
    "system_ext": dict(fill="#999999", stroke="#6B6B6B", font="#FFFFFF", rounded=8),
    "container":  dict(fill="#438DD5", stroke="#2E6295", font="#FFFFFF", rounded=8),
    "component":  dict(fill="#85BBF0", stroke="#5D82A8", font="#000000", rounded=8),
}

ELEMENT_TYPES = {"person", "system", "container", "database", "queue", "component"}

STEREOTYPE = {
    "person":    "Person",
    "system":    "Software System",
    "container": "Container",
    "queue":     "Container",
    "database":  "Container",
    "component": "Component",
}


def _style_key(el: dict) -> str:
    t = el["type"]
    if t == "person":
        return "person_ext" if el.get("external") else "person"
    if t == "system":
        return "system_ext" if el.get("external") else "system"
    if t in {"container", "queue", "database"}:
        return "container"
    return "component"


class Catalog:
    name = "c4"

    @staticmethod
    def has_element(type_: str) -> bool:
        return type_ in ELEMENT_TYPES

    @staticmethod
    def has_group(type_: str) -> bool:
        return False

    @staticmethod
    def use_nested_layout() -> bool:
        return False

    @staticmethod
    def element_size() -> tuple[int, int]:
        return 220, 130

    @staticmethod
    def rank(el: dict) -> int:
        t = el["type"]
        if t == "person":
            return 2 if el.get("external") else 0
        if t == "system" and el.get("external"):
            return 2
        return 1

    @staticmethod
    def element_style(el: dict) -> str:
        s = PALETTE[_style_key(el)]
        base = (
            f"whiteSpace=wrap;html=1;fontColor={s['font']};"
            f"fillColor={s['fill']};strokeColor={s['stroke']};"
            "align=center;verticalAlign=middle;fontSize=12;metaEdit=1;"
        )
        if el["type"] == "database":
            return (
                "shape=cylinder3;boundedLbl=1;backgroundOutline=1;size=15;"
                "direction=north;" + base
            )
        return f"rounded=1;arcSize={s['rounded']};{base}"

    @staticmethod
    def element_stereotype(el: dict) -> str:
        kind = STEREOTYPE.get(el["type"], el["type"].capitalize())
        if el.get("external"):
            kind += ", External"
        tech = el.get("technology")
        if el["type"] in {"container", "component", "queue", "database"} and tech:
            return f"[{kind}: {tech}]"
        return f"[{kind}]"

    @staticmethod
    def group_style(g: dict) -> str:
        return ""

    @staticmethod
    def group_label(g: dict) -> str:
        return escape(g.get("name", g.get("id", "")))
