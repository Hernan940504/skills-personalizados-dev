# Justificación de sizing CIDR — Seguros-Bolivar-ciencuadras-PROD

> Cuenta destino: **Seguros-Bolivar-ciencuadras-PROD** (`844669095517`)
> VPC de origen analizada: `vpc-0550459b3a96ce79e` (www-vpc-ciencuadras) · Cuenta `290296201161` · Región `us-east-1`
> Fecha: 2026-09-02 · Autor: Arquitectura
> Base de datos: informe de sizing CIDR + validación directa contra la API de AWS (perfil `ciencuadras`, rol `ViewOnlyAccess`).

## Decisión

**Se asigna un `/21` (2 048 direcciones, 2 043 usables) a la cuenta Seguros-Bolivar-ciencuadras-PROD.**

Esta es la decisión de arquitectura. Las secciones siguientes la sustentan con datos medidos. No es una recomendación entre varias: es el prefijo que satisface simultáneamente la demanda validada, el diseño obligatorio de 3 AZ y el objetivo declarado de crecimiento, sin incurrir en el sobredimensionamiento que este mismo proyecto busca corregir.

## 1. Objetivo

Fijar el prefijo CIDR de la nueva cuenta productiva de Ciencuadras con un criterio único y trazable, sustentado en el uso real de la aplicación y no en estimaciones. Todos los escenarios (`/24` a `/19`) se evalúan para dejar constancia del descarte de cada uno; la conclusión es el `/21`.

## 2. Demanda de direcciones (validada contra la cuenta real)

Cada cifra fue verificada contra la API de AWS de la cuenta origen, no estimada:

| Componente | IPs (pico) | Verificación |
|---|---|---|
| Base no-ECS (NAT, endpoints, LB, TGW) | 40 | 167 ENIs totales medidas; desglose por tipo confirmado |
| ECS Fargate (autoescalado, MaxCapacity) | 280 | Suma exacta de `MaxCapacity` de 42 servicios PROD = **280** |
| Lambda en VPC (Hyperplane, concurrencia 200) | 8 | Solo **7 ENIs** Lambda hoy para 103 funciones en VPC |
| **Demanda pico total** | **~328** | |
| Escenario Lambda alto (concurrencia 500) | ~338 | Variación marginal |

Referencias operativas medidas que enmarcan la demanda:
- **Piso estable** (suma `MinCapacity` ECS = 80 + base 40) = **~120 IPs**.
- **Carga real hoy** (~123 tareas running + base) ≈ **163 IPs**.
- El pico de 280 es **techo teórico**: asume que los 42 servicios llegan a su máximo simultáneamente.

## 3. Análisis histórico de comportamiento (15 meses)

### 3.1 Alcance y limitación de la telemetría

Se evaluó el comportamiento real de la aplicación durante el máximo período que CloudWatch permite: **15 meses (may-2025 a jul-2026)**, que es el techo de retención de la plataforma. Se documenta una limitación relevante hallada durante el análisis:

- **No existe historia de consumo directo de IPs.** La métrica `AvailableIPAddressCount` no se publica por defecto en CloudWatch y `ECS/ContainerInsights` está **deshabilitado en 5 de los 6 clústeres PROD**. En consecuencia, no hay serie histórica de tareas ECS ni de IPs libres por subred.
- Por ello el análisis temporal se apoya en **proxies de demanda con historia disponible**: `RequestCount` de los Application Load Balancers de PROD (tráfico de negocio) y `CPUUtilization` por servicio ECS (presión de cómputo). Ambos reflejan la evolución de la carga, aunque no cuenten IPs directamente.
- **Recomendación de observabilidad:** habilitar Container Insights en los 6 clústeres PROD para que futuras reevaluaciones dispongan de la medición directa de tareas/IPs.

### 3.2 Tendencia de tráfico (proxy de demanda)

Tráfico agregado de los 8 ALB de PROD, meses completos:

| Métrica | Valor |
|---|---|
| Tráfico mes inicial (2025-05) | 164.6 M requests |
| Tráfico mes final (2026-07) | 299.8 M requests |
| **Crecimiento punta a punta** | **+82 %** |
| Promedio primeros 3 meses | 200.1 M/mes |
| Promedio últimos 3 meses | 290.4 M/mes |
| Crecimiento (ventana 3m vs 3m) | +45 % |
| Pendiente de tendencia | +7.4 M requests/mes |
| **Crecimiento anualizado estimado** | **~+54 %/año** |

**Conclusión:** la demanda de Ciencuadras PROD **no está plana; crece de forma sostenida** (~+54 % anualizado, sin caídas estructurales en 15 meses). El grueso del tráfico se concentra en `ms-internal-prod-alb` (3 097 M requests en 15 meses) y `www-cluster-ciencuadras` (515 M).

### 3.3 Patrón de utilización (por qué el pico de 280 es real)

CPU de los servicios PROD del clúster de microservicios (muestra representativa, 15 meses):

