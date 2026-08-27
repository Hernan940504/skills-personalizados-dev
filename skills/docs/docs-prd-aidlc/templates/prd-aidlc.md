# PRD — {{NOMBRE_PRODUCTO}}

> Product Requirements Document · Insumo para AI-DLC (AWS)
> Línea de negocio: {{LINEA_NEGOCIO}} · Tipo: {{TIPO}} (propio | interno)
> Autor: {{AUTOR}} · Fecha: {{FECHA}} · Versión: 0.1.0
> Estado: BORRADOR — cerrar los `⚠️ POR VALIDAR` antes de pasar a `/aidlc`.

---

## SOLUCIÓN

**Nombre de la solución:**
{{TODO}}

**Descripción en una línea (qué resuelve y para qué área/equipo):**
{{TODO}}

**Empresa / Organización:**
Seguros Bolívar — Grupo Bolívar

---

## 1. PROBLEMA DE NEGOCIO

**¿Cuál es el problema?** (específico, sin adjetivos vagos)
{{TODO}}

**¿Cuánto cuesta este problema?** (cuantifica: tiempo, dinero, errores, insatisfacción)
{{TODO}}

**¿Hace cuánto existe este problema?**
{{TODO}}

---

## 2. STAKEHOLDERS Y SPONSOR

**Sponsor** (persona con autoridad para aprobar recursos y adoptar la solución):
{{TODO}}

**Usuarios finales** (quiénes lo usan en el día a día):
{{TODO}}

**Quién puede bloquear la adopción** (IT, Seguridad de la Información, Compliance / Superintendencia Financiera, Arquitectura Empresarial, líder de área):
{{TODO}}

---

## 3. ESTADO ACTUAL

**¿Cómo se resuelve hoy?** (proceso manual, herramienta, workaround)
{{TODO}}

**Herramientas actuales:**
{{TODO}}

**Qué funciona bien (NO tocar):**
{{TODO}}

**Qué no funciona (oportunidad de mejora):**
{{TODO}}

---

## 4. ESTADO FUTURO DESEADO

**¿Cómo se vería el proceso si la solución funciona perfectamente?**
{{TODO}}

**¿Qué cambia para el usuario final en su día a día?**
{{TODO}}

---

## 5. CRITERIOS DE ÉXITO

> 2-3 métricas medibles que el sponsor entienda y valore. Con valor actual y target.

| Métrica | Valor actual | Target |
|---------|--------------|--------|
| {{TODO}} | {{TODO}} | {{TODO}} |
| {{TODO}} | {{TODO}} | {{TODO}} |
| {{TODO}} | {{TODO}} | {{TODO}} |

---

## 6. RESTRICCIONES

> Ver `references/seguros-bolivar-guardrails.md`. Marca lo que no conozcas como `⚠️ POR VALIDAR`.

**Técnicas** (stack aprobado, integraciones, políticas de IT, JFrog):
{{TODO}}

**De datos** (acceso, datos sensibles, Habeas Data, redacción de PII, retención ≤ 90 días):
{{TODO}}

**Organizacionales** (presupuesto, timeline, aprobaciones, change management):
{{TODO}}

**Compliance / Seguridad** (Superintendencia Financiera, aprobación dual, aislamiento entre líneas, trazabilidad):
{{TODO}}

---

## 7. ENFOQUE TÉCNICO PROPUESTO (AI-First)

**Capacidad de IA que aplica** (clasificación, extracción, generación, orquestación de agentes, automatización de workflow):
{{TODO}}

**¿Por qué IA y no automatización tradicional?**
{{TODO}}

**Arquitectura de alto nivel** (componentes principales; usa stack aprobado):
{{TODO}}

**Diseño AI-First** (endpoints estructurados/predecibles, inferencia asíncrona, versionado de modelos, sin PII en prompts, PgVector/Pinecone para similitud):
{{TODO}}

---

## 8. RIESGOS Y DEPENDENCIAS

**Riesgo 1:** {{TODO}}
**Mitigación:** {{TODO}}

**Riesgo 2:** {{TODO}}
**Mitigación:** {{TODO}}

**Riesgo 3:** {{TODO}}
**Mitigación:** {{TODO}}

**Dependencias externas** (APIs, accesos, datos de terceros, aprobaciones pendientes):
{{TODO}}

---

## 9. LÍMITES DE ALCANCE

**En alcance (lo que SÍ se construye en el MVP):**
- {{TODO}}
- {{TODO}}
- {{TODO}}

**Fuera de alcance (lo que NO se construye ahora):**
- {{TODO}}
- {{TODO}}
- {{TODO}}

---

## 10. INSUMO PARA AI-DLC (AWS)

> Esta sección conecta el PRD con el framework AI-DLC. Ver `references/aidlc-mapping.md`.

**Intent propuesto** (una frase imperativa que capture el objetivo):

```
/aidlc {{TODO: intent en una frase, p. ej. "Construir una plataforma no-code para que negocio cree agentes de IA con aprobación dual"}}
```

**Mapeo sección → fase de AI-DLC:**

| Fase AI-DLC | Se alimenta de | Qué debe producir |
|-------------|----------------|-------------------|
| Ideation | §1 Problema, §4 Estado futuro, §5 Criterios de éxito | Intent refinado, propuesta de valor |
| Inception | §2 Stakeholders, §6 Restricciones, §7 Enfoque técnico, §9 Alcance | Requirements + Design (user stories, arquitectura) |
| Gates / verificación | §8 Riesgos, §5 Criterios de éxito, aprobación dual | Criterios de aceptación por gate |

**Preguntas abiertas para Requirements/Design** (que AI-DLC deberá resolver):
- {{TODO}}
- {{TODO}}

---

## Checklist de entrega

- [ ] Problema identificado y **cuantificado** con datos reales
- [ ] Sponsor y stakeholders identificados
- [ ] Estado actual documentado (proceso, herramientas, pain points)
- [ ] Estado futuro deseado definido
- [ ] Criterios de éxito medibles (valor actual + target)
- [ ] Restricciones alineadas con los guardrails de Seguros Bolívar
- [ ] Enfoque AI-First declarado (capacidad de IA + por qué IA)
- [ ] Riesgos con mitigación y dependencias listadas
- [ ] Límites de alcance (dentro / fuera del MVP)
- [ ] Bloque AI-DLC completo (`intent` + mapeo por fase)
- [ ] Sin `⚠️ POR VALIDAR` pendientes sin responsable
- [ ] Sin PII ni datos reales de clientes/pólizas en el documento

---

*PRD generado con el skill `docs-prd-aidlc` · Seguros Bolívar*
