# docs-c4-context

> Skill especializado en **C4 Nivel 1 (Contexto)** — genera un `.drawio` con
> el sistema en foco como caja negra, sus actores y los sistemas externos.
> **Lenguaje de negocio**, sin tecnologías. Pensado para presentaciones a
> stakeholders y conversaciones de Arquitectura Empresarial.

---

## Qué hace

1. Define **un único sistema en foco** (`scope:true`).
2. Identifica actores (`person`) y sistemas externos (`system` + `external:true`).
3. Etiqueta las relaciones con **intención de negocio**, no protocolos.
4. Genera el `.drawio` vía `skills/_lib/drawio/render.py` (motor compartido).

Salida: `c4-contexto-<sistema>.drawio` listo para abrir en draw.io desktop o
app.diagrams.net.

---

## Prompts que activan este skill

```
"Hazme un C4 de contexto del sistema de facturación"
"Diagrama nivel 1 con los actores y sistemas externos"
"Necesito el contexto para una presentación a negocio"
"System context diagram en draw.io"
"Visión general de cómo encaja el sistema X en la organización"
```

---

## Estructura

```
docs-c4-context/
├── SKILL.md
├── README.md
├── scripts/
│   └── generate.sh              # wrapper → ../../_lib/drawio/render.py c4
├── templates/
│   └── context.example.json     # ejemplo Nivel 1 (banca por internet)
└── references/
    ├── c4-context-guide.md      # qué preguntar, qué incluir/excluir
    └── best-practices-context.md# checklist y anti-patrones
```

El generador real vive en `skills/_lib/drawio/` (motor compartido por los 4
skills C4/cloud). Este skill solo aporta el prompt especializado y los
materiales de referencia.

---

## Uso manual

```bash
python3 skills/_lib/drawio/render.py c4 c4-contexto.json c4-contexto.drawio
```

o el wrapper local:

```bash
skills/docs/docs-c4-context/scripts/generate.sh c4-contexto.json c4-contexto.drawio
```

---

## Reglas duras (Nivel 1)

- **Solo** tipos `person` y `system`. Nada de `container`, `component`,
  `database` ni `queue`.
- **Un único** elemento con `scope:true`.
- Descripciones en lenguaje de negocio.
- Relaciones describen intención, no protocolos.
- ≤ ~15 elementos. Si necesitas más, considera un **System Landscape** o
  varios contextos por dominio.

Si necesitas mostrar tecnologías, BDs o componentes internos: usa
`docs-c4-containers` (Nivel 2) o `docs-c4-components` (Nivel 3) — un
`.drawio` por nivel.

---

## Limitaciones conocidas

| Limitación | Workaround |
|---|---|
| El skill no decide qué es interno/externo por ti | Pregunta al usuario o asume convención de la organización |
| No infiere relaciones desde código | Construye el modelo desde la descripción del usuario |
| Layout automático en 3 filas | Reorganiza con `Arrange > Layout` en draw.io |
