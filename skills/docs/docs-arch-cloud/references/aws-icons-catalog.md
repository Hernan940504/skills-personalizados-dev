# Catálogo AWS — íconos disponibles

Cada `type` mapea a un ícono oficial `mxgraph.aws4.*` con el color de su
categoría (paleta oficial AWS Architecture Icons). Si el servicio que necesitas
no aparece aquí, usa el más cercano y aclara en `description`; o avisa para
extender el catálogo en `skills/_lib/drawio/aws_shapes.py`.

---

## Compute

| `type` | Servicio |
|---|---|
| `ec2` | EC2 |
| `lambda` | AWS Lambda |
| `lightsail` | Lightsail |
| `batch` | AWS Batch |
| `elastic_beanstalk` | Elastic Beanstalk |
| `app_runner` | App Runner |

## Containers

| `type` | Servicio |
|---|---|
| `fargate` | Fargate |
| `ecs` | Elastic Container Service |
| `eks` | Elastic Kubernetes Service |
| `ecr` | Elastic Container Registry |

## Storage

| `type` | Servicio |
|---|---|
| `s3` | Simple Storage Service (S3) |
| `ebs` | Elastic Block Store |
| `efs` | Elastic File System |
| `fsx` | FSx |
| `glacier` | S3 Glacier |
| `storage_gateway` | Storage Gateway |
| `backup` | AWS Backup |

## Database

| `type` | Servicio |
|---|---|
| `rds` | RDS |
| `aurora` | Aurora |
| `dynamodb` | DynamoDB |
| `elasticache` | ElastiCache |
| `redshift` | Redshift |
| `neptune` | Neptune |
| `documentdb` | DocumentDB |
| `timestream` | Timestream |

## Networking & Content Delivery

| `type` | Servicio |
|---|---|
| `vpc` | VPC (servicio, no el grupo) |
| `route_53` | Route 53 |
| `cloudfront` | CloudFront |
| `api_gateway` | API Gateway |
| `elb` | Elastic Load Balancing (genérico) |
| `alb` | Application Load Balancer |
| `nlb` | Network Load Balancer |
| `direct_connect` | Direct Connect |
| `global_accelerator` | Global Accelerator |
| `transit_gateway` | Transit Gateway |
| `app_mesh` | App Mesh |

## Security, Identity & Compliance

| `type` | Servicio |
|---|---|
| `iam` | IAM |
| `cognito` | Cognito |
| `kms` | KMS |
| `secrets_manager` | Secrets Manager |
| `acm` | Certificate Manager |
| `waf` | WAF |
| `shield` | Shield |
| `guardduty` | GuardDuty |
| `macie` | Macie |

## Management & Governance

| `type` | Servicio |
|---|---|
| `cloudwatch` | CloudWatch |
| `cloudtrail` | CloudTrail |
| `config` | Config |
| `systems_manager` | Systems Manager |
| `cloudformation` | CloudFormation |
| `organizations` | Organizations |
| `control_tower` | Control Tower |
| `trusted_advisor` | Trusted Advisor |

## Application Integration

| `type` | Servicio |
|---|---|
| `sqs` | SQS |
| `sns` | SNS |
| `eventbridge` | EventBridge |
| `step_functions` | Step Functions |
| `mq` | MQ |
| `appflow` | AppFlow |

## Analytics

| `type` | Servicio |
|---|---|
| `athena` | Athena |
| `glue` | Glue |
| `kinesis` | Kinesis (genérico) |
| `kinesis_data_streams` | Kinesis Data Streams |
| `kinesis_firehose` | Kinesis Data Firehose |
| `emr` | EMR |
| `msk` | MSK (Managed Kafka) |
| `opensearch` | OpenSearch Service |
| `quicksight` | QuickSight |

## Machine Learning

| `type` | Servicio |
|---|---|
| `sagemaker` | SageMaker |
| `comprehend` | Comprehend |
| `rekognition` | Rekognition |
| `polly` | Polly |
| `translate` | Translate |
| `textract` | Textract |
| `bedrock` | Bedrock |

## Developer Tools

| `type` | Servicio |
|---|---|
| `codecommit` | CodeCommit |
| `codebuild` | CodeBuild |
| `codedeploy` | CodeDeploy |
| `codepipeline` | CodePipeline |
| `cloud9` | Cloud9 |

## IoT

| `type` | Servicio |
|---|---|
| `iot_core` | IoT Core |
| `greengrass` | IoT Greengrass |

## Front-end & Mobile

| `type` | Servicio |
|---|---|
| `amplify` | Amplify |
| `appsync` | AppSync |

## Genéricos / Actores

| `type` | Uso |
|---|---|
| `user` | Usuario individual |
| `users` | Múltiples usuarios / clientes |
| `client` | Cliente genérico |
| `mobile_client` | Cliente móvil |
| `internet` | Símbolo de Internet |
| `traditional_server` | Servidor tradicional (legacy) |
| `generic` | Aplicación genérica |

---

## Grupos (boundaries / contenedores lógicos)

Los grupos van en `groups[]` y se anidan vía `parent`. Cada uno produce un
recuadro con el ícono del grupo en la esquina superior.

| `type` | Uso |
|---|---|
| `aws_cloud` | Toda la nube AWS |
| `account` | AWS Account |
| `region` | Región (us-east-1, eu-west-1, …) |
| `vpc` | VPC |
| `availability_zone` | Availability Zone |
| `private_subnet` | Subred privada |
| `public_subnet` | Subred pública |
| `subnet` | Subred genérica |
| `auto_scaling_group` | Auto Scaling Group |
| `security_group` | Security Group |
| `corporate_dc` | Data center corporativo (on-prem visto desde AWS) |
| `ec2_instance` | Contenido de una instancia EC2 (procesos/agents) |
| `server_contents` | Contenido de un servidor genérico |
| `generic_group` | Grupo genérico |

### Anidamiento recomendado

```
account
└── region
    └── vpc
        ├── availability_zone "us-east-1a"
        │   ├── public_subnet "public-1a"
        │   └── private_subnet "private-1a"
        └── availability_zone "us-east-1b"
            ├── public_subnet "public-1b"
            └── private_subnet "private-1b"
```

Servicios regionales (que no viven en una AZ específica) — IAM, Route 53,
CloudFront, S3 — se pueden colocar a nivel `account` o `region`. CloudFront es
global, así que puede ir incluso fuera de cualquier región.

---

## Tips para que el diagrama luzca bien

- **Multi-AZ siempre que sea producción.** Modela ≥ 2 AZs aunque uses los
  mismos servicios.
- **BDs en subnet privada** — `rds`, `aurora`, `elasticache` van en
  `private_subnet`, nunca en `public_subnet`.
- **Lambdas en VPC solo si necesitan acceso a recursos privados** — si no
  necesitan VPC, déjalas a nivel de `region` (más simple y sin penalización
  de cold start).
- **API Gateway y CloudFront** quedan a nivel de región o cuenta — no van
  dentro de VPC.
- **NAT/Internet Gateway** se modelan implícitamente con la convención
  "subnet pública" / "subnet privada".
