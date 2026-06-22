"""Catálogo OnPremise (data center / red corporativa) con shapes estándar de draw.io.

Usa principalmente `mxgraph.networks.*` (red/datacenter), `mxgraph.rack.*`
(equipo de rack) y formas básicas (cilindro, actor) que están disponibles en
cualquier instalación de draw.io sin librerías externas.
"""

from __future__ import annotations

from html import escape

PALETTE = {
    "compute":  "#2A5599",
    "storage":  "#388E3C",
    "network":  "#7B1FA2",
    "security": "#C62828",
    "user":     "#455A64",
    "generic":  "#5A6C7D",
}

# type -> (shape spec, category, "tag")
# shape spec puede ser:
#   - "shape=...;..."  (estilo completo)
#   - "icon:<shape>"   (icono con label debajo y color de categoría)
SERVICES: dict[str, tuple[str, str, str]] = {
    # Compute / servers
    "server":             ("icon:mxgraph.networks.server", "compute", "Server"),
    "application_server": ("icon:mxgraph.networks.server", "compute", "Application Server"),
    "web_server":         ("icon:mxgraph.networks.server", "compute", "Web Server"),
    "mainframe":          ("icon:mxgraph.networks.mainframe", "compute", "Mainframe"),
    "virtual_machine":    ("icon:mxgraph.networks.virtual_machine", "compute", "Virtual Machine"),
    "container":          ("icon:mxgraph.networks.server", "compute", "Container Host"),
    # Storage
    "database":           ("cylinder", "storage", "Database"),
    "file_server":        ("icon:mxgraph.networks.storage", "storage", "File Server"),
    "nas":                ("icon:mxgraph.networks.storage", "storage", "NAS"),
    "san":                ("icon:mxgraph.networks.storage", "storage", "SAN"),
    "backup":             ("icon:mxgraph.networks.tape_array", "storage", "Backup"),
    "storage_array":      ("icon:mxgraph.networks.storage", "storage", "Storage Array"),
    # Network
    "router":             ("icon:mxgraph.networks.router_1", "network", "Router"),
    "switch":             ("icon:mxgraph.networks.switch_1", "network", "Switch"),
    "load_balancer":      ("icon:mxgraph.networks.load_balancer", "network", "Load Balancer"),
    "gateway":            ("icon:mxgraph.networks.gateway", "network", "Gateway"),
    "modem":              ("icon:mxgraph.networks.modem", "network", "Modem"),
    "wireless_ap":        ("icon:mxgraph.networks.wireless_ap", "network", "Wireless AP"),
    "proxy":              ("icon:mxgraph.networks.server", "network", "Proxy Server"),
    "api_gateway":        ("icon:mxgraph.networks.gateway", "network", "API Gateway"),
    "message_broker":     ("icon:mxgraph.networks.server", "network", "Message Broker"),
    # Security
    "firewall":           ("icon:mxgraph.networks.firewall_1", "security", "Firewall"),
    "ids":                ("icon:mxgraph.networks.firewall_1", "security", "IDS"),
    "ips":                ("icon:mxgraph.networks.firewall_1", "security", "IPS"),
    "vpn":                ("icon:mxgraph.networks.vpn_gateway", "security", "VPN Gateway"),
    # Users / clients
    "user":               ("actor", "user", "User"),
    "users":              ("actor", "user", "Users"),
    "workstation":        ("icon:mxgraph.networks.workstation", "user", "Workstation"),
    "laptop":             ("icon:mxgraph.networks.laptop", "user", "Laptop"),
    "mobile":             ("icon:mxgraph.networks.mobile", "user", "Mobile Device"),
    "browser":            ("icon:mxgraph.networks.workstation", "user", "Browser"),
    "printer":            ("icon:mxgraph.networks.printer", "user", "Printer"),
    # Generic
    "service":            ("box", "generic", "Service"),
    "component":          ("box", "generic", "Component"),
    "system":             ("box", "generic", "System"),
    "internet":           ("icon:mxgraph.networks.cloud", "generic", "Internet"),
    "cloud":              ("icon:mxgraph.networks.cloud", "generic", "Cloud"),
}

# type -> color del borde
GROUPS: dict[str, str] = {
    "data_center":     "#37474F",
    "dmz":             "#C62828",
    "internal_network":"#2A5599",
    "rack":            "#5A6C7D",
    "vlan":            "#7B1FA2",
    "zone":            "#388E3C",
    "system":          "#37474F",
    "site":            "#37474F",
}


def _icon_style(shape: str, color: str) -> str:
    return (
        f"shape={shape};html=1;labelPosition=center;"
        "verticalLabelPosition=bottom;align=center;verticalAlign=top;"
        f"strokeColor={color};fillColor={color};fontColor=#232F3E;fontSize=12;"
        "outlineConnect=0;"
    )


def _cylinder_style(color: str) -> str:
    return (
        "shape=cylinder3;whiteSpace=wrap;html=1;boundedLbl=1;backgroundOutline=1;"
        "size=15;direction=north;"
        f"fillColor={color};strokeColor={color};fontColor=#FFFFFF;"
        "align=center;verticalAlign=middle;fontSize=12;"
    )


def _box_style(color: str) -> str:
    return (
        "rounded=1;arcSize=8;whiteSpace=wrap;html=1;"
        f"fillColor={color};strokeColor={color};fontColor=#FFFFFF;"
        "align=center;verticalAlign=middle;fontSize=12;"
    )


def _actor_style(color: str) -> str:
    return (
        "shape=umlActor;verticalLabelPosition=bottom;labelPosition=center;"
        "verticalAlign=top;html=1;outlineConnect=0;"
        f"strokeColor={color};fillColor={color};fontColor=#232F3E;fontSize=12;"
    )


class Catalog:
    name = "onprem"

    @staticmethod
    def has_element(type_: str) -> bool:
        return type_ in SERVICES

    @staticmethod
    def has_group(type_: str) -> bool:
        return type_ in GROUPS

    @staticmethod
    def use_nested_layout() -> bool:
        return True

    @staticmethod
    def element_size() -> tuple[int, int]:
        return 140, 90

    @staticmethod
    def rank(el: dict) -> int:
        return 1

    @staticmethod
    def element_style(el: dict) -> str:
        spec, category, _ = SERVICES[el["type"]]
        color = PALETTE.get(category, PALETTE["generic"])
        if spec.startswith("icon:"):
            return _icon_style(spec[len("icon:"):], color)
        if spec == "cylinder":
            return _cylinder_style(color)
        if spec == "actor":
            return _actor_style(color)
        return _box_style(color)

    @staticmethod
    def element_stereotype(el: dict) -> str:
        _, _, tag = SERVICES[el["type"]]
        tech = el.get("technology")
        if tech:
            return f"[{tag}: {tech}]"
        return f"[{tag}]"

    @staticmethod
    def group_style(g: dict) -> str:
        color = GROUPS[g["type"]]
        return (
            "rounded=1;arcSize=4;html=1;dashed=1;dashPattern=8 4;"
            f"strokeColor={color};fillColor=none;"
            f"fontColor={color};fontSize=12;fontStyle=1;"
            "verticalAlign=top;align=left;spacingTop=8;spacingLeft=12;"
            "container=1;pointerEvents=0;collapsible=0;recursiveResize=0;"
        )

    @staticmethod
    def group_label(g: dict) -> str:
        tag = g["type"].replace("_", " ").upper()
        name = escape(g.get("name", g.get("id", "")))
        return f"{name}<br><font style='font-size:10px'>[{tag}]</font>"
