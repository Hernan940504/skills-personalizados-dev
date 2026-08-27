# Mapeo del PRD → framework AI-DLC (AWS)

Cómo el PRD alimenta el **AI-Driven Development Life Cycle (AI-DLC)** de AWS.
El PRD es el **insumo** que se entrega antes de invocar `/aidlc`; no reemplaza
las fases, las nutre.

> Referencias: AWS DevOps blog "AI-Driven Development Life Cycle" y
> `awslabs/aidlc-workflows` (docs: awslabs.github.io/aidlc-workflows).
> Contenido reformulado para cumplimiento de licencias.

---

## Qué es AI-DLC (resumen)

Metodología que estructura el desarrollo asistido por IA en fases repetibles y
trazables, manteniendo al humano en control en cada punto de decisión. Se
invoca con un solo comando:

```
/aidlc <intent>
```

A partir del `intent`, guía un flujo: **intent → requirements → design →
implementation → testing → deployment**, con puntos de aprobación (gates) entre
etapas.

**Fases (5):** Initialization, Ideation, Inception, Construction, Operation.

- **Initialization** — arranque determinístico; crea el espacio/intent. No
  requiere insumo del PRD.
- **Ideation** — clarifica y refina el intent y la propuesta de valor.
- **Inception** — genera requirements y design (historias de usuario,
  arquitectura) a partir del contexto.
- **Construction** — implementación, código y pruebas.
- **Operation** — despliegue y operación.

El PRD alimenta principalmente **Ideation** e **Inception**, y aporta los
criterios para los **gates**.

---

## Tabla de mapeo (sección PRD → fase AI-DLC)

| Sección del PRD | Fase AI-DLC que alimenta | Cómo se usa |
|---|---|---|
| §1 Problema de negocio | Ideation | Justifica el intent; contexto del "por qué". |
| §4 Estado futuro deseado | Ideation | Define el resultado esperado / propuesta de valor. |
| §5 Criterios de éxito | Ideation + Gates | Métricas → criterios de aceptación medibles. |
| §2 Stakeholders y sponsor | Inception | Actores para historias de usuario; quién aprueba. |
| §3 Estado actual | Inception | Restricciones del proceso vigente a respetar. |
| §6 Restricciones | Inception | Límites técnicos/datos/compliance del design. |
| §7 Enfoque técnico (AI-First) | Inception | Base de la arquitectura propuesta. |
| §9 Límites de alcance | Inception | Define qué entra/sale del primer ciclo. |
| §8 Riesgos y dependencias | Gates / verificación | Condiciones que deben vigilarse en cada gate. |

---

## Cómo escribir el `intent`

El `intent` es una frase imperativa que captura el objetivo, no la solución
detallada. Debe ser lo bastante específico para orientar y lo bastante abierto
para que AI-DLC proponga el diseño.

Bueno:
```
/aidlc Construir una plataforma no-code para que negocio cree y apruebe agentes de IA con aprobación dual
```

Débil (demasiado vago):
```
/aidlc Hacer una plataforma de IA
```

Demasiado prescriptivo (invade la fase de design):
```
/aidlc Crear un React con FastAPI, tabla agents en PostgreSQL y endpoint POST /agents que...
```

---

## Buenas prácticas de handoff

- Entrega el PRD **con los `⚠️ POR VALIDAR` cerrados**; los pendientes se vuelven
  ambigüedad que AI-DLC no puede resolver solo.
- Las **preguntas abiertas** del §10 del PRD son insumo directo para la etapa de
  Requirements: déjalas explícitas.
- Mantén el PRD versionado junto al código/artefactos de la iniciativa.
- El PRD describe el "qué" y el "porqué"; deja el "cómo" detallado para
  Inception/Construction de AI-DLC.
