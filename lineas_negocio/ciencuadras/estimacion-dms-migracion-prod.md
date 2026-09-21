# Estimación de DMS — Migración BD Ciencuadras (legada → nueva PROD)

> Cuenta origen (legada): **Soluciones Bolívar S.A.S Ciencuadras** (`290296201161`) · Región `us-east-1`
> Cuenta destino (nueva productiva): **Seguros-Bolivar-ciencuadras-PROD** (`844669095517`)
> Fecha: 2026-09-02 · Autor: Arquitectura
> Fuente: validación directa contra la API de AWS (perfil `ciencuadras`, rol `ViewOnlyAccess`) sobre el clúster productivo real.

## Decisión

**Se recomienda una instancia de replicación DMS `dms.c6i.2xlarge` (8 vCPU / 16 GiB), Multi-AZ, con 200 GiB de almacenamiento, ejecutando una tarea única full-load + CDC.**

Es el punto que satisface simultáneamente: el volumen medido (~322 GiB), el pico de concurrencia y escritura de la base origen, y el margen operativo para no convertir el DMS en el cuello de botella de la migración. Las secciones siguientes lo sustentan con datos medidos, no estimados.

## 1. Alcance

Migración del clúster productivo **`www-rds-production-cluster`** (Aurora MySQL 8.0) desde la cuenta legada a un clúster Aurora MySQL equivalente en la nueva cuenta PROD. Los clústeres `dev-*`, `pre-*` y `qa-*` que coexisten en la cuenta legada **no** forman parte de esta estimación (se segmentan a sus propias cuentas por ambiente).

## 2. Datos medidos de la base origen

Todas las cifras fueron verificadas contra CloudWatch / RDS de la cuenta `290296201161`, no estimadas.

### 2.1 Topología del clúster productivo

| Rol | Instancia | Clase | Notas |
|---|---|---|---|
| Writer | `www-rds-production` | `db.r7g.xlarge` (4 vCPU / 32 GiB) | Origen del CDC (lee binlog) |
| Reader | `reader-rds-production` | `db.r7g.xlarge` | |
| Reader | `reportes-cc-prod` | `db.t3.medium` | Cargas de reportería |

- **Motor:** Aurora MySQL `8.0.mysql_aurora.3.10.3`
- **`binlog_format` = `ROW`** — requisito de CDC ya presente, pero en estado **`pending-reboot`** (ver riesgos).
- Retención de backup: 7 días.

### 2.2 Peso (volumen real)

| Métrica | Valor |
|---|---|
| `VolumeBytesUsed` (clúster prod) | **346 311 966 720 bytes ≈ 322.5 GiB** |

El `AllocatedStorage` de la API reporta 1 GB porque Aurora gestiona el almacenamiento de forma elástica; la fuente de verdad del peso es `VolumeBytesUsed`.

### 2.3 Concurrencia y carga (writer, ventana de 14 días)

| Métrica | Pico (1h) | Promedio | Pico fino (1 min, 24h) |
|---|---|---|---|
| `DatabaseConnections` | **719** | 225 | 198 |
| `CPUUtilization` writer | **90.9 %** | — | — |
| `CommitThroughput` (commits/s) | **537** | — | 469 |
| `WriteThroughput` | 6.47 MB/s | — | 5.71 MB/s |
| `ReadThroughput` | 79.8 MB/s | — | — |
| `WriteIOPS` | 4 879 | — | — |
| `NetworkTransmitThroughput` | 35.0 MB/s | — | — |

Lecturas clave para el dimensionamiento del DMS:
- **Concurrencia alta y CPU del writer al 91 %:** el writer ya opera cerca de saturación en pico. El DMS añade carga de lectura (full-load) y de lectura de binlog (CDC), por lo que conviene **arrancar el full-load fuera del horario pico** y que la instancia DMS tenga holgura para no re-leer.
- **~537 commits/s en pico:** es el ritmo de cambios que el CDC debe drenar sin acumular latencia. Es un caudal de transacciones moderado-alto; una instancia DMS pequeña se quedaría corta en el sostenimiento del CDC.
- **~322 GiB a mover en full-load:** determina la duración de la carga inicial y el almacenamiento de la instancia de replicación.

## 3. Dimensionamiento de la instancia de replicación DMS

### 3.1 Criterios

DMS consume CPU y memoria en proporción al **paralelismo de tablas**, al **caché de transacciones de CDC** y al **tamaño de las filas en tránsito**. Los factores medidos que empujan el tamaño hacia arriba:

