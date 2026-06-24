"""Catálogo de íconos oficiales AWS (mxgraph.aws4.*) para draw.io.

Cada `type` mapea a un `resIcon` del shape `mxgraph.aws4.resourceIcon` con el
color de su categoría (paleta oficial AWS Architecture Icons 2018+).

Categorías y color de relleno:
- compute:    #ED7100 (naranja)
- containers: #ED7100
- storage:    #7AA116 (verde)
- database:   #C925D1 (magenta)
- network:    #8C4FFF (violeta)
- security:   #DD344C (rojo)
- mgmt:       #E7157B (rosa)
- integration:#E7157B
- analytics:  #8C4FFF
- ml:         #01A88D (teal)
- developer:  #C925D1
- iot:        #7AA116
- migration:  #8C4FFF
- frontend:   #DD344C
"""

from __future__ import annotations

from html import escape

CATEGORY_COLOR = {
    "compute":     "#ED7100",
    "containers":  "#ED7100",
    "storage":     "#7AA116",
    "database":    "#C925D1",
    "network":     "#8C4FFF",
    "security":    "#DD344C",
    "mgmt":        "#E7157B",
    "integration": "#E7157B",
    "analytics":   "#8C4FFF",
    "ml":          "#01A88D",
    "developer":   "#C925D1",
    "iot":         "#7AA116",
    "migration":   "#8C4FFF",
    "frontend":    "#DD344C",
    "generic":     "#232F3E",
}

