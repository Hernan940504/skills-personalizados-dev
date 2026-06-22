"""Catálogo de íconos oficiales Google Cloud (mxgraph.gcp2.*) para draw.io.

Cada `type` mapea a un shape `mxgraph.gcp2.<service>`. Para grupos (VPC, zona,
región, proyecto) se usan rectángulos con borde punteado en el color del
producto Google (azul Compute, verde Storage, rojo AI, amarillo Database).
"""

from __future__ import annotations

from html import escape

# Colores oficiales Google Cloud por categoría.
GCP_BLUE   = "#4285F4"   # Compute / Networking
GCP_GREEN  = "#34A853"   # Storage / Big Data
GCP_RED    = "#EA4335"   # AI / ML
GCP_YELLOW = "#FBBC04"   # Databases / Security
GCP_DARK   = "#1A73E8"
GCP_GRAY   = "#5F6368"

# type -> (shape, color etiqueta)
SERVICES: dict[str, tuple[str, str]] = {
    # Compute
    "compute_engine":     ("mxgraph.gcp2.compute_engine", GCP_BLUE),
    "app_engine":         ("mxgraph.gcp2.app_engine", GCP_BLUE),
    "cloud_functions":    ("mxgraph.gcp2.cloud_functions", GCP_BLUE),
    "cloud_run":          ("mxgraph.gcp2.cloud_run", GCP_BLUE),
    "gke":                ("mxgraph.gcp2.kubernetes_engine", GCP_BLUE),
    "kubernetes_engine":  ("mxgraph.gcp2.kubernetes_engine", GCP_BLUE),
    # Storage
    "cloud_storage":      ("mxgraph.gcp2.cloud_storage", GCP_GREEN),
    "persistent_disk":    ("mxgraph.gcp2.persistent_disk", GCP_GREEN),
    "filestore":          ("mxgraph.gcp2.filestore", GCP_GREEN),
    "storage_transfer":   ("mxgraph.gcp2.storage_transfer_service", GCP_GREEN),
    # Databases
    "cloud_sql":          ("mxgraph.gcp2.cloud_sql", GCP_YELLOW),
    "cloud_spanner":      ("mxgraph.gcp2.cloud_spanner", GCP_YELLOW),
    "cloud_bigtable":     ("mxgraph.gcp2.cloud_bigtable", GCP_YELLOW),
    "firestore":          ("mxgraph.gcp2.firestore", GCP_YELLOW),
    "datastore":          ("mxgraph.gcp2.datastore", GCP_YELLOW),
    "memorystore":        ("mxgraph.gcp2.memorystore", GCP_YELLOW),
    "bigquery":           ("mxgraph.gcp2.bigquery", GCP_GREEN),
    # Networking
    "cloud_load_balancing": ("mxgraph.gcp2.cloud_load_balancing", GCP_BLUE),
    "cloud_cdn":          ("mxgraph.gcp2.cloud_cdn", GCP_BLUE),
    "cloud_dns":          ("mxgraph.gcp2.cloud_dns", GCP_BLUE),
    "cloud_armor":        ("mxgraph.gcp2.cloud_armor", GCP_YELLOW),
    "cloud_interconnect": ("mxgraph.gcp2.cloud_interconnect", GCP_BLUE),
    "cloud_nat":          ("mxgraph.gcp2.cloud_nat", GCP_BLUE),
    "cloud_vpn":          ("mxgraph.gcp2.cloud_vpn", GCP_BLUE),
    "virtual_private_cloud": ("mxgraph.gcp2.virtual_private_cloud", GCP_BLUE),
    # Big Data
    "dataflow":           ("mxgraph.gcp2.cloud_dataflow", GCP_GREEN),
    "dataproc":           ("mxgraph.gcp2.cloud_dataproc", GCP_GREEN),
    "pubsub":             ("mxgraph.gcp2.cloud_pubsub", GCP_GREEN),
    "dataprep":           ("mxgraph.gcp2.cloud_dataprep", GCP_GREEN),
    "composer":           ("mxgraph.gcp2.cloud_composer", GCP_GREEN),
    "data_catalog":       ("mxgraph.gcp2.data_catalog", GCP_GREEN),
    # AI / ML
    "ai_platform":        ("mxgraph.gcp2.ai_platform", GCP_RED),
    "automl":             ("mxgraph.gcp2.automl", GCP_RED),
    "vision_api":         ("mxgraph.gcp2.cloud_vision_api", GCP_RED),
    "natural_language_api": ("mxgraph.gcp2.cloud_natural_language_api", GCP_RED),
    "speech_api":         ("mxgraph.gcp2.cloud_speech_to_text_api", GCP_RED),
    "translation_api":    ("mxgraph.gcp2.cloud_translation_api", GCP_RED),
    # Identity & Security
    "iam":                ("mxgraph.gcp2.identity_and_access_management", GCP_YELLOW),
    "cloud_kms":          ("mxgraph.gcp2.key_management_service", GCP_YELLOW),
    "identity_platform":  ("mxgraph.gcp2.identity_platform", GCP_YELLOW),
    "security_scanner":   ("mxgraph.gcp2.cloud_security_scanner", GCP_YELLOW),
    # Management & Operations
    "cloud_monitoring":   ("mxgraph.gcp2.cloud_monitoring", GCP_BLUE),
    "cloud_logging":      ("mxgraph.gcp2.cloud_logging", GCP_BLUE),
    "cloud_build":        ("mxgraph.gcp2.cloud_build", GCP_BLUE),
    "cloud_source_repos": ("mxgraph.gcp2.cloud_source_repositories", GCP_BLUE),
    "container_registry": ("mxgraph.gcp2.container_registry", GCP_BLUE),
    "artifact_registry":  ("mxgraph.gcp2.artifact_registry", GCP_BLUE),
    # API & integration
    "cloud_endpoints":    ("mxgraph.gcp2.cloud_endpoints", GCP_BLUE),
    "apigee":             ("mxgraph.gcp2.apigee_api_platform", GCP_BLUE),
    "cloud_tasks":        ("mxgraph.gcp2.cloud_tasks", GCP_BLUE),
    "cloud_scheduler":    ("mxgraph.gcp2.cloud_scheduler", GCP_BLUE),
    "workflows":          ("mxgraph.gcp2.workflows", GCP_BLUE),
    # IoT
    "iot_core":           ("mxgraph.gcp2.cloud_iot_core", GCP_GREEN),
    # Genéricos
    "user":               ("mxgraph.gcp2.user", GCP_GRAY),
    "users":              ("mxgraph.gcp2.users", GCP_GRAY),
}

