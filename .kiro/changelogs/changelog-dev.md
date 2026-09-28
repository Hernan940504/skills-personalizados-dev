# Changelog — dev

## [No publicado]

### Agregado
- Se generó `lineas_negocio/ciencuadras/arquitectura-componentes-ciencuadras-aws.drawio` con vistas multipágina por environment, catálogo de runtime y catálogo funcional detallado de DEV, y topología objetivo PROD, basado en inventario AWS de solo lectura. Incluye íconos AWS, componentes agrupados por capacidad, relaciones trazables y exclusión de cuentas, ARN, CIDR y secretos; se incorporaron el modelo JSON editable y la especificación de requisitos, diseño y tareas.
- Se generó `lineas_negocio/ciencuadras/comparativa-dms-vs-snapshot-prod.md` con la comparativa de estrategias de migración (DMS vs snapshot cross-account) para la BD productiva de Ciencuadras, incluyendo beneficios, riesgos, consideraciones y tiempo/costo como variables, basada en datos medidos contra la API de AWS
- Se generó `lineas_negocio/ciencuadras/estimacion-dms-migracion-prod.md` con la estimación de instancia DMS para la migración de la BD productiva de Ciencuadras (cuenta legada `290296201161` → nueva PROD `844669095517`), basada en peso y concurrencia medidos contra la API de AWS (rol ViewOnlyAccess)
- Se creó script `scripts/jira_update_issues.py` para actualizar issues en Jira reemplazando referencias de TASD-1 por TASD-4 en summary y description
- Se configuró integración con Langfuse MCP para análisis de comportamiento del agente conversacional
- Se creó steering file `langfuse-agent-analysis.md` con flujo de análisis de transferencias a agentes humanos
- Se generó informe completo de comportamiento del agente Victoria (informe-victoria-agent-behavior.html) con análisis mes a mes desde Mayo 2026
- Se creó el skill `docs-prd-aidlc` (categoría docs) para definir PRDs de productos como insumo del framework AI-DLC de AWS, adaptado a los guardrails de Seguros Bolívar: SKILL.md, README.md, plantilla de PRD de 9 secciones + bloque AI-DLC, 4 references (guía de llenado, mapeo a fases AI-DLC, guardrails corporativos, checklist) y script scaffold `new-prd.sh`
- Se documentó el plan de reactivación del WordPress legado de Ciencuadras en `lineas_negocio/ciencuadras/plan-reactivacion-wordpress-legado-efs-s3.md`, con cuentas origen/destino, migración reversible EFS→S3, paridad inicial de PRE, control condicional de Terraform y estimación de costos.
- Se agregó `.kiro/steering/aws-sso-authentication.md` como regla persistente: antes de cualquier conexión AWS se renueva el perfil con `aws-sso-refresh` y se valida la identidad con `aws sts get-caller-identity`, sin exponer credenciales.
- Se incorporó `lineas_negocio/ciencuadras/evidencia-aws-wordpress-legado-2026-09-21.md` con inventario AWS en vivo del WordPress legado de la cuenta `290296201161`: EFS activo de PROD, PRE inoperante por filesystem eliminado, propiedad CloudFormation, costo EFS y ruta de migración a S3.

### Cambiado
- Se ajustó la memoria de Ciencuadras para registrar la alternativa corta EFS→S3 mientras se define WordPress Multitenant, la cuenta DEV `Servicios-Bolivar-Ciencuadras-DEV` (`383946777605`), la propiedad CloudFormation del EFS y la condición exclusiva de retirar EFS solo tras garantizar S3 en producción.
- Se reestructuró la arquitectura objetivo para mostrar PRE y PROD aislados, con el mismo esquema de borde, imagen, ECS, Aurora, S3, secretos y observabilidad; EFS/DataSync solo aparecen en el runbook de migración y Redis queda pendiente de validación directa.
- Se retiró Redis como dependencia confirmada del WordPress legado: la evidencia conserva `www-redis` como recurso compartido sin vínculo probado con la task definition, imagen o plugins.
- Se documentó DataSync como recurso temporal gestionado por Terraform, con ejecuciones aprobadas fuera de `terraform apply`, y se agregaron costos separados para `290296201161` y una futura migración de cuentas.

### Corregido
- Se corrigió `skills/devops/aws-sso-refresh/scripts/aws-refresh.sh` para solicitar el scope OIDC de acceso a cuentas, desactivar pager/autoprompt durante el registro y fallar explícitamente si IAM Identity Center no devuelve identificadores de cliente; el skill se actualizó a v1.0.1 con compatibilidad Kiro.