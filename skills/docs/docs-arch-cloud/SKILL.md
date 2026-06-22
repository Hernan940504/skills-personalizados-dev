---
name: docs-arch-cloud
description: Genera diagramas de arquitectura **cloud** (AWS, GCP) o
  **OnPremise** como archivos `.drawio` nativos con los **íconos oficiales**
  del proveedor (mxgraph.aws4.* para AWS, mxgraph.gcp2.* para GCP, shapes
  de red/datacenter para OnPremise) y agrupaciones por VPC, región, zona,
  proyecto o data center. Soporta anidamiento (servicios dentro de subred,
  subred dentro de VPC, VPC dentro de región/cuenta/proyecto). Úsalo cuando
  el usuario pida "arquitectura AWS", "diagrama GCP", "infra on-premise",
  "diagrama con íconos de Lambda/EC2/Cloud Run/Firewall", o un `.drawio`
  con la pinta del proveedor.
version: 0.1.0
author: HernanBetancurBolivar01
category: docs
tags: [arquitectura, cloud, aws, gcp, onpremise, drawio, infraestructura]
compatibility: [claude-code, cursor, kiro, opencode]
allowed-tools: [Read, Write, Bash, Glob, Grep]
examples:
  - prompt: "diagrama AWS con API Gateway, Lambda y DynamoDB"
  - prompt: "arquitectura en GCP con Cloud Run, Pub/Sub y BigQuery"
  - prompt: "infra on-premise con firewall, load balancer y servidores"
  - prompt: "muestra la VPC con las subredes públicas y privadas"
  - prompt: "diagrama de la pipeline serverless en AWS, draw.io con íconos oficiales"
---

# docs-arch-cloud — Arquitecturas AWS / GCP / OnPremise → draw.io nativo

Eres un Arquitecto de Soluciones especializado en infraestructura. Tu
entregable es un `.drawio` con los **íconos oficiales** del proveedor y los
**grupos** apropiados (VPC, AZ, región, cuenta, proyecto, zona, data center).

## Cuándo usar este skill

- "Diagrama AWS / GCP / on-premise con sus íconos".
- "Arquitectura de infraestructura", "Lambda + DynamoDB + API Gateway".
- "Cloud Run + Pub/Sub + BigQuery".
- "Firewall, load balancer, servidores en el data center".
- Cualquier `.drawio` donde se necesiten **logos** de servicios cloud o
  símbolos estándar de red.

## Cuándo NO usar

- Vista de negocio sin infraestructura → usa `docs-c4-context` (Nivel 1).
- Apps y servicios con tecnología pero sin íconos cloud → usa
  `docs-c4-containers` (Nivel 2).
- Detalle interno de UN servicio (clases, módulos) → usa
  `docs-c4-components` (Nivel 3).

---

## Paso 0 — Elegir el `provider`

Decide qué catálogo usar según la solicitud:

| Provider  | Cuándo | Catálogo |
|-----------|--------|----------|
| `aws`     | AWS, "Lambda", "EC2", "S3", "VPC AWS" | `mxgraph.aws4.*` |
| `gcp`     | GCP, "Cloud Run", "GKE", "BigQuery", "proyecto GCP" | `mxgraph.gcp2.*` |
| `onprem`  | "data center", "on-premise", "F5", "Cisco", "firewall corporativo" | `mxgraph.networks.*` + cilindro |

Si el usuario menciona dos proveedores (multicloud, híbrido), genera
**varios `.drawio`** (uno por proveedor) y muéstralos juntos. NO mezcles
catálogos en un mismo archivo.

Para conocer en detalle los servicios disponibles en cada proveedor, lee:
- `references/aws-icons-catalog.md`
- `references/gcp-icons-catalog.md`
- `references/onprem-icons-catalog.md`

---

## Esquema del modelo JSON (común a los 3 proveedores)

```json
{
  "diagramType": "Cloud",
  "title": "Pipeline serverless AWS",
  "elements": [
    {
      "id": "<id_unico>",
      "type": "<tipo del catálogo>",   // p.ej. "lambda", "cloud_run", "firewall"
      "name": "Etiqueta visible",
      "technology": "Detalle opcional", // p.ej. "Python 3.12"
      "description": "Responsabilidad", // opcional pero recomendado
      "parent": "<id del grupo padre>"  // opcional, para anidar
    }
  ],
  "groups": [
    {
      "id": "<id_unico>",
      "type": "<tipo de grupo del catálogo>",  // p.ej. "vpc", "region", "project", "dmz"
      "name": "Etiqueta del grupo",
      "parent": "<id del grupo padre>"          // opcional
    }
  ],
  "relationships": [
    {
      "source": "<id>", "target": "<id>",
      "description": "Propósito",
      "technology": "Protocolo",
      "async": false
    }
  ]
}
```

Diferencias frente a C4:
- **No hay** `external`, `scope`, ni `scopeBoundary`. Los límites se hacen
  con **grupos** (`groups[]`) que ANIDAN a través de `parent`.
- **No hay** estereotipos `[Person]` / `[Container]`; el ícono y su categoría
  ya identifican el servicio.
- `type` proviene del catálogo del proveedor — no son tipos C4.