1. Volumen de ~322 GiB con full-load paralelo (varias tablas simultáneas).
2. ~537 commits/s a sostener en CDC sin latencia creciente.
3. Writer origen ya al 91 % de CPU: el DMS debe ser eficiente para minimizar ventana e impacto.

### 3.2 Comparación de clases (familia c6i, optimizada a cómputo)

| Clase | vCPU | RAM | Veredicto |
|---|---|---|---|
| `dms.t3.medium` | 2 | 4 GiB | **Descartada.** Burstable; se agota en full-load de 322 GiB y no sostiene 537 commits/s. |
| `dms.c6i.large` | 2 | 4 GiB | **Descartada.** Sin burst, pero 4 GiB de RAM son insuficientes para el caché de CDC a este ritmo de commits. |
| `dms.c6i.xlarge` | 4 | 8 GiB | **Ajustada, sin margen.** Serviría, pero deja poca holgura ante el pico de commits y el paralelismo deseado. |
| **`dms.c6i.2xlarge`** | **8** | **16 GiB** | **Recomendada.** Paraleliza el full-load de 322 GiB, sostiene el CDC con caché en memoria y absorbe el pico de 537 commits/s con margen. |
| `dms.c6i.4xlarge` | 16 | 32 GiB | **Sobredimensionada** para este volumen y caudal; coste sin beneficio medible. |

### 3.3 Configuración recomendada

| Parámetro | Valor | Justificación |
|---|---|---|
| Clase de instancia | `dms.c6i.2xlarge` | Ver 3.2 |
| Multi-AZ | **Sí** | Migración de datos productivos; la resiliencia del canal de replicación es obligatoria por arquitectura. |
| Almacenamiento | **200 GiB** | El storage del DMS guarda logs y caché de tablas en tránsito, no una copia de los 322 GiB. 200 GiB dan holgura para logs de CDC ante picos sin ser excesivo. |
| Tipo de tarea | **full-load + CDC** | Carga inicial y luego replicación continua hasta el corte. |
| Versión de motor DMS | 3.5.x (última estable) | Compatibilidad con Aurora MySQL 8.0. |
| Paralelismo (`MaxFullLoadSubTasks`) | 8 (ajustar por nº de tablas) | Aprovecha las 8 vCPU en full-load. |

## 4. Estimación de duración del full-load

Estimación orientativa; la duración real depende del nº de tablas, índices y del impacto tolerado sobre el writer al 91 % de CPU.

| Supuesto de rendimiento efectivo | Duración aprox. de 322 GiB |
|---|---|
| Conservador (~50 GB/h) | ~6.5 h |
| Esperado (~80–100 GB/h) | ~3.3–4 h |

Recomendación: **iniciar el full-load en ventana de baja concurrencia** (fuera del pico donde el writer llega al 91 %) para acotar el impacto y acelerar la carga.

## 5. Riesgos y precondiciones

- **`binlog_format=ROW` está `pending-reboot`.** Debe estar **efectivamente aplicado** (reinicio del clúster) antes de iniciar el CDC, o la tarea fallará al no encontrar binlog en formato ROW. Verificar antes del corte.
- **Retención de binlog:** subir `binlog retention hours` en el origen (p. ej. 24–48 h) para que el CDC pueda reanudar tras una interrupción sin perder cambios.
- **Writer al 91 % de CPU en pico:** el full-load concurrente con el pico puede degradar la aplicación. Mitigar con ventana horaria y/o leyendo el full-load desde un **reader** si la topología lo permite (el CDC sí debe leer el binlog del writer).
- **Conectividad entre cuentas** `290296201161 → 844669095517`: validar peering/TGW y security groups antes de la tarea (fuera del alcance de esta estimación de sizing).
- **Objetos no migrables por DMS** (triggers, procedimientos, foreign keys durante carga): planificar su recreación post-migración.

## 6. Resumen ejecutivo

| Concepto | Valor medido / recomendado |
|---|---|
| Peso de la BD productiva | **~322.5 GiB** (`VolumeBytesUsed`) |
| Concurrencia pico | **719 conexiones**, CPU writer **91 %** |
| Caudal de cambios (CDC) | **~537 commits/s** pico |
| **Instancia DMS recomendada** | **`dms.c6i.2xlarge`, Multi-AZ, 200 GiB** |
| Tarea | full-load + CDC |
| Ventana de full-load estimada | ~3.3–6.5 h según rendimiento efectivo |