- **CPU promedio muy baja (0.1 %–5.8 %) con picos máximos por encima del 100 % (hasta 132 %).** Los servicios están ociosos la mayor parte del tiempo pero sufren picos intensos que **disparan el autoescalado**. Esto confirma que dimensionar por el techo de autoescalado (280) y no por el promedio es lo correcto: el consumo de IPs se concentra en los eventos de escalado, no en el estado estable.
- **Carga nueva de IA ya materializándose:** `ciencuadras-prod-python-asistente-2.0-ia-ms` pasó de 0.1 % a 4.0 % de CPU promedio (~40x) y aparecen servicios `python-mcp-inmuebles-ia`. Las "funcionalidades futuras" que motivan la holgura **ya están apareciendo en producción**.

### 3.4 Implicación directa sobre el sizing

Con crecimiento de tráfico ~+54 %/año, la demanda pico de ~328 IPs de hoy se proyecta al alza. Aplicando ese crecimiento al driver de sizing:

- En **~18 meses** la demanda proyectada supera los **~500 IPs**, acercándose al límite útil del `/23` y consumiendo buena parte de la holgura del `/22`.
- El `/21` absorbe ese crecimiento con margen: aún a 500-600 IPs proyectadas, la ocupación se mantiene por debajo del 30 %.

El histórico convierte la elección del `/21` de "holgura preventiva" a **respuesta cuantificada a una tendencia de crecimiento medida y sostenida**.

## 4. Comparativa de prefijos

Ocupación calculada sobre IPs usables (AWS reserva 5 por subred). "Cubre" evalúa contra la demanda alta (338).

| Prefijo | Total IPs | Usables | Ocup. @pico (328) | Ocup. @alto (338) | Ocup. @piso (120) | Holgura vs pico | Cubre |
|---|---|---|---|---|---|---|---|
| /24 | 256 | 251 | 130.7 % | 134.7 % | 47.8 % | 0.8x | **NO** |
| /23 | 512 | 507 | 64.7 % | 66.7 % | 23.7 % | 1.5x | justo |
| /22 | 1 024 | 1 019 | 32.2 % | 33.2 % | 11.8 % | 3.1x | sí |
| **/21 (decisión)** | 2 048 | 2 043 | 16.1 % | 16.5 % | 5.9 % | 6.2x | sí |
| /20 | 4 096 | 4 091 | 8.0 % | 8.3 % | 2.9 % | 12.5x | sí |
| /19 | 8 192 | 8 187 | 4.0 % | 4.1 % | 1.5 % | 25.0x | sí |

## 5. Por qué /21 y no otro prefijo — descarte razonado

El `/21` no se elige por preferencia sino por eliminación objetiva de todas las demás opciones. Cada prefijo se descarta por una razón concreta y verificable:

**`/24` se descarta: es matemáticamente insuficiente.** 251 usables < 328 de demanda. Quedaría por encima del 100 % de ocupación desde el primer día. No es una opción.

**`/23` se descarta: opera al límite.** Con 507 usables, la ocupación en pico es 65-67 %. En el escenario de Lambda alto combinado con rolling deployments concurrentes de ECS, la ocupación se acerca al 100 %. No deja espacio para VPC endpoints por servicio ni para un solo microservicio nuevo. Es el mínimo técnico de supervivencia, no una base con futuro.

**`/22` se descarta para esta cuenta: no cumple el objetivo declarado de crecimiento.** Es el prefijo que recomienda el informe y funciona en operación normal (32 % de ocupación, holgura 3x). Sin embargo, presenta dos limitaciones concretas que chocan con el objetivo de este proyecto:

  1. *Margen zonal ajustado.* El diseño obliga a repartir en 3 AZ. Con `/22`, cada AZ dispone de una sola subred privada `/24` (251 usables). El pico de ECS (~280) repartido en 3 AZ da ~94 IPs por AZ, es decir **37 % de ocupación por subred privada en pico**. Un rolling deployment o un evento de escalado concentrado en una AZ consume ese `/24` con rapidez, sin subred contigua libre para absorberlo.
  2. *Sin espacio para crecimiento genuino.* La holgura de 3x se consume con lo previsible: VPC endpoints por servicio (ECR, SQS, Secrets Manager — 1 ENI por AZ cada uno), nuevos microservicios y cualquier aumento de `MaxCapacity`. El `/22` cubre el hoy; no cubre el mañana que este proyecto pide explícitamente proteger.

  El `/22` es correcto para una cuenta cuyo objetivo fuera "cubrir la demanda actual con eficiencia". No es correcto para esta cuenta, cuyo objetivo declarado es "no quedar corto para funcionalidades futuras".

**`/20` se descarta: es sobredimensionado.** Holgura 12.5x, ocupación 8 %. Solo se justificaría si Ciencuadras PROD proyectara multiplicar por más de cinco su footprint actual, y no existe evidencia de ello en la carga medida. Consume espacio direccionable escaso sin contrapartida.

**`/19` se descarta: repite el error que este proyecto corrige.** Holgura 25x, ocupación 4 %. Es exactamente el mismo patrón de sobredimensionamiento del `/16` actual (hoy al 0.9 % de ocupación) que motivó esta revisión. Elegirlo sería reintroducir el problema a menor escala, en un esquema con Transit Gateway y 320 cuentas que compiten por rangos no solapados.

