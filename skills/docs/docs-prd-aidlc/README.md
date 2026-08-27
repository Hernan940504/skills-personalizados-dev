# docs-prd-aidlc

> Skill para **definir el PRD (Product Requirements Document)** de un producto o
> iniciativa de Seguros Bolívar y dejarlo listo como **insumo del framework
> AI-DLC de AWS**. Conduce una entrevista guiada de 9 secciones, cuantifica cada
> afirmación y produce un PRD en Markdown que termina en un `intent` accionable
> para `/aidlc`.

---

## Qué hace

1. Clasifica la iniciativa: **producto propio** (Product Vision Board) o
   **problema interno** (Internal Solution Brief).
2. Recorre 9 secciones sin omitir ninguna: problema, sponsor/stakeholders,
   estado actual, estado futuro, criterios de éxito, restricciones, enfoque de
   IA, riesgos y límites de alcance.
3. Aplica los **guardrails de Seguros Bolívar** (stack aprobado, JFrog,
   PostgreSQL/PgVector/Pinecone, gateway de IA interno, aprobación dual, Habeas
   Data, redacción de PII, retención ≤ 90 días).
4. Cierra con el bloque **"Insumo para AI-DLC"**: el `intent` propuesto y el
   mapeo sección → fase (Ideation / Inception / gates).

Salida: `lineas_negocio/<linea-negocio>/prd-<nombre-producto>.md`.

---

## Por qué existe

El material de la Estación 1 de Hardcore AI (Internal Solution Brief y Product
Vision Board) es un excelente punto de partida, pero es genérico. Este skill lo
adapta a la realidad de Seguros Bolívar y lo conecta con el flujo real de
trabajo: el PRD deja de ser un documento de presentación y se convierte en el
**insumo estructurado que alimenta `/aidlc`** (fases Ideation e Inception del
AI-DLC de AWS). Así, la transición de "idea" a "requisitos y diseño asistidos
por IA" no pierde contexto.

---

## Prompts que activan este skill

```
"Ayúdame a definir el PRD del nuevo producto de cotización de vida"
"Quiero preparar el insumo para AI-DLC de mi iniciativa de agentes"
"Necesito un internal solution brief para un problema interno"
"Arma el product requirements document de Hefesto"
"Documenta el intent y los requisitos para pasar a /aidlc"
```

## Prompts que NO deberían activarlo

```
"Hazme el diagrama de arquitectura AWS"        → docs-arch-cloud
"Genera el C4 de contexto"                      → docs-c4-context
"Crea el endpoint REST de cotización"           → skills backend
```

---

## Estructura

```
docs-prd-aidlc/
├── SKILL.md                              # manifest para el agente
├── README.md                             # este archivo (para humanos)
├── scripts/
│   └── new-prd.sh                        # scaffold del PRD por línea de negocio
├── templates/
│   └── prd-aidlc.md                      # plantilla del PRD (9 secciones + AI-DLC)
└── references/
    ├── prd-fill-guide.md                 # qué preguntar por sección, errores comunes
    ├── aidlc-mapping.md                  # mapeo PRD → fases de AI-DLC (AWS)
    ├── seguros-bolivar-guardrails.md     # restricciones de stack, datos, compliance
    └── prd-checklist.md                  # checklist de calidad antes de entregar
```

---

## Uso manual

Crear el archivo del PRD ya nombrado y ubicado:

```bash
skills/docs/docs-prd-aidlc/scripts/new-prd.sh "hefesto" "mercadeo" interno
# → crea lineas_negocio/mercadeo/prd-hefesto.md desde la plantilla
```

Luego se completa el contenido siguiendo el workflow del `SKILL.md`.

---

## Pre-requisitos

- `bash` disponible (macOS/Linux). El scaffold es un script POSIX simple.
- No requiere runtimes adicionales: el skill produce Markdown.
- Conocer quién es el **sponsor** de la iniciativa (para cerrar los
  `⚠️ POR VALIDAR`).

---

## Cómo extenderlo o ajustarlo

- Cambiar la ubicación por defecto de salida → editar `scripts/new-prd.sh`.
- Añadir/quitar secciones del PRD → editar `templates/prd-aidlc.md` y su reflejo
  en el `SKILL.md` (Paso 2 del workflow).
- Actualizar restricciones corporativas → editar
  `references/seguros-bolivar-guardrails.md` (fuente única de esas reglas).

---

## Relación con otros skills

| Después del PRD… | Skill sugerido |
|---|---|
| Diagrama de contexto de negocio | `docs-c4-context` |
| Contenedores / componentes | `docs-c4-containers`, `docs-c4-components` |
| Arquitectura cloud con íconos | `docs-arch-cloud` |
| Requirements/Design detallados | `/aidlc` (framework AWS AI-DLC) |

---

## Limitaciones conocidas

| Limitación | Workaround |
|---|---|
| No inventa datos: si no hay número, marca `⚠️ POR VALIDAR` | El sponsor cierra los pendientes antes de `/aidlc` |
| No decide el alcance del MVP por ti | Se define en entrevista (Paso 2) |
| No ejecuta AI-DLC — solo prepara su insumo | Correr `/aidlc <intent>` en el harness correspondiente |
