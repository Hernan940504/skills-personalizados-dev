# Evidencia AWS en vivo — WordPress legado de Ciencuadras

| Campo | Valor |
|---|---|
| Fecha y hora de corte | 2026-09-21, hora Colombia |
| Cuenta consultada | `290296201161` — Soluciones Bolívar S.A.S Ciencuadras |
| Región | `us-east-1` |
| Acceso usado | SSO renovado con `aws-sso-refresh`; rol `ViewOnlyAccess` |
| Tipo de operaciones | Solo lectura: STS, ECS, EFS, S3, CloudFormation, ECR, ELB, Application Auto Scaling, CloudWatch y Cost Explorer |
| Alcance | WordPress legado `www` / `pre` y su persistencia EFS/S3 |

> **Conclusión ejecutiva.** El WordPress legado productivo está activo y sano en la cuenta `290296201161`; PRE también existe en esa misma cuenta, pero no está operativo. El servicio PRE intenta montar el filesystem EFS `fs-3952f8cc`, que ya no existe. No se debe reactivar PRE aumentando su `desiredCount`: seguirá fallando. La reconstrucción debe reemplazar esa dependencia de EFS por S3 y preservar la propiedad actual de CloudFormation hasta que exista un plan de adopción Terraform sin deriva. El EFS de PROD permanece disponible y recuperable; **solo se elimina cuando se garantice, mediante evidencia operativa en producción, que S3 soporta correctamente todos los medios y no queda ningún consumidor EFS**.

---

## 1. Identidad y límites de la evidencia

La sesión SSO fue renovada para el perfil `ciencuadras` y se validó con STS contra la cuenta `290296201161`. Los resultados siguientes son observaciones reales a la fecha de corte, no proyecciones.

No se ejecutaron acciones de escritura, cambios de DNS, despliegues, escalamiento, importaciones Terraform, transferencias DataSync ni borrados.

Por confirmación del usuario, `290296201161` es la **cuenta actual sobre la que se ejecuta esta reactivación**. La exploración de `cc-pre` (`691370287769`) no encontró componentes WordPress/EFS/ECS/S3/CloudFormation relacionados y queda descartada. Las cuentas `805516213253` y `844669095517` se conservan como referencias de inventario y de una eventual evolución de cuentas; este informe operativo documenta el estado real de `290296201161`.

---

## 2. Estado real de PROD y PRE

| Dimensión | PROD | PRE | Conclusión |
|---|---|---|---|
| Clúster ECS | `www-cluster-ciencuadras` | `pre-cluster-ciencuadras` | Ambos existen en la cuenta legada. |
| Servicio WordPress | Activo, 4 deseadas / 4 corriendo / 0 pendientes | Activo en control plane, 1 deseada / **0 corriendo** / 0 pendientes | PRE no está disponible aunque el servicio exista. |
| Escalamiento | Mínimo 2, máximo 10; CPU 40%, memoria 70% | Mínimo 1, máximo 4; CPU 40% | PRE no replica la capacidad ni la política completa de PROD. |
| Task definition vigente | Familia `www-ecs-ciencuadras-wordpress`, revisión 37 | Familia `pre-ecs-ciencuadras-wordpress`, revisión 31 | Son artefactos distintos. |
| Tamaño Fargate | 2 vCPU / 4 GB | 0,25 vCPU / 1 GB | PRE no tiene paridad de tamaño con PROD. |
| Imagen | Tag mutable `latest`; último push observado en 2022 | Tag mutable `latest`; último push observado en 2023 | Ninguno está fijado por digest; no existe garantía de reproducibilidad por tag. |
| Target group | 4 targets healthy | Sin targets healthy | PROD está atendiendo tráfico; PRE no logra iniciar tarea. |

### Causa comprobada de la indisponibilidad de PRE

La task definition PRE monta el volumen `efshtml` en `/media/efs/` y referencia el filesystem `fs-3952f8cc`. La consulta EFS devuelve `FileSystemNotFound` para ese ID.