# type -> color del borde del grupo
GROUPS: dict[str, str] = {
    "gcp_cloud":  GCP_DARK,
    "project":    GCP_DARK,
    "region":     GCP_BLUE,
    "zone":       GCP_GREEN,
    "vpc":        GCP_BLUE,
    "subnet":     GCP_BLUE,
    "system":     GCP_GRAY,
    "instance_group": GCP_BLUE,
}


class Catalog:
    name = "gcp"

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
        return 78, 78

    @staticmethod
    def rank(el: dict) -> int:
        return 1

    @staticmethod
    def element_style(el: dict) -> str:
        shape, color = SERVICES[el["type"]]
        return (
            "sketch=0;points=[[0,0,0],[0.25,0,0],[0.5,0,0],[0.75,0,0],[1,0,0],"
            "[0,1,0],[0.25,1,0],[0.5,1,0],[0.75,1,0],[1,1,0],[0,0.25,0],"
            "[0,0.5,0],[0,0.75,0],[1,0.25,0],[1,0.5,0],[1,0.75,0]];"
            "outlineConnect=0;gradientColor=none;"
            f"fontColor={color};fillColor={color};strokeColor=#ffffff;"
            "dashed=0;verticalLabelPosition=bottom;verticalAlign=top;"
            "align=center;html=1;fontSize=12;fontStyle=0;aspect=fixed;"
            f"shape={shape};"
        )

    @staticmethod
    def element_stereotype(el: dict) -> str:
        return ""

    @staticmethod
    def group_style(g: dict) -> str:
        color = GROUPS[g["type"]]
        return (
            "rounded=1;arcSize=2;html=1;dashed=1;dashPattern=8 4;"
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
