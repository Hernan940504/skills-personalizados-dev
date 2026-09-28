# Requirements — Diagrama de componentes AWS Ciencuadras

| Campo | Valor |
|---|---|
| Producto | Arquitectura de componentes Ciencuadras en AWS |
| Artefacto principal | `lineas_negocio/ciencuadras/arquitectura-componentes-ciencuadras-aws.drawio` |
| Estado | Aprobado para elaboración con inventario de solo lectura |
| Fecha de evidencia | 2026-09-23 |
| Clasificación | Interno |

## Objetivo

Entregar un diagrama Draw.io nativo que describa la arquitectura de componentes de Ciencuadras a partir del inventario AWS de Desarrollo y de las características verificadas de los entornos operativos, especialmente Producción.

## Requisitos funcionales

1. El archivo debe abrirse en draw.io/diagrams.net como un único documento con cuatro páginas:
   - panorama de componentes por environment;
   - catálogo de componentes del environment DEV;
   - topología de componentes objetivo para PROD;
   - catálogo detallado de capacidades funcionales de DEV.
2. La organización visible debe usar exclusivamente boundaries de environment (`DEV`, `PRE`, `STAGE`, `PROD`) y capacidades técnicas. No debe mostrar IDs de cuenta, ARN, CIDR, nombres internos de recursos ni secretos.
3. Cada vista debe incluir íconos AWS nativos y relaciones etiquetadas con propósito y protocolo cuando exista evidencia.
4. La vista DEV debe representar los componentes inventariados: CDN, API Gateway, VPC Link, balanceo interno, ECS/Fargate, Aurora MySQL, ElastiCache, S3, SQS, Lambda, Cognito, ECR, Systems Manager, WAF y observabilidad.
5. La vista PROD debe reflejar las características verificadas: tres AZ, subredes públicas y privadas, CloudFront con orígenes S3/API Gateway/ALB, balanceadores públicos e internos, API Gateway con VPC Link, ECS/Fargate, Aurora MySQL cifrada, almacenamiento de objetos, mensajería, funciones/automatización, seguridad, observabilidad y entrega continua.
6. El modelo debe agrupar cargas equivalentes por capacidad funcional, usando metadata de tooltip/propiedades para conservar detalle sin publicar nomenclatura interna.

## Requisitos no funcionales y de seguridad

- Las fuentes AWS se consultan únicamente con rol de lectura y la evidencia queda resumida, sin exportar configuraciones sensibles ni datos de negocio.
- Los componentes no observados directamente no se presentarán como hechos. Las integraciones lógicas agregadas se identificarán como patrones de capacidad.
- La persistencia objetivo de medios de WordPress se modelará en S3; EFS legado no forma parte del estado objetivo.
- El diagrama debe ser legible por página y conservar las relaciones dentro de su contexto de environment.

## Criterios de aceptación

- [ ] El archivo `.drawio` es XML válido y contiene exactamente cuatro páginas.
- [ ] Las cuatro páginas se abren sin advertencias en draw.io y usan shapes AWS oficiales.
- [ ] Los labels visibles no contienen cuentas, ARNs, CIDR, IDs de recursos, endpoints ni secretos.
- [ ] Las relaciones de entrada CloudFront → S3/API Gateway/ALB y API Gateway → VPC Link → balanceadores internos están representadas.
- [ ] DEV y PROD muestran sus diferencias de capacidad y topología, sin asumir paridad completa entre ambos.
