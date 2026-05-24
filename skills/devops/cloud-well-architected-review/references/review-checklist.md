# Review Checklist

Checklist práctico para convertir una descripción de arquitectura en hallazgos accionables.

## Datos mínimos de entrada

- Objetivo del aplicativo y flujo crítico.
- Proveedor(es), regiones y ambientes.
- Componentes: frontend, backend, APIs, datos, colas, storage, red, identidad.
- Tráfico, picos, latencia objetivo y dependencias externas.
- RTO/RPO, criticidad, cumplimiento y datos sensibles.
- Forma de despliegue, observabilidad e IaC.
- Restricciones de presupuesto y operación.

## Señales de riesgo por pilar

### Seguridad

- Recursos públicos sin necesidad clara.
- Secretos en variables planas, repositorios o imágenes.
- IAM amplio (`*`, admin, service accounts compartidas).
- Falta de cifrado, KMS o rotación de llaves.
- Logs sin auditoría o sin retención adecuada.
- Ausencia de WAF/rate limiting para APIs públicas.
- Multi-tenant sin aislamiento de datos por tenant.

### Escalabilidad / Performance

- Backend síncrono para tareas largas.
- Base de datos como cuello de botella único.
- Sin cache/CDN en lecturas frecuentes.
- Sin autoscaling o sin límites configurados.
- Conexiones DB no controladas desde workloads serverless.
- Dependencias externas sin timeouts o fallback.
- No hay pruebas de carga ni SLO de latencia.

### Resiliencia

- Un solo AZ/zona para componentes críticos.
- Backups no probados o sin restore drill.
- Sin RTO/RPO definido.
- Reintentos agresivos que amplifican fallos.
- Sin DLQ para mensajería.
- Deployments sin rollback.
- Migraciones de base de datos no reversibles.

### Costos

- Recursos sobredimensionados o siempre encendidos.
- Logs/trazas con retención indefinida.
- NAT/egress/cross-region replication no presupuestados.
- Ambientes no productivos sin apagado programado.
- Falta de etiquetas/labels, presupuestos y alertas.
- Uso de Kubernetes cuando el equipo no necesita esa complejidad.

### Excelencia operativa

- Infraestructura manual sin IaC.
- Alertas por síntomas tardíos, no por SLO.
- Dashboards inexistentes o no usados en incidentes.
- Sin runbooks ni ownership.
- CI/CD sin gates, tests o escaneo básico.

### Sostenibilidad

- Recursos ociosos permanentes.
- Retención de datos excesiva.
- Regiones elegidas sin considerar eficiencia, latencia o residencia.
- Procesamiento batch ineficiente o no alineado a demanda.

## Preguntas de profundización útiles

- ¿Cuál es el flujo que más dinero o reputación compromete si falla?
- ¿Qué indisponibilidad máxima tolera el negocio y qué pérdida de datos acepta?
- ¿Qué datos son sensibles y quién debe poder accederlos?
- ¿Cuál es el pico esperado y cómo se comportan las dependencias externas?
- ¿Qué parte del sistema hoy genera más costo o más incidentes?

## Scoring sugerido

Usa una escala cualitativa simple:

| Nivel | Criterio |
|---|---|
| Bajo | Faltan controles básicos o hay riesgos críticos sin mitigación |
| Medio | Diseño viable con brechas claras antes de producción |
| Alto | Buen alineamiento, riesgos residuales gestionados y operación definida |

No presentes el score como certificación. Es una estimación consultiva basada en la información disponible.

## Señales en IaC para el Paso 0

Cuando hay repositorio, `scripts/discover-architecture.sh` ancla el assessment. Señales típicas a confirmar manualmente:

- **Terraform** `*.tf`: `provider "aws"` / `provider "google"`, backend de state, `variables.tf` sin valores sensibles.
- **CloudFormation/CDK**: `AWSTemplateFormatVersion`, `cdk.json`, recursos `AWS::`.
- **Kubernetes/Helm**: `kind:`, `Chart.yaml`, límites de recursos, sondas, secrets.
- **Docker**: `Dockerfile`, `docker-compose*.yml`, imágenes base y puertos expuestos.
- **ADRs**: decisiones previas que expliquen tradeoffs ya asumidos.

Si el script detecta señales de **Azure** (`provider "azurerm"`, `Microsoft.*`), decláralo fuera de cobertura y limita el análisis a principios generales.
