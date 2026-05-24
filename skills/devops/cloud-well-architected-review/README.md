# cloud-well-architected-review

Skill para evaluar arquitecturas de aplicaciones cloud contra AWS Well-Architected Framework y
Google Cloud Well-Architected/Architecture Framework.

## Qué hace

- Escanea el repo (Terraform, CloudFormation, Kubernetes, Docker, ADRs) y detecta si la arquitectura es AWS, GCP o híbrida. Azure queda fuera de cobertura.
- Clasifica el estado del diseño: conceptual, preproducción o producción.
- Prioriza análisis de seguridad, escalabilidad/performance, resiliencia y costos.
- Identifica tradeoffs, riesgos de implementación, problemas de diseño y recomendaciones.
- Genera una matriz accionable con severidad, evidencia, riesgo, recomendación y prioridad.
- Opcionalmente persiste el informe como `WELL-ARCHITECTED-REVIEW.md` (a confirmación).

## Cuándo usarlo

Úsalo cuando quieras revisar una arquitectura cloud antes de construir, pasar a producción,
migrar, optimizar costos o corregir problemas de diseño.

## Ejemplos

- "Revisa esta arquitectura en AWS con ECS, RDS, SQS y CloudFront."
- "Evalúa riesgos de este diseño en GCP con Cloud Run, Pub/Sub y Cloud SQL."
- "Necesito tradeoffs entre EKS y Cloud Run para esta aplicación."
- "Haz un assessment well-architected de seguridad, resiliencia y costos."

## Referencias

- `scripts/discover-architecture.sh` — descubre proveedor e IaC del repo (Paso 0).
- `references/framework-mapping.md`
- `references/review-checklist.md`
