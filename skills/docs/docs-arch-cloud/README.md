# docs-arch-cloud

> Skill de **arquitecturas cloud y on-premise** — genera `.drawio` nativo con
> los **íconos oficiales** del proveedor (AWS `mxgraph.aws4.*`, GCP
> `mxgraph.gcp2.*`, OnPremise `mxgraph.networks.*`) y agrupaciones por VPC,
> región, AZ, proyecto, zona, data center o DMZ. Soporta anidamiento
> arbitrario.

---

## Qué hace

1. Elige `provider`: `aws`, `gcp` o `onprem`.
2. Modela servicios (Lambda, Cloud Run, firewall, BD, etc.) con `type` del
   catálogo correspondiente.
3. Define grupos (VPC, región, AZ, proyecto, zona, DMZ, VLAN) y anida
   servicios con `parent`.
4. Genera el `.drawio` vía `skills/_lib/drawio/render.py` (motor compartido).

Salida: `arquitectura-<sistema>-<provider>.drawio`.

---

## Prompts que activan este skill

```
"Diagrama AWS con API Gateway, Lambda y DynamoDB"
"Arquitectura en GCP con Cloud Run, Pub/Sub y BigQuery"
"Infra on-premise con firewall, load balancer y servidores"
"Muestra la VPC con las subredes públicas y privadas"
"Diagrama de la pipeline serverless en AWS, draw.io con íconos oficiales"
"Multi-AZ en AWS para producción"
"Pipeline de datos GCP con Dataflow y BigQuery"
```

---

## Estructura

```
docs-arch-cloud/
├── SKILL.md
├── README.md
├── scripts/
│   └── generate.sh                       # wrapper: ./generate.sh <provider> <json> [out]
├── templates/
│   ├── aws.example.json                  # API serverless multi-AZ
│   ├── gcp.example.json                  # pipeline de datos
│   └── onprem.example.json               # data center con DMZ + VLANs
└── references/
    ├── aws-icons-catalog.md              # tipos AWS + grupos
    ├── gcp-icons-catalog.md              # tipos GCP + grupos
    ├── onprem-icons-catalog.md           # tipos OnPrem + grupos
    ├── provider-selection-guide.md       # cómo elegir provider, multi-cloud
    └── cloud-arch-best-practices.md      # red, HA, observabilidad, anti-patrones
```

---

## Uso manual

```bash
# AWS
python3 skills/_lib/drawio/render.py aws    arquitectura.json arquitectura.drawio

# GCP
python3 skills/_lib/drawio/render.py gcp    arquitectura.json arquitectura.drawio

# OnPremise
python3 skills/_lib/drawio/render.py onprem arquitectura.json arquitectura.drawio
```

o el wrapper local:

```bash
skills/docs/docs-arch-cloud/scripts/generate.sh aws arquitectura.json arquitectura.drawio
```

---

## Esquema del modelo (común a los 3 proveedores)

```json
{
  "diagramType": "Cloud",
  "title": "Mi arquitectura",
  "elements": [
    { "id": "svc1", "type": "<del catálogo>", "name": "...", "description": "...", "parent": "subnet-a" }
  ],
  "groups": [
    { "id": "vpc",    "type": "vpc",    "name": "VPC 10.0.0.0/16", "parent": "region" },
    { "id": "subnet-a", "type": "private_subnet", "name": "private-a", "parent": "vpc" }
  ],
  "relationships": [
    { "source": "svc1", "target": "svc2", "description": "Llama", "technology": "HTTPS", "async": false }
  ]
}
```

---

## Reglas duras

- **Un solo `provider` por archivo.** Para multi-cloud genera varios
  `.drawio`.
- **Servicios anidados explícitamente** en sus VPC/subnet/zona vía `parent`.
- **BDs en subred privada.** Anti-patrón si están en pública.
- **Producción multi-AZ / multi-zona.** Modela ≥ 2 AZs/zonas.
- **≤ ~25 servicios** por diagrama. Si te pasas, divide por capa o dominio.
- **Etiquetar relaciones** con propósito + protocolo cuando aporten;
  `async:true` en colas y pub/sub.

---

## Limitaciones conocidas

| Limitación | Workaround |
|---|---|
| Catálogos no cubren el 100% de servicios | Usa el más cercano y aclara en `description`; o amplía `skills/_lib/drawio/<provider>_shapes.py` |
| Layout grid simple por grupo | Reorganiza con `Arrange > Layout` o a mano en draw.io |
| No combina proveedores en un archivo | Genera varios `.drawio` y muéstralos juntos |
| No infiere desde Terraform/CloudFormation/IaC | El agente arma el modelo desde la descripción del usuario |