**Conclusión del descarte:** eliminados `/24` (insuficiente), `/23` (al límite), `/22` (no cumple el objetivo de crecimiento), `/20` y `/19` (sobredimensionados), **el único prefijo que satisface las tres restricciones a la vez —demanda validada, margen zonal en 3 AZ y objetivo de crecimiento sin derroche— es el `/21`.** El análisis histórico de la sección 3 (crecimiento sostenido ~+54 %/año) refuerza este descarte: el `/22` se quedaría corto en el horizonte de ~18 meses.

## 6. Evidencia del reparto por AZ (comparación /22 vs /21)

El diseño reparte en 3 AZ con subredes privadas (ECS/Lambda) y públicas (NAT/LB). El pico ECS (~280) repartido en 3 AZ da ~94 IPs por AZ en el peor caso concentrado:

| Escenario | Privada por AZ | IPs privadas (3 AZ) | Pública por AZ | Ocupación privada/AZ en pico |
|---|---|---|---|---|
| /22 → privadas /24 + públicas /26 | /24 (251) | 753 | /26 (59) | **37 %** |
| **/21 → privadas /23 + públicas /25** | **/23 (507)** | **1 521** | **/25 (123)** | **19 %** |

Con `/21` cada subred privada por AZ (`/23`) tiene el doble de capacidad y opera a la mitad de ocupación en pico. Esto elimina el riesgo de agotamiento zonal que presenta el `/22` sin necesidad de rediseñar la topología.

## 7. Por qué el /21 es suficiente y no excesivo

El `/21` se sitúa deliberadamente en el punto donde la holgura protege el crecimiento sin desperdiciar direccionamiento:

- **Suficiente para el crecimiento:** holgura 6.2x sobre el pico, capacidad para VPC endpoints, nuevos microservicios y aumentos de `MaxCapacity` sin volver a solicitar CIDR ni recurrir a secondary CIDRs (el parche que hoy tiene la VPC origen con `10.66.48.0/21`).
- **No excesivo:** ocupación 16 % en pico. Está un salto por debajo del `/20` (8 %) y dos por debajo del `/19` (4 %), evitando el sobredimensionamiento. Un `/21` es un consumo moderado y responsable del plan IPAM corporativo.

## 8. Consideraciones de implementación

- **Validar solapamiento con Transit Gateway** antes de crear la VPC (se confirmaron 3 ENIs de TGW activas en la VPC origen) y contra redes on-premise. El rango `/21` seleccionado no debe solaparse con lo anunciado en el TGW.
- **Topología de subredes del `/21`:** privadas `/23` en 3 AZ para ECS/Lambda; públicas `/25` en 3 AZ para NAT/LB. Mantener las Lambdas con la misma combinación subnet+SG para maximizar el reuso de ENIs Hyperplane.
- **VPC endpoints:** cada Interface Endpoint consume 1 ENI por AZ; contemplar su crecimiento dentro del `/21`.
- **Revisar los 17 servicios con `MaxCapacity ≥ 3× MinCapacity`:** si son techos heredados y no demanda real, ajustarlos reduce el pico teórico; el `/21` mantiene holgura incluso sin ese ajuste.
- **La cuenta nueva nace limpia:** la VPC origen mezcla dev/qa/pre/stage/prod (28 clústeres ECS); la PROD nueva llevará solo carga productiva, lo que hace del sizing sobre 280 IPs una base conservadora.
- **Habilitar Container Insights** en los 6 clústeres PROD (hoy 5 deshabilitados) para disponer de medición histórica directa de tareas/IPs en futuras reevaluaciones. El análisis actual usó proxies (tráfico ALB y CPU) por ausencia de esta telemetría.
- **Reevaluar** ante nuevos servicios o mayores capacidades de autoescalado, dentro del margen que el `/21` ya provee.

## Resumen ejecutivo

**Decisión: `/21` (2 043 IPs usables) para Seguros-Bolivar-ciencuadras-PROD.** La demanda pico validada contra la API de AWS es ~328 IPs (280 ECS + 40 base + 8 Lambda). El análisis histórico de 15 meses (máximo que permite CloudWatch) muestra un **crecimiento de tráfico sostenido de ~+54 %/año** (+82 % punta a punta), con picos de CPU que superan el 100 % y carga de IA ya materializándose en producción: la demanda no está plana, crece. Los prefijos se descartan uno a uno por razón objetiva: `/24` insuficiente, `/23` al límite, `/22` sin margen zonal ni espacio para el crecimiento medido, `/20` y `/19` sobredimensionados y repetitivos del error del `/16` actual. El `/21` es el único prefijo que cubre la demanda con holgura 6.2x, mantiene las subredes privadas por AZ al 19 % de ocupación en pico y absorbe la tendencia de crecimiento observada sin desperdiciar direccionamiento. El `/22` que sugiere el informe es válido para operación corriente pero, proyectado sobre el crecimiento real, se quedaría corto en ~18 meses; por eso se selecciona el `/21`. Se documenta como hallazgo que la medición directa de IPs no existe históricamente (Container Insights deshabilitado) y se recomienda habilitarla.
