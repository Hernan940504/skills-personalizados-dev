# Buenas prácticas de arquitectura cloud y on-premise

Reglas comunes a los 3 proveedores para que el diagrama sea correcto, claro
y refleje decisiones sensatas. No son reglas C4 sino de **arquitectura de
infraestructura**.

---

## 1. Red — separación pública / privada

- **Subredes públicas** alojan únicamente puntos de entrada: ALB/NLB,
  proxies, NAT/Internet Gateway.
- **Subredes privadas** alojan compute (apps, workers) y BDs.
- **Las BDs NUNCA van en subred pública.** Es un anti-patrón de seguridad.
- En GCP: VPC es global, pero las subredes son regionales. Aplica el mismo
  principio público/privado.

## 2. Alta disponibilidad — multi-AZ / multi-zona

- En producción modela **≥ 2 AZs** (AWS) o **≥ 2 zonas** (GCP).
- Servicios compute (Lambda, EC2, Cloud Run, app servers on-prem) se
  modelan en cada AZ/zona.
- BDs gestionadas (RDS Multi-AZ, Cloud SQL HA) se modelan como UNA caja con
  `description: "Multi-AZ"` o como dos cajas si quieres mostrar la réplica.

## 3. Punto de entrada único

Toda arquitectura debería tener un punto de entrada controlado:
- AWS: Route 53 → CloudFront → ALB/API Gateway → backend.
- GCP: Cloud DNS → Cloud Load Balancing (con Cloud Armor) → backend.
- OnPrem: ISP → Firewall → LB → Web/App servers.

Si te faltan piezas (sin DNS, sin LB, sin WAF), pregúntate por qué — quizás
sea ambiente no productivo, o falta cobertura en el diseño.

## 4. Identidad y secretos

- Modela `iam` / IAM siempre que sea relevante para la conversación.
- Para secretos: `secrets_manager` (AWS), `cloud_kms` (GCP).
- Si el usuario menciona "claves API hard-coded" o "credenciales en el código"
  → señala el riesgo explícitamente en la justificación del diagrama.

## 5. Observabilidad

Incluye al menos un servicio de monitoreo y logs:
- AWS: `cloudwatch`, `cloudtrail`.
- GCP: `cloud_monitoring`, `cloud_logging`.
- OnPrem: si usan Prometheus / Grafana / ELK self-hosted, modélalos como
  `server` con `technology` específica.

## 6. Bases de datos — gestionadas vs autohospedadas

- En cloud, prefiere servicios gestionados (`rds`, `aurora`, `dynamodb`,
  `cloud_sql`, `firestore`, `bigquery`) — etiqueta la decisión en
  `description` si no es obvia.
- En on-prem, las BDs van como `database` (cilindro) con su tecnología y
  versión explícitas.

## 7. Mensajería y eventos

- Marca con `async:true` todas las relaciones que cruzan colas / topics /
  pub-sub.
- Modela colas/topics como servicios propios (`sqs`, `sns`, `pubsub`,
  `kafka` on-prem), no como flechas implícitas.

## 8. Anti-patrones que debe señalar el agente

Al revisar la descripción del usuario, llama la atención si detectas:
- BD en subnet pública.
- Apps con acceso directo a internet sin LB/Firewall.
- Single AZ en producción.
- Servicios sin observabilidad declarada.
- Secretos en variables de entorno hard-coded (cuando hay servicios de
  secretos disponibles).
- Permisos `*:*` en IAM (cuando se discute).
- Pub/Sub directo a una sola BD sin buffer (acoplamiento fuerte).

Es legítimo mostrar el diagrama "tal cual existe" hoy, pero indica los
riesgos en la justificación.

## 9. Tamaño del diagrama

- ≤ ~25 servicios en pantalla.
- Si te pasas:
  - Divide por **capa**: red, compute, datos, observabilidad, seguridad.
  - Divide por **dominio**: ventas, fulfillment, analytics.
  - Cada división en su propio `.drawio` con un trozo coherente.

## 10. Convenciones de nombres

- Nombres reales del proyecto cuando los conozcas (`api-orders-prod`,
  `vpc-data-platform`, `db.r6g.large`).
- Cuando no los conoces, usa nombres descriptivos: `Get Orders Function`,
  `Internal API`, `Orders DB`.
- CIDR en grupos cuando ayuda: `vpc 10.0.0.0/16`, `subnet 10.0.1.0/24`.

## 11. Trazabilidad

- Versiona los `.drawio` en git (XML hace buen diff).
- Acompaña con un ADR que explique decisiones críticas (por qué multi-region,
  por qué Aurora vs RDS, por qué Cloud Run vs GKE).
- Nombre recomendado: `arquitectura-<sistema>-<provider>.drawio`.

---

## Checklist antes de entregar

- [ ] Provider elegido y consistente en todo el archivo.
- [ ] BDs en subredes privadas.
- [ ] ≥ 2 AZs / zonas si es producción.
- [ ] Punto de entrada con LB / API Gateway / Firewall.
- [ ] IAM y secretos modelados si aplican.
- [ ] Observabilidad presente (logs/métricas).
- [ ] Colas / pub-sub marcadas con `async:true`.
- [ ] ≤ ~25 servicios en pantalla.
- [ ] Cada elemento con `description` informativa.
- [ ] Relaciones con descripción + protocolo cuando aporten.
- [ ] El `.drawio` abre y valida sin errores.
- [ ] Justificaste decisiones de red y HA en el mensaje.
- [ ] Señalaste los anti-patrones que detectaste (si los hubo).
