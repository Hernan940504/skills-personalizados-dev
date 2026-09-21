# Comparativa de estrategias de migración — DMS vs Snapshot cross-account

> Base de datos: clúster productivo **`www-rds-production-cluster`** (Aurora MySQL 8.0)
> Cuenta origen (legada): **Soluciones Bolívar S.A.S Ciencuadras** (`290296201161`) · Región `us-east-1`
> Cuenta destino (nueva PROD): **Seguros-Bolivar-ciencuadras-PROD** (`844669095517`)
> Fecha: 2026-09-02 · Autor: Arquitectura
> Fuente: validación directa contra la API de AWS (perfil `ciencuadras`, rol `ViewOnlyAccess`).

## Resumen ejecutivo

Existen dos caminos para llevar la BD productiva de Ciencuadras a la nueva cuenta: **AWS DMS** (full-load + CDC) y **restauración desde un snapshot compartido cross-account**. No son excluyentes; de hecho se complementan.

| Criterio | Snapshot cross-account | AWS DMS (full-load + CDC) |
|---|---|---|
| Downtime | **Alto** (corte total durante copia + restauración) | **Mínimo/near-zero** (CDC replica en caliente) |
| Fidelidad de copia | **Total** (bloque a bloque, incluye triggers, SP, FKs, usuarios) | **Parcial** (DML sí; objetos secundarios requieren recreación) |
| Complejidad operativa | **Baja** (procedimiento nativo RDS) | **Media/Alta** (endpoints, tarea, tuning, monitoreo CDC) |
| Costo directo | **Bajo** (solo almacenamiento + transferencia) | **Medio** (instancia DMS activa durante toda la ventana) |
| Tiempo total | **Horas** (una sola pasada) | **Horas de carga + días de CDC** hasta el corte |
| Bloqueante principal | **KMS de Seguridad TI** (`520521765653`) | **CPU writer al 91 %** + `binlog ROW` pending-reboot |

**Recomendación:** para un corte planificado con ventana de mantenimiento, **snapshot** es más simple, más barato y de copia íntegra. Si el negocio **no tolera downtime**, la vía es **DMS** (o un enfoque híbrido: snapshot para la carga inicial + DMS solo-CDC para alcanzar el corte).

## 1. Datos medidos que condicionan ambas rutas

| Dato | Valor | Impacto |
|---|---|---|
| Volumen real (`VolumeBytesUsed`) | **~322.5 GiB** | Tiempo de copia (snapshot) y de full-load (DMS) |
| Snapshot manual más reciente | `rds:www-rds-production-cluster-2026-09-02-01-05` (322 GiB, hoy) | La vía snapshot ya tiene material reciente disponible |
| Cifrado | **Sí**, KMS `mrk-a8c3d03cd28c46bfa4bf908b2951698d` | Clave **multi-región PRIMARY**, gobernada por **Seguridad TI (`520521765653`)** |
| Concurrencia pico | 719 conexiones, CPU writer **91 %** | El full-load de DMS compite con la carga productiva |
| Caudal de cambios | ~537 commits/s pico | Dimensiona el CDC de DMS |
| `binlog_format` | ROW, **pending-reboot** | Precondición de CDC; requiere reinicio efectivo |

## 2. Estrategia A — Snapshot cross-account

### 2.1 Procedimiento (resumen)
1. Tomar (o reutilizar) un snapshot manual del clúster en la cuenta origen.
2. **Compartir la KMS key** (o una copia re-cifrada) con la cuenta destino — requiere acción de **Seguridad TI**.
3. Compartir el snapshot con la cuenta destino (`844669095517`).
4. En destino: **copiar** el snapshot re-cifrándolo con una KMS propia de la cuenta PROD.
5. **Restaurar** un nuevo clúster Aurora desde el snapshot copiado.
6. Recrear parámetros, security groups, endpoints y reconectar la aplicación.

### 2.2 Beneficios
- **Copia íntegra:** incluye triggers, procedimientos, foreign keys, usuarios y objetos que DMS no migra limpiamente.
- **Simplicidad:** procedimiento nativo de RDS, sin infraestructura adicional que operar.
- **Costo bajo:** no hay instancia de replicación corriendo por días.
- **Predecible:** una sola pasada; el resultado es idéntico al origen en el instante del snapshot.

### 2.3 Riesgos y consideraciones
- **Downtime alto:** los cambios posteriores al snapshot **no** se replican. Requiere ventana de mantenimiento con la aplicación detenida (o en solo-lectura) desde el snapshot hasta el corte.
- **Dependencia de Seguridad TI (bloqueante):** la KMS es una clave *customer-managed multi-región* de la cuenta `520521765653`. Compartir/usar un snapshot cifrado cross-account **exige** que Seguridad TI autorice la política de la key hacia la cuenta destino. Sin esa autorización, la restauración cifrada no es posible.
- **Re-cifrado obligatorio:** en destino conviene copiar el snapshot con una KMS propia de PROD para no quedar atados a la key de otra cuenta.
- **Deriva de datos:** cuanto más tiempo pase entre el snapshot y el corte, más cambios se pierden. Obliga a coordinar el corte de aplicación.

