# Checklist de calidad del PRD (antes de entregar / pasar a /aidlc)

Recórrela antes de dar el PRD por terminado. Un ítem sin cumplir es trabajo
pendiente, no un detalle.

## Contenido

- [ ] La iniciativa está clasificada (producto propio vs problema interno).
- [ ] El problema está **cuantificado** (número o hecho verificable, no adjetivos).
- [ ] Sponsor con autoridad identificado.
- [ ] Usuarios finales y quién puede **bloquear** la adopción identificados.
- [ ] Estado actual documentado, incluyendo lo que funciona y NO se toca.
- [ ] Estado futuro descrito como resultado para el usuario, no como lista de features.
- [ ] 2-3 criterios de éxito **medibles** con valor actual y target.
- [ ] Riesgos con mitigación accionable y dependencias externas listadas.
- [ ] Límites de alcance: qué SÍ y qué NO entra en el MVP.

## Alineación con Seguros Bolívar

- [ ] Stack propuesto dentro de lo aprobado (ver guardrails).
- [ ] Manejo de PII declarado (redacción antes de modelos de IA).
- [ ] Retención de datos sensibles ≤ 90 días considerada.
- [ ] Aprobación dual / supervisión humana indicada si aplica.
- [ ] Dependencias vía JFrog y versiones pineadas mencionadas si hay stack.

## Enfoque AI-First

- [ ] Capacidad de IA declarada (clasificación / extracción / generación /
      orquestación / automatización de workflow).
- [ ] Justificación de por qué IA y no automatización tradicional.
- [ ] Salida estructurada + inferencia asíncrona contempladas.

## Insumo para AI-DLC

- [ ] `intent` propuesto en una frase imperativa (ni vago ni prescriptivo).
- [ ] Tabla de mapeo sección → fase completa.
- [ ] Preguntas abiertas para Requirements/Design listadas.

## Higiene

- [ ] Sin `⚠️ POR VALIDAR` sin responsable de cierre.
- [ ] Sin PII ni datos reales de clientes/pólizas en el documento ni en ejemplos.
- [ ] Archivo guardado en `lineas_negocio/<linea>/prd-<producto>.md`.
- [ ] CHANGELOG del proyecto actualizado.
