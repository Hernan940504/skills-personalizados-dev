# Design — Diagrama de componentes AWS Ciencuadras

| Campo | Valor |
|---|---|
| Documento | Diseño técnico del artefacto Draw.io |
| Versión | 1.0 |
| Fecha | 2026-09-23 |
| Basado en | `requirements.md`, inventario AWS de solo lectura y referencias visuales proporcionadas |
| Clasificación | Interno |

## Decisión de visualización

Se generará un único `.drawio` con cuatro páginas. Esta separación conserva la densidad de componentes de las referencias sin introducir un lienzo único ilegible ni mezclar configuraciones de ambientes distintos.

| Página | Propósito | Límite de información |
|---|---|---|
| `01 · Panorama por environment` | Muestra el patrón de componentes compartido y las diferencias relevantes entre DEV, PRE, STAGE y PROD. | Capacidades agregadas, sin recursos individuales. |
| `02 · DEV · Catálogo de runtime` | Describe el inventario fuente: entrada, workloads, datos, integración, seguridad y operación. | Agrupa los 45 servicios ECS observados por dominio técnico. |
| `03 · PROD · Topología objetivo` | Muestra la topología de alta disponibilidad para Producción basada en la evidencia operativa. | Tres AZ, subredes públicas/privadas y componentes de entrega, runtime, datos y operación. |
| `04 · DEV · Componentes detallados` | Descompone las capacidades de DEV en experiencia, dominio, legado, IA, datos y automatización. | Etiquetas funcionales sin nombres internos de recursos. |

## Estructura de boundaries

Cada página AWS seguirá la jerarquía:

```text
AWS Cloud
└── Environment
    └── us-east-1
        ├── Edge y servicios regionales
        ├── VPC
        │   ├── Subredes públicas — 3 AZ
        │   └── Subredes privadas — 3 AZ
        └── Plataforma, datos y operación
```

Los nombres visibles describen capacidad y environment; se excluyen cuentas, identificadores, endpoints, direcciones IP, CIDR, repositorios y nombres de recursos.

## Componentes modelados

### Edge y entrada

- Usuarios y sistemas externos.
- CloudFront como CDN, con orígenes S3, API Gateway y ALB observados.
- AWS WAF.
- API Gateway y VPC Link.
- ALB/NLB público e interno según environment.

### Runtime de aplicación

- ECS/Fargate agrupado en microfrontends, servicios Java de dominio, servicios PHP/legado, servicios Python/IA y WordPress cuando corresponde.
- ECR como repositorio de imágenes.
- Lambda, Step Functions y EventBridge para capacidades serverless y de automatización.
- SQS/SNS para desacoplamiento asíncrono.

### Datos, seguridad y operación

- Aurora MySQL cifrada y distribuida en tres AZ.
- ElastiCache, S3 y DMS como componentes de datos según el environment.
- Cognito, Systems Manager, KMS, Secrets Manager e IAM como controles de configuración e identidad cuando fueron observados.
- CloudWatch, logs y alarmas para observabilidad.
- CodePipeline/CodeBuild/CodeDeploy como entrega continua observada en la cuenta de referencia productiva.

## Relaciones

Las flechas representan únicamente relaciones confirmadas por configuración AWS o patrones agregados explícitos:

1. `Usuarios → CloudFront` por HTTPS.
2. `CloudFront → S3`, `CloudFront → API Gateway` y `CloudFront → ALB` según orígenes inventariados.
3. `API Gateway → VPC Link → balanceador interno` por HTTPS.
4. `Balanceadores → workloads ECS/Fargate` por HTTP/HTTPS.
5. `Workloads → Aurora / ElastiCache / S3 / SQS` mediante acceso de aplicación agregado.
6. `SQS → Lambda / automatización` como ruta asíncrona agregada.
7. `ECR → ECS/Fargate` como suministro de imágenes; `pipeline → ECR / runtime` como entrega continua.

Las dependencias de negocio a CRM, marketing y facturación se representan como una capacidad externa agregada porque existen workloads de integración; no se dibujan endpoints ni contratos que no fueron inspeccionados.

## Metadatos y notas de precisión

Los íconos agregados usarán `tooltip`, `properties` y `members` del modelo para incluir conteos, dominios funcionales y límites de la evidencia. Esto evita exponer nombres internos y permite que el lector consulte detalle directamente en draw.io.

El estado objetivo de WordPress modela medios en S3. La persistencia EFS legada no se representa como parte del target; se conserva en documentación de transición separada.

## Generación

El modelo fuente es un JSON multipágina. Un proceso local invoca el renderizador institucional `skills/_lib/drawio/render.py` para cada página y combina sus nodos `<diagram>` en un único `mxfile` nativo.
