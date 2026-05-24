# Framework Mapping: AWS + Google Cloud

Usa este documento como brújula para alinear el assessment con los marcos oficiales.

## Fuentes oficiales

- AWS Well-Architected Framework: https://docs.aws.amazon.com/wellarchitected/latest/framework/
- AWS Well-Architected Tool: https://docs.aws.amazon.com/wellarchitected/latest/userguide/waf.html
- Google Cloud Well-Architected Framework: https://cloud.google.com/architecture/framework
- Google Cloud Architecture Center: https://cloud.google.com/architecture

## Pilares

| Área de análisis en esta skill | AWS Well-Architected | Google Cloud Well-Architected |
|---|---|---|
| Seguridad | Security | Security, privacy, and compliance |
| Escalabilidad / Performance | Performance efficiency | Performance optimization |
| Resiliencia | Reliability | Reliability |
| Costos | Cost optimization | Cost optimization |
| Excelencia operativa | Operational excellence | Operational excellence |
| Sostenibilidad | Sustainability | No es pilar principal en GCP WAF; tratar como práctica transversal |

## Orden de prioridad de esta skill

1. Seguridad
2. Escalabilidad / Performance
3. Resiliencia
4. Costos
5. Excelencia operativa
6. Sostenibilidad

Este orden es intencional para revisiones de aplicativos: primero evita exposición de datos y fallos graves,
luego valida capacidad de atender demanda, continuidad de servicio, eficiencia económica y operación.

## Equivalencias de servicios frecuentes

| Capacidad | AWS | GCP |
|---|---|---|
| Identidad cloud | IAM, IAM Identity Center, STS | IAM, Cloud Identity, Workload Identity Federation |
| KMS | AWS KMS, CloudHSM | Cloud KMS, Cloud HSM |
| Red | VPC, Security Groups, NACL, PrivateLink | VPC, Firewall Rules, Private Service Connect |
| WAF / DDoS | AWS WAF, Shield, CloudFront | Cloud Armor, Cloud CDN |
| Contenedores serverless | ECS Fargate, App Runner | Cloud Run |
| Kubernetes | EKS | GKE |
| Funciones | Lambda | Cloud Functions |
| SQL administrado | RDS, Aurora | Cloud SQL, AlloyDB |
| NoSQL | DynamoDB | Firestore, Bigtable |
| Mensajería | SQS, SNS, EventBridge, MSK | Pub/Sub, Eventarc, Cloud Tasks |
| Observabilidad | CloudWatch, X-Ray, CloudTrail | Cloud Monitoring, Cloud Logging, Cloud Trace, Cloud Audit Logs |
| Secretos | Secrets Manager, SSM Parameter Store | Secret Manager |
| IaC | CloudFormation, CDK, Terraform | Deployment Manager, Terraform, Config Controller |

## Lentes transversales

Considera lentes o perspectivas cuando el usuario mencione:

- Industria regulada: financiero, salud, gobierno, educación.
- IA/ML o analítica intensiva.
- SaaS multi-tenant.
- Migración desde on-premises.
- Datos personales o residencia de datos.
- Arquitectura híbrida o conectividad privada.