# type -> (resIcon, category)
SERVICES: dict[str, tuple[str, str]] = {
    # Compute
    "ec2":                ("mxgraph.aws4.ec2", "compute"),
    "lambda":             ("mxgraph.aws4.lambda", "compute"),
    "lightsail":          ("mxgraph.aws4.lightsail", "compute"),
    "batch":              ("mxgraph.aws4.batch", "compute"),
    "elastic_beanstalk":  ("mxgraph.aws4.elastic_beanstalk", "compute"),
    "fargate":            ("mxgraph.aws4.fargate", "containers"),
    "ecs":                ("mxgraph.aws4.ecs", "containers"),
    "eks":                ("mxgraph.aws4.eks", "containers"),
    "ecr":                ("mxgraph.aws4.ecr", "containers"),
    "app_runner":         ("mxgraph.aws4.app_runner", "compute"),
    # Storage
    "s3":                 ("mxgraph.aws4.s3", "storage"),
    "ebs":                ("mxgraph.aws4.elastic_block_store", "storage"),
    "efs":                ("mxgraph.aws4.elastic_file_system", "storage"),
    "fsx":                ("mxgraph.aws4.fsx", "storage"),
    "glacier":            ("mxgraph.aws4.s3_glacier", "storage"),
    "storage_gateway":    ("mxgraph.aws4.storage_gateway", "storage"),
    "backup":             ("mxgraph.aws4.backup", "storage"),
    # Database
    "rds":                ("mxgraph.aws4.rds", "database"),
    "aurora":             ("mxgraph.aws4.aurora", "database"),
    "dynamodb":           ("mxgraph.aws4.dynamodb", "database"),
    "elasticache":        ("mxgraph.aws4.elasticache", "database"),
    "redshift":           ("mxgraph.aws4.redshift", "database"),
    "neptune":            ("mxgraph.aws4.neptune", "database"),
    "documentdb":         ("mxgraph.aws4.documentdb_with_mongodb_compatibility", "database"),
    "timestream":         ("mxgraph.aws4.timestream", "database"),
    # Network & content delivery
    "vpc":                ("mxgraph.aws4.vpc", "network"),
    "route_53":           ("mxgraph.aws4.route_53", "network"),
    "cloudfront":         ("mxgraph.aws4.cloudfront", "network"),
    "api_gateway":        ("mxgraph.aws4.api_gateway", "network"),
    "elb":                ("mxgraph.aws4.elastic_load_balancing", "network"),
    "alb":                ("mxgraph.aws4.application_load_balancer", "network"),
    "nlb":                ("mxgraph.aws4.network_load_balancer", "network"),
    "direct_connect":     ("mxgraph.aws4.direct_connect", "network"),
    "global_accelerator": ("mxgraph.aws4.global_accelerator", "network"),
    "transit_gateway":    ("mxgraph.aws4.transit_gateway", "network"),
    "app_mesh":           ("mxgraph.aws4.app_mesh", "network"),
    # Security
    "iam":                ("mxgraph.aws4.identity_and_access_management", "security"),
    "cognito":            ("mxgraph.aws4.cognito", "security"),
    "kms":                ("mxgraph.aws4.key_management_service", "security"),
    "secrets_manager":    ("mxgraph.aws4.secrets_manager", "security"),
    "acm":                ("mxgraph.aws4.certificate_manager_3", "security"),
    "waf":                ("mxgraph.aws4.waf", "security"),
    "shield":             ("mxgraph.aws4.shield", "security"),
    "guardduty":          ("mxgraph.aws4.guardduty", "security"),
    "macie":              ("mxgraph.aws4.macie", "security"),
    # Management & Governance
    "cloudwatch":         ("mxgraph.aws4.cloudwatch", "mgmt"),
    "cloudtrail":         ("mxgraph.aws4.cloudtrail", "mgmt"),
    "config":             ("mxgraph.aws4.config", "mgmt"),
    "systems_manager":    ("mxgraph.aws4.systems_manager", "mgmt"),
    "cloudformation":     ("mxgraph.aws4.cloudformation", "mgmt"),
    "organizations":      ("mxgraph.aws4.organizations", "mgmt"),
    "control_tower":      ("mxgraph.aws4.control_tower", "mgmt"),
    "trusted_advisor":    ("mxgraph.aws4.trusted_advisor", "mgmt"),
    # Application integration
    "sqs":                ("mxgraph.aws4.sqs", "integration"),
    "sns":                ("mxgraph.aws4.sns", "integration"),
    "eventbridge":        ("mxgraph.aws4.eventbridge", "integration"),
    "step_functions":     ("mxgraph.aws4.step_functions", "integration"),
    "mq":                 ("mxgraph.aws4.mq", "integration"),
    "appflow":            ("mxgraph.aws4.appflow", "integration"),
    # Analytics
    "athena":             ("mxgraph.aws4.athena", "analytics"),
    "glue":               ("mxgraph.aws4.glue", "analytics"),
    "kinesis":            ("mxgraph.aws4.kinesis", "analytics"),
    "kinesis_data_streams": ("mxgraph.aws4.kinesis_data_streams", "analytics"),
    "kinesis_firehose":   ("mxgraph.aws4.kinesis_data_firehose", "analytics"),
    "emr":                ("mxgraph.aws4.emr", "analytics"),
    "msk":                ("mxgraph.aws4.managed_streaming_for_kafka", "analytics"),
    "opensearch":         ("mxgraph.aws4.opensearch_service", "analytics"),
    "quicksight":         ("mxgraph.aws4.quicksight", "analytics"),
    # Machine Learning
    "sagemaker":          ("mxgraph.aws4.sagemaker", "ml"),
    "comprehend":         ("mxgraph.aws4.comprehend", "ml"),
    "rekognition":        ("mxgraph.aws4.rekognition", "ml"),
    "polly":              ("mxgraph.aws4.polly", "ml"),
    "translate":          ("mxgraph.aws4.translate", "ml"),
    "textract":           ("mxgraph.aws4.textract", "ml"),
    "bedrock":            ("mxgraph.aws4.bedrock", "ml"),
    # Developer Tools
    "codecommit":         ("mxgraph.aws4.codecommit", "developer"),
    "codebuild":          ("mxgraph.aws4.codebuild", "developer"),
    "codedeploy":         ("mxgraph.aws4.codedeploy", "developer"),
    "codepipeline":       ("mxgraph.aws4.codepipeline", "developer"),
    "cloud9":             ("mxgraph.aws4.cloud9", "developer"),
    # IoT
    "iot_core":           ("mxgraph.aws4.iot_core", "iot"),
    "greengrass":         ("mxgraph.aws4.iot_greengrass", "iot"),
    # Front-end & user
    "amplify":            ("mxgraph.aws4.amplify", "frontend"),
    "appsync":            ("mxgraph.aws4.appsync", "frontend"),
    # Genéricos (caja / actor)
    "user":               ("mxgraph.aws4.user", "generic"),
    "users":              ("mxgraph.aws4.users", "generic"),
    "client":             ("mxgraph.aws4.client", "generic"),
    "mobile_client":      ("mxgraph.aws4.mobile_client", "generic"),
    "internet":           ("mxgraph.aws4.internet_alt1", "generic"),
    "traditional_server": ("mxgraph.aws4.traditional_server", "generic"),
    "generic":            ("mxgraph.aws4.generic_application", "generic"),
}