Los eventos recientes del servicio PRE muestran intentos repetidos de iniciar la tarea y un `ResourceInitializationError`: no puede resolver/montar el EFS inexistente. La task definition no usa access point, no habilita cifrado en tránsito y monta el volumen en modo escritura.

**Decisión técnica:** no restaurar el EFS PRE como solución definitiva. La corrección objetivo es una nueva task definition para PRE que no dependa de EFS y use media en S3. Su origen debe ser el artefacto de PROD fijado por digest, no los tags `latest` actuales.

---

## 3. EFS de producción: estado, dependencia y propiedad

### 3.1 Filesystem actual

| Campo | Hallazgo |
|---|---|
| Filesystem | `fs-ae7b375b` — `www-efs-ciencuadras-wordpress` |
| Tamaño actual | 52.963.133.440 bytes (≈49,3 GiB) |
| Estado | Disponible |
| Cifrado en reposo | Sí |
| Modo de rendimiento | General Purpose |
| Throughput | Elastic |
| Lifecycle | Transición a IA después de 7 días |
| Mount targets | 2, distribuidos en dos AZ de `us-east-1` |
| Access points | No existen |
| Backup policy EFS | No existe una política configurada |
| File system policy | No existe una política configurada |
| Task definition PROD | Lo monta en `/media/efs/` con escritura, sin cifrado en tránsito ni autorización IAM de EFS |

El security group de EFS permite NFS (2049) a varios security groups. Uno es el security group del WordPress actual; al menos una referencia histórica no se pudo resolver por su formato/estado. Antes de retirar EFS hay que confirmar todos los consumidores reales y depurar referencias obsoletas.

### 3.2 Propiedad CloudFormation

El stack CloudFormation `www-efs-ciencuadras-wordpress` es propietario del filesystem, sus dos mount targets y su security group. El stack `www-ecs-ciencuadras-wordpress` es propietario, entre otros, del servicio ECS, task definition, target group, reglas de listener, ECR, CodeBuild y CodePipeline de PROD.

PRE también conserva los stacks `pre-efs-ciencuadras-wordpress` y `pre-ecs-ciencuadras-wordpress`. El primero reporta `CREATE_COMPLETE`, pero su recurso físico EFS ya no existe: es una **deriva comprobada** entre CloudFormation y AWS.

### 3.3 Conclusión Terraform y repositorios

