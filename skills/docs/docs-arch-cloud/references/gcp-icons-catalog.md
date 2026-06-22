# Catálogo GCP — íconos disponibles

Cada `type` mapea a un ícono oficial `mxgraph.gcp2.*` con el color del
producto Google Cloud. Si necesitas un servicio que no está, usa el más
cercano y aclara en `description`; o avisa para extender el catálogo en
`skills/_lib/drawio/gcp_shapes.py`.

---

## Compute

| `type` | Servicio |
|---|---|
| `compute_engine` | Compute Engine |
| `app_engine` | App Engine |
| `cloud_functions` | Cloud Functions |
| `cloud_run` | Cloud Run |
| `gke` / `kubernetes_engine` | Google Kubernetes Engine |

## Storage

| `type` | Servicio |
|---|---|
| `cloud_storage` | Cloud Storage |
| `persistent_disk` | Persistent Disk |
| `filestore` | Filestore |
| `storage_transfer` | Storage Transfer Service |

## Databases

| `type` | Servicio |
|---|---|
| `cloud_sql` | Cloud SQL |
| `cloud_spanner` | Cloud Spanner |
| `cloud_bigtable` | Cloud Bigtable |
| `firestore` | Firestore |
| `datastore` | Datastore (legacy) |
| `memorystore` | Memorystore (Redis) |
| `bigquery` | BigQuery |

## Networking

| `type` | Servicio |
|---|---|
| `cloud_load_balancing` | Cloud Load Balancing |
| `cloud_cdn` | Cloud CDN |
| `cloud_dns` | Cloud DNS |
| `cloud_armor` | Cloud Armor (WAF) |
| `cloud_interconnect` | Cloud Interconnect |
| `cloud_nat` | Cloud NAT |
| `cloud_vpn` | Cloud VPN |
| `virtual_private_cloud` | VPC (servicio, no el grupo) |

## Big Data

| `type` | Servicio |
|---|---|
| `dataflow` | Cloud Dataflow |
| `dataproc` | Cloud Dataproc |
| `pubsub` | Cloud Pub/Sub |
| `dataprep` | Cloud Dataprep |
| `composer` | Cloud Composer |
| `data_catalog` | Data Catalog |

## AI / ML

| `type` | Servicio |
|---|---|
| `ai_platform` | Vertex AI / AI Platform |
| `automl` | AutoML |
| `vision_api` | Cloud Vision API |
| `natural_language_api` | Cloud Natural Language API |
| `speech_api` | Cloud Speech-to-Text |
| `translation_api` | Cloud Translation API |

## Identity & Security

| `type` | Servicio |
|---|---|
| `iam` | Identity and Access Management |
| `cloud_kms` | Cloud KMS |
| `identity_platform` | Identity Platform |
| `security_scanner` | Cloud Security Scanner |

## Management & Operations

| `type` | Servicio |
|---|---|
| `cloud_monitoring` | Cloud Monitoring |
| `cloud_logging` | Cloud Logging |
| `cloud_build` | Cloud Build |
| `cloud_source_repos` | Cloud Source Repositories |
| `container_registry` | Container Registry |
| `artifact_registry` | Artifact Registry |

## API & Integration

| `type` | Servicio |
|---|---|
| `cloud_endpoints` | Cloud Endpoints |
| `apigee` | Apigee API Platform |
| `cloud_tasks` | Cloud Tasks |
| `cloud_scheduler` | Cloud Scheduler |
| `workflows` | Workflows |

## IoT

| `type` | Servicio |
|---|---|
| `iot_core` | Cloud IoT Core |

## Genéricos / Actores

| `type` | Uso |
|---|---|
| `user` | Usuario individual |
| `users` | Múltiples usuarios |

---

## Grupos (boundaries / contenedores lógicos)

Los grupos GCP se renderizan como rectángulos punteados con etiqueta y color
del producto. Van en `groups[]` y se anidan con `parent`.

| `type` | Uso |
|---|---|
| `gcp_cloud` | Toda la nube GCP |
| `project` | Project (la unidad fundamental en GCP) |
| `region` | Región (us-central1, europe-west1, …) |
| `zone` | Zona dentro de la región (us-central1-a) |
| `vpc` | VPC |
| `subnet` | Subred |
| `instance_group` | Instance Group (managed) |
| `system` | Sistema genérico (etiqueta libre) |

### Anidamiento recomendado

```
project
├── region "us-central1"
│   ├── zone "us-central1-a"
│   │   └── (instancias específicas de zona)
│   └── vpc
│       └── subnet "default"
└── (servicios regionales/globales: BigQuery, Cloud Storage, IAM, ...)
```

Diferencias clave con AWS:
- **El project es la unidad de aislamiento principal** — más fuerte que un
  account AWS.
- Muchos servicios son **regionales o globales**, no zonales. BigQuery, Cloud
  Storage, IAM, Pub/Sub viven a nivel de proyecto o región, no de zona.
- **VPC global por defecto** — una VPC en GCP cruza regiones; las subredes son
  regionales.

---

## Tips para que el diagrama luzca bien

- **Modela el `project`** siempre como el grupo raíz. Indica el ID del
  proyecto en `name` (`data-platform-prod`).
- **Servicios serverless** (Cloud Run, Cloud Functions) **no necesitan VPC**
  a menos que requieran conectividad privada. Si la tienen, modela la
  conexión VPC explícitamente.
- **Pub/Sub, BigQuery, Cloud Storage** son **globales**: colócalos a nivel de
  proyecto (o región si aplica).
- **GKE** se modela como un solo servicio + grupo `instance_group` si quieres
  mostrar pools de nodos.
- Para multi-región o multi-zona en HA, modela explícitamente las regiones
  y zonas con sus grupos.
