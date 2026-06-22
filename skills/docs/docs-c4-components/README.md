# docs-c4-components

> Skill especializado en **C4 Nivel 3 (Componentes)** — genera un `.drawio`
> con zoom a UN solo contenedor y sus piezas internas (controllers, services,
> repositories, gateways, módulos). Pensado para los desarrolladores de ese
> contenedor.

---

## Qué hace

1. Define **un único contenedor en foco** (`scopeBoundary` = nombre del contenedor).
2. Modela sus componentes internos como `component` con `scope:true`.
3. Modela dependencias externas (BD, colas, otros contenedores, sistemas
   externos) con `external:true`.
4. Genera el `.drawio` vía `skills/_lib/drawio/render.py` (motor compartido).

Salida: `c4-componentes-<contenedor>.drawio`.

---

## Prompts que activan este skill

```
"Componentes de la API de pedidos en draw.io"
"C4 nivel 3 del servicio de pagos"
"Cómo está estructurada por dentro la API"
"Controllers, services y repositories del microservicio"
"Diagrama interno del worker de eventos"
```

---

## Estructura

```
docs-c4-components/
├── SKILL.md
├── README.md
├── scripts/
│   └── generate.sh                   # wrapper → ../../_lib/drawio/render.py c4
├── templates/
│   └── components.example.json       # ejemplo N3 (API de Pedidos, layered)
└── references/
    ├── c4-components-guide.md        # qué es un componente, granularidad
    ├── component-decomposition.md    # patrones: layered, hexagonal, CQRS, event-driven
    └── best-practices-components.md  # checklist y anti-patrones
```

---

## Uso manual

```bash
python3 skills/_lib/drawio/render.py c4 c4-componentes-<contenedor>.json c4-componentes-<contenedor>.drawio
```

o el wrapper local:

```bash
skills/docs/docs-c4-components/scripts/generate.sh c4-componentes-<contenedor>.json c4-componentes-<contenedor>.drawio
```

---

## Regla número uno

**Un solo contenedor por diagrama.** Si necesitas ver el interior de varios,
genera un `.drawio` por cada uno. El `scopeBoundary` representa ese contenedor,
no el sistema completo.

---

## Tipos en Nivel 3

| `type`      | Uso |
|-------------|-----|
| `component` | Pieza interna del contenedor en foco (siempre `scope:true`) |
| `container` | Otro contenedor del sistema (siempre `external:true`) |
| `database`  | BD que el contenedor usa (`external:true`) |
| `queue`     | Cola/tópico que el contenedor produce o consume (`external:true`) |
| `system`    | Sistema externo de terceros (`external:true`) |

Granularidad recomendada: **5–15 componentes** por diagrama.

---

## Limitaciones conocidas

| Limitación | Workaround |
|---|---|
| No infiere componentes desde el repo | El agente arma el modelo desde la descripción del usuario |
| Layout en 3 capas; ≥ 15 cajas pueden necesitar ajuste | Reorganiza con `Arrange > Layout` en draw.io |
| No es un diagrama de clases | Para UML detallado, genera desde el IDE |
