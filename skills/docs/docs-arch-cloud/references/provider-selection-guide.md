# Cómo elegir el `provider`

Este skill soporta tres flavors. El primer paso siempre es decidir cuál usar.

---

## Señales por proveedor

### `aws`
- Nombres de servicios AWS: Lambda, EC2, S3, DynamoDB, API Gateway, ALB,
  CloudFront, Route 53, SQS, SNS, EventBridge, Kinesis, ECS, EKS, Fargate.
- Términos: VPC, AZ, Region, Account, Security Group.
- "Architecture diagram AWS", "diagrama de la cuenta AWS", "stack en AWS".

### `gcp`
- Nombres de servicios GCP: Cloud Run, Cloud Functions, GKE, App Engine,
  Cloud Storage, Cloud SQL, Spanner, BigQuery, Pub/Sub, Dataflow, Vertex AI.
- Términos: Project, Region, Zone, VPC (global), Cloud Armor.
- "Diagrama en GCP", "stack de Google Cloud", "pipeline de datos GCP".

### `onprem`
- "Data center", "on-premise", "infra local", "red corporativa".
- Equipos: F5, Cisco, Palo Alto, FortiGate, switch, router, firewall.
- Software self-hosted: Tomcat, nginx, Apache, Oracle, Kafka on-prem.
- VLANs, DMZ, sucursal, sitio remoto.

Si la solicitud es ambigua, **pregunta** antes de generar.

---

## Multi-cloud o híbrido

Genera **un `.drawio` por proveedor**, no los mezcles en uno solo. Cada
catálogo tiene íconos distintos y un `.drawio` con dos provider sería un
caos visual.

Ejemplos:
- App en AWS que llama a BigQuery (analytics en GCP):
  → `aws.drawio` con el lado AWS + una caja `client` que represente la
    integración hacia GCP en `description`.
  → `gcp.drawio` con BigQuery + Dataflow + Pub/Sub, y una caja `user` o
    `client` que represente la app AWS que envía datos.
  → Acompáñalos con un texto que explique cómo se conectan.

- Migración on-prem → AWS:
  → `onprem.drawio` con el estado actual.
  → `aws.drawio` con el estado objetivo.
  → ADR explicando las decisiones.

---

## Cuándo NO usar este skill

- Si el usuario solo quiere mostrar **lógica de negocio** sin tecnología
  cloud-específica → usa `docs-c4-context` (Nivel 1).
- Si el usuario quiere **piezas desplegables genéricas con tecnología**
  (apps + BDs + colas) **sin íconos cloud** → usa `docs-c4-containers`
  (Nivel 2). Ej: "Tengo una API en Spring Boot + PostgreSQL + Kafka", sin
  decir AWS/GCP.
- Si el usuario quiere **componentes internos** de un servicio → usa
  `docs-c4-components` (Nivel 3).

---

## Caso típico: un equipo de soluciones cloud

Producto típico de un arquitecto de soluciones es un set de 2–4 diagramas:

1. **Contexto** (`docs-c4-context`) — visión de negocio.
2. **Contenedores** (`docs-c4-containers`) — piezas desplegables genéricas,
   sin íconos cloud.
3. **Cloud (este skill)** — los mismos contenedores mapeados a servicios
   AWS/GCP con sus íconos oficiales, VPC, AZs.
4. (Opcional) **Componentes** (`docs-c4-components`) — interior de los
   contenedores más complejos.

No es necesario generar los 4 siempre. Empieza por el que pida el usuario y
ofrece los demás solo si aportan valor.