# type -> (grIcon, strokeColor)
GROUPS: dict[str, tuple[str, str]] = {
    "aws_cloud":          ("mxgraph.aws4.group_aws_cloud_alt", "#232F3E"),
    "region":             ("mxgraph.aws4.group_region", "#00A4A6"),
    "vpc":                ("mxgraph.aws4.group_vpc", "#8C4FFF"),
    "availability_zone":  ("mxgraph.aws4.group_availability_zone", "#00A4A6"),
    "private_subnet":     ("mxgraph.aws4.group_security_group", "#00A4A6"),
    "public_subnet":      ("mxgraph.aws4.group_security_group", "#7AA116"),
    "subnet":             ("mxgraph.aws4.group_security_group", "#00A4A6"),
    "account":            ("mxgraph.aws4.group_account", "#CD2264"),
    "auto_scaling_group": ("mxgraph.aws4.group_auto_scaling_group", "#ED7100"),
    "security_group":     ("mxgraph.aws4.group_security_group", "#DD344C"),
    "corporate_dc":       ("mxgraph.aws4.group_corporate_data_center", "#5A6C7D"),
    "ec2_instance":       ("mxgraph.aws4.group_ec2_instance_contents", "#ED7100"),
    "server_contents":    ("mxgraph.aws4.group_server_contents", "#5A6C7D"),
    "generic_group":      ("mxgraph.aws4.group_security_group", "#5A6C7D"),
}


class Catalog:
    name = "aws"

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
    def cell_size() -> tuple[int, int]:
        # Celda de layout: icono 78 + ~100px de ancho para el label, y
        # ~70px adicionales en alto para 2-3 líneas de label/stereotipo.
        return 180, 150

    @staticmethod
    def brief_label() -> bool:
        return True

    @staticmethod
    def label_width() -> int:
        return 160

    @staticmethod
    def rank(el: dict) -> int:
        return 1

    @staticmethod
    def element_style(el: dict) -> str:
        res_icon, category = SERVICES[el["type"]]
        color = CATEGORY_COLOR.get(category, CATEGORY_COLOR["generic"])
        return (
            "sketch=0;points=[[0,0,0],[0.25,0,0],[0.5,0,0],[0.75,0,0],[1,0,0],"
            "[0,1,0],[0.25,1,0],[0.5,1,0],[0.75,1,0],[1,1,0],[0,0.25,0],"
            "[0,0.5,0],[0,0.75,0],[1,0.25,0],[1,0.5,0],[1,0.75,0]];"
            "outlineConnect=0;fontColor=#232F3E;gradientColor=none;"
            f"fillColor={color};strokeColor=#ffffff;dashed=0;"
            "verticalLabelPosition=bottom;verticalAlign=top;align=center;html=1;"
            "fontSize=12;fontStyle=0;aspect=fixed;"
            "shape=mxgraph.aws4.resourceIcon;"
            f"resIcon={res_icon};"
        )

    @staticmethod
    def element_stereotype(el: dict) -> str:
        return ""  # los íconos AWS no llevan estereotipo C4

    @staticmethod
    def group_style(g: dict) -> str:
        gr_icon, stroke = GROUPS[g["type"]]
        return (
            "points=[[0,0],[0.25,0],[0.5,0],[0.75,0],[1,0],[1,0.25],[1,0.5],"
            "[1,0.75],[1,1],[0.75,1],[0.5,1],[0.25,1],[0,1],[0,0.75],[0,0.5],"
            "[0,0.25]];outlineConnect=0;gradientColor=none;html=1;whiteSpace=wrap;"
            "fontSize=12;fontStyle=0;container=1;pointerEvents=0;collapsible=0;"
            "recursiveResize=0;"
            f"shape=mxgraph.aws4.group;grIcon={gr_icon};"
            f"strokeColor={stroke};fillColor=none;verticalAlign=top;align=left;"
            "spacingLeft=30;fontColor=#5A6C7D;dashed=0;"
        )

    @staticmethod
    def group_label(g: dict) -> str:
        return escape(g.get("name", g.get("id", "")))