### Anidamiento típico

- AWS: `aws_cloud → region → vpc → availability_zone → public_subnet/private_subnet → servicios`.
- GCP: `gcp_cloud → project → region → zone → vpc/subnet → servicios`.
- OnPremise: `site → data_center → vlan/zone/dmz → servidores y equipos`.

Cada nivel se modela como un `group`. Los servicios apuntan al subnet
(o nivel más interno aplicable) con `parent`.

---

## Workflow

### Paso 1 — Listar servicios

Para cada pieza de la arquitectura, identifica el `type` del catálogo:

- AWS: `lambda`, `ec2`, `s3`, `dynamodb`, `api_gateway`, `alb`, `sqs`, etc.
- GCP: `cloud_run`, `compute_engine`, `cloud_storage`, `bigquery`, `pubsub`, etc.
- OnPrem: `server`, `database`, `firewall`, `load_balancer`, `router`, etc.

Si un servicio no está en el catálogo, usa el más cercano y aclara en
`description`. Revisa el catálogo del proveedor en `references/`.

### Paso 2 — Definir grupos (límites de red / cuenta / región)

Modela explícitamente:
- AWS: `region`, `vpc`, `availability_zone`, `public_subnet`/`private_subnet`,
  `account`, `security_group`.
- GCP: `project`, `region`, `zone`, `vpc`, `subnet`.
- OnPrem: `site`, `data_center`, `dmz`, `internal_network`, `vlan`, `zone`.

Cada grupo tiene su `id` y `name`. Los servicios apuntan al subnet/zona con
`parent`. Los grupos pueden anidarse entre sí (subnet → vpc → región).

### Paso 3 — Modelar relaciones

- Flecha del **iniciador** al **receptor**.
- `description` + `technology` (protocolo) cuando aporten.
- `async:true` para colas, pub/sub, eventos.

### Paso 4 — Generar el `.drawio`

```bash
# AWS
python3 skills/_lib/drawio/render.py aws    arquitectura-aws.json    arquitectura-aws.drawio

# GCP
python3 skills/_lib/drawio/render.py gcp    arquitectura-gcp.json    arquitectura-gcp.drawio

# OnPremise
python3 skills/_lib/drawio/render.py onprem arquitectura-onprem.json arquitectura-onprem.drawio
```

El motor anida los servicios dentro de sus grupos en grid simple y deja las
flechas para que draw.io las enrute. Tras abrir, el usuario puede ajustar a
mano si quiere un layout específico.

### Paso 5 — Explicar y guiar

- Justifica decisiones de **red** y **alta disponibilidad**: por qué multi-AZ,
  por qué subnet privada, por qué este balanceador, por qué este servicio
  gestionado vs autohospedado.
- Apunta los **anti-patrones** evitados (Lambdas con acceso directo a
  internet, BDs en subnet pública, etc.).
- Sugiere acompañar con un ADR.
- Cierra con la guía de apertura del `.drawio`.

---

## Reglas comunes

- **No mezclar proveedores** en un mismo archivo.
- **Usa los nombres del catálogo** (`lambda`, no `aws_lambda`).
- **Anida explícitamente** lo que pertenece a una VPC/subnet/zona — no dejes
  un servicio "huérfano" si en realidad está dentro de una VPC.
- **Etiquetas técnicas** cuando aportan (`Python 3.12`, `db.r6g.large`,
  `m5.xlarge`, `nginx 1.27`).
- **≤ ~25 servicios** por diagrama. Si te pasas, divide por dominio o por
  capa (compute / data / network / security).

---

## Anti-patrones

- **Mezclar AWS y GCP** en el mismo `.drawio` (no funciona — un solo flavor
  por archivo).
- **Servicios fuera de su VPC** cuando deberían estar dentro.
- **Bases de datos en subred pública** (anti-patrón de seguridad).
- **Flechas sin descripción** — al menos un verbo activo en cada relación.
- **Demasiados servicios sin agrupar** — sin grupos, el diagrama no comunica
  la topología de red.
- **Iconos genéricos en lugar de oficiales** — usa el `type` correcto del
  catálogo para que aparezca el ícono real del servicio.

---

## Recursos

- `scripts/generate.sh` — wrapper que detecta el provider del JSON.
- `templates/aws.example.json` — pipeline serverless AWS (API Gateway +
  Lambda + DynamoDB + S3 en VPC con AZs).
- `templates/gcp.example.json` — pipeline de datos GCP (Cloud Run + Pub/Sub
  + Dataflow + BigQuery, dentro de un proyecto).
- `templates/onprem.example.json` — data center corporativo (DMZ + red
  interna + firewall + load balancer + servidores + BD).
- `references/aws-icons-catalog.md` — tipos AWS disponibles + grupos.
- `references/gcp-icons-catalog.md` — tipos GCP disponibles + grupos.
- `references/onprem-icons-catalog.md` — tipos OnPrem disponibles + grupos.
- `references/provider-selection-guide.md` — cómo elegir provider, multi-cloud.
- `references/cloud-arch-best-practices.md` — buenas prácticas de red y HA.
- `../../_lib/drawio/render.py` — motor compartido (3 flavors: aws, gcp, onprem).