### 2.4 Tiempo (variable)
| Fase | Estimación |
|---|---|
| Tomar snapshot manual (si no se reutiliza) | 15–45 min |
| Autorización + compartición KMS (Seguridad TI) | **Variable: horas a días** (depende del proceso interno) |
| Copiar snapshot a destino (re-cifrado, ~322 GiB) | 30–90 min |
| Restaurar clúster desde snapshot | 30–60 min |
| **Total técnico** (sin espera de Seguridad TI) | **~2–4 h** |
| **Downtime efectivo de la app** | Desde el snapshot hasta reconexión: **horas** |

### 2.5 Costo (variable)
- **Almacenamiento de snapshot copiado:** ~322 GiB × tarifa de backup storage/GB-mes (prorrateado por el tiempo que exista la copia).
- **Transferencia de datos** cross-account (misma región `us-east-1`): sin cargo de transferencia entre cuentas en la misma región para copia de snapshot.
- **KMS:** costo marginal por requests de cifrado/descifrado.
- **Sin costo de cómputo de replicación.**
- **Costo indirecto dominante:** el **downtime** (impacto de negocio de tener la app detenida durante el corte).

## 3. Estrategia B — AWS DMS (full-load + CDC)

### 3.1 Procedimiento (resumen)
1. Provisionar instancia de replicación DMS (ver estimación: **`dms.c6i.2xlarge`, Multi-AZ, 200 GiB**).
2. Configurar endpoints origen (writer legado) y destino (clúster nuevo, previamente creado).
3. Ejecutar **full-load** de ~322 GiB con paralelismo de tablas.
4. **CDC** replicando ~537 commits/s hasta alcanzar latencia ~0.
5. Corte: detener escrituras en origen, esperar drenaje de CDC, apuntar la app al destino.

### 3.2 Beneficios
- **Downtime mínimo (near-zero):** el CDC mantiene el destino sincronizado; el corte es de minutos.
- **Flexibilidad:** permite transformaciones, filtrado de tablas y validación de datos durante la migración.
- **No depende de compartir la KMS de origen:** DMS lee datos y los escribe en el destino con su propia configuración de cifrado.

### 3.3 Riesgos y consideraciones
- **Writer al 91 % de CPU en pico:** el full-load concurrente puede degradar la aplicación. Mitigar con ventana de baja carga.
- **`binlog ROW` pending-reboot:** el CDC falla si no está efectivamente aplicado; requiere reinicio del clúster antes de iniciar.
- **Objetos no migrados:** triggers, procedimientos almacenados y FKs requieren recreación manual post-migración.
- **Complejidad operativa:** hay una tarea DMS que monitorear (latencia de CDC, errores de tabla) durante días.
- **Retención de binlog:** subir a 24–48 h para tolerar reinicios del CDC sin pérdida.

### 3.4 Tiempo (variable)
| Fase | Estimación |
|---|---|
| Provisión DMS + endpoints | 30–60 min |
| Full-load ~322 GiB | ~3.3–6.5 h (según rendimiento efectivo) |
| CDC hasta latencia ~0 | **Horas a días** (hasta la ventana de corte acordada) |
| Corte final | Minutos |
| **Downtime efectivo de la app** | **Minutos** |

### 3.5 Costo (variable)
- **Instancia DMS `dms.c6i.2xlarge` Multi-AZ:** costo por hora **durante toda la ventana** (full-load + días de CDC). Este es el costo dominante y crece con la duración del CDC.
- **Almacenamiento DMS:** 200 GiB.
- **Transferencia:** misma región, cross-account, sin cargo relevante.
- **Sin costo de downtime** (beneficio frente a snapshot).

## 4. Enfoque híbrido (recomendado si el downtime debe ser mínimo)

1. **Snapshot** para la carga inicial (rápido e íntegro).
2. Restaurar el clúster destino desde el snapshot.
3. **DMS en modo solo-CDC** desde el punto de tiempo del snapshot para alcanzar el corte con downtime mínimo.

Combina la fidelidad y velocidad del snapshot con el downtime bajo del CDC, y reduce la ventana de full-load de DMS (menos horas de instancia = menos costo).

## 5. Matriz de decisión

| Si el driver principal es… | Elegir |
|---|---|
| Minimizar downtime | **DMS** o **Híbrido** |
| Minimizar costo y complejidad | **Snapshot** |
| Copia 100 % fiel (triggers, SP, FKs, usuarios) | **Snapshot** o **Híbrido** |
| Corte con ventana de mantenimiento tolerable | **Snapshot** |
| Independencia de la KMS de Seguridad TI | **DMS** |

## 6. Variables abiertas a confirmar con negocio/seguridad

- **Ventana de downtime tolerable** por el negocio (define snapshot vs DMS).
- **Tiempo de respuesta de Seguridad TI** para autorizar la KMS (bloqueante de la vía snapshot).
- **Fecha objetivo del corte** (define cuántos días corre el CDC y, por tanto, el costo de DMS).
- **Costos unitarios vigentes** de la cuenta (instancia DMS/hora, backup storage/GB-mes) para cerrar cifras exactas.