El EFS actual **no fue identificado como un recurso creado por Terraform**: la propiedad en AWS corresponde a `www-efs-ciencuadras-wordpress` de CloudFormation y la revisión de [`ciencuadras-infra`](https://github.com/segurosbolivar/ciencuadras-infra) no encontró declaración EFS. Por tanto, Terraform no debe intentar crear, importar o destruir `fs-ae7b375b` como un atajo para la migración.

Para la alternativa corta mientras se define WordPress Multitenant, la recomendación es usar `ciencuadras-infra` únicamente para recursos **nuevos y condicionales** de `pre`/`prod` —S3, KMS, IAM, DataSync, observabilidad y configuración no colisionante— y mantener CloudFormation como dueño de los componentes existentes hasta decidir una adopción sin deriva o un servicio paralelo. `servicios-ciencuadras-networking-infra` queda como referencia de red para evolución de cuentas, no como repositorio de la corrección inmediata en `290296201161`.

> Terraform no debe crear recursos con los mismos nombres/ARN mientras CloudFormation sea el propietario. Se requiere una de estas rutas: (a) adoptar/importar primero el recurso y obtener un plan sin cambios; o (b) desplegar recursos paralelos con nombres nuevos, migrar consumidores y retirar el dueño anterior de forma controlada.

---

## 4. S3 actual y consecuencia para la migración

El bucket `ciencuadras-wp` existe, pero no es una réplica viable del EFS actual:

| Campo | Hallazgo |
|---|---|
| Objetos / tamaño total | 529 objetos; 10.579.813 bytes (≈10,1 MiB) |
| Prefijos visibles | `wp-content/` y `wp-includes/` |
| Cifrado por defecto | AES256 |
| Bloqueo de acceso público | Habilitado en los cuatro controles |
| Versionado | No configurado |
| Bucket policy | No existe |
| Hosting de sitio S3 | No configurado |

Con aproximadamente 49,3 GiB en EFS y solo 10,1 MiB en este bucket, no se debe asumir que el bucket representa el contenido ni los medios activos de PROD. El diseño objetivo debe crear buckets o prefijos **nuevos y separados para PRE y PROD**, con versionado, cifrado KMS, lifecycle, CloudFront/OAC y roles IAM de mínimo privilegio.

---

## 5. Costos reales de EFS

Cost Explorer muestra que el costo de EFS no está dominado por el almacenamiento. El único filesystem EFS disponible en la cuenta es el filesystem de WordPress, aunque se debe confirmar que no tenga otros consumidores antes de atribuirle el 100% del costo funcional.

| Periodo | Costo total EFS (USD) | Costo `ETDataAccess` (USD) | Datos con cargo de acceso (GB, Cost Explorer) |
|---|---:|---:|---:|
| 2026-06 | 537,79 | 535,56 | 17.850,88 |
| 2026-07 | 585,89 | 583,60 | 19.452,13 |
| 2026-08 | 532,56 | 530,28 | 17.675,03 |
| 2026-09-01 a 2026-09-20 | 380,31 | 378,71 | 12.621,87 |

Promedio de los tres meses completos:

- **US$552,08/mes** de EFS.
- **US$549,81/mes (99,59%)** corresponde a `ETDataAccess`, tráfico de acceso bajo Elastic Throughput.
- La proyección lineal de septiembre a 30 días es **~US$570,46**.
- El almacenamiento cobrado representa solo unos pocos dólares mensuales; la reducción no se logra por mover 49,3 GiB de capacidad, sino por eliminar aproximadamente 17,7–19,5 TB/mes de accesos a EFS si la aplicación deja de leer medios desde ese filesystem.

CloudWatch confirma una magnitud coherente de `MeteredIOBytes` mensual. Este es el caso económico central para S3 + CloudFront: una migración correcta puede retirar el costo de acceso EFS, pero debe medir el aumento de solicitudes S3 y entrega CDN antes de prometer un ahorro neto.

### Implicación de costo de migración

El volumen inicial a transferir es del orden de 49,3 GiB más incrementales. El costo único de DataSync será pequeño frente al costo recurrente de acceso EFS, pero se debe calcular con la tarifa vigente, el número real de pasadas y la clasificación de archivos. No se inicia DataSync hasta conocer qué rutas de `/media/efs/` son medios, código, cache, backups o datos no migrables.

---

## 6. Riesgos y deuda técnica observados

| Hallazgo | Riesgo | Acción exigida |
|---|---|---|
| PRE referencia un EFS eliminado | Servicio caído y bucle de intentos ECS | Sustituir la dependencia por S3; no aumentar réplicas como remediación. |
| EFS de PROD se monta con escritura, sin access point, IAM auth ni cifrado en tránsito | Amplio alcance de filesystem y menor control de acceso | El destino S3 debe tener prefijos, IAM y cifrado explícitos por ambiente. |
| EFS no tiene backup policy ni file system policy | Recuperación y gobierno no demostrados por el servicio | Crear backup verificable antes de la migración y probar restauración. |
| ECR usa `latest`, tags mutables y scan-on-push deshabilitado | No hay artefacto reproducible ni garantía de seguridad de imagen | Fijar digest, habilitar escaneo y construir imagen inmutable antes de PRE. |
| Existe un `www-redis` compartido, sin vínculo comprobado con WordPress | La existencia del recurso no prueba dependencia de la task definition, imagen o plugins del CMS | No incluir Redis como componente/costo base; validar configuración o PoC antes de incorporarlo por ambiente. |
| CloudFormation PRE muestra CREATE_COMPLETE con EFS eliminado | Deriva y riesgo de creación/actualización inesperada | Inventariar dueño de cada recurso; adoptar o reemplazar en paralelo. |
| Bucket `ciencuadras-wp` no tiene versionado/policy y es muy pequeño | No sirve de objetivo confiable de media | Crear almacenamiento S3 de media explícito por ambiente. |

---

## 7. Ruta recomendada, actualizada con evidencia real

### Fase A — Preparar y adoptar

1. Congelar cambios no esenciales en los stacks WordPress existentes y exportar el inventario de recursos CloudFormation/ECS.
2. Identificar el contenido exacto bajo `/media/efs/` mediante una tarea diagnóstica aprobada o un montaje de solo lectura; no usar una copia ciega de todo el filesystem.
3. Definir matriz de clasificación: `uploads` y medios a S3; core/plugins/temas a imagen; cache/temporales fuera de la migración; secretos a Secrets Manager/Parameter Store.
4. Declarar mediante Terraform los recursos S3, KMS, IAM, observabilidad y DataSync **solo para `pre` y `prod`**. Ejecutar cada sincronización DataSync mediante runbook/pipeline con aprobación; no sustituir directamente recursos con dueño CloudFormation.
5. Versionar el artefacto y fijar el digest que servirá como referencia de hora cero.

### Fase B — Recuperar PRE en paralelo

1. Crear bucket/prefijo S3 PRE nuevo y ejecutar sincronización inicial desde EFS PROD únicamente para rutas clasificadas como media.
2. Restaurar un corte de la base de datos PROD en PRE, sanear PII, rotar secretos, deshabilitar correo/webhooks/pagos y aplicar `noindex`.
3. Desplegar una task definition PRE nueva sin volumen EFS y con roles S3 restringidos al ambiente.
4. Mantener el servicio PRE existente como referencia de configuración, no como base ejecutable; actualmente está roto por el EFS eliminado.
5. Validar contenido, medias, uploads, thumbnails, cron, SEO y rollback.

### Fase C — Migrar PROD

1. Ejecutar sincronización inicial mientras PROD sigue atendiendo tráfico.
2. Congelar escrituras de medios en una ventana acordada, ejecutar incremental final y validar conteos, bytes y checksums.
3. Migrar por estrategia de adopción CloudFormation/Terraform o por servicio paralelo; no crear recursos homónimos que compitan con el stack actual.
4. Cambiar al servicio S3 validado, monitorear errores y mantener EFS recuperable durante el periodo de rollback.
5. Solo tras aceptación y ausencia de consumidores, retirar EFS y sus reglas de red.

---

## 8. Brechas aún pendientes

1. Listado y clasificación archivo por archivo de `/media/efs/` (ViewOnly no permite examinar el filesystem).
2. Confirmación de todos los consumidores EFS; hay varios security groups autorizados a NFS.
3. Inventario vivo de las cuentas separadas `805516213253` (Servicios Ciencuadras PRE) y `844669095517` (Seguros Ciencuadras PROD), si serán parte de la migración de cuenta además de la reactivación del legado.
4. Selección del plugin/mecanismo de media offload compatible con la versión real de WordPress y PHP.
5. Costeo de S3, CDN, solicitudes y DataSync con datos de tráfico del WordPress, para convertir el potencial de ahorro EFS en un business case neto.

---

## 9. Relación con el plan existente

Este informe complementa y corrige con evidencia viva el [plan de reactivación EFS → S3](./plan-reactivacion-wordpress-legado-efs-s3.md). La regla de oro queda así:

- **PROD activo real:** `www-ecs-ciencuadras-wordpress` sobre `fs-ae7b375b` en la cuenta `290296201161`.
- **PRE legado real:** `pre-ecs-ciencuadras-wordpress`, hoy inoperante por `fs-3952f8cc` eliminado.
- **Solución objetivo:** S3 por ambiente y artefactos inmutables; no reconstruir EFS PRE como estado final.
- **Propiedad de infraestructura:** CloudFormation hasta que Terraform adopte sin deriva o despliegue recursos paralelos.
