# `skills/_lib/drawio` — motor compartido `.drawio`

Módulo Python que convierte un modelo JSON normalizado en un archivo
`.drawio` nativo (XML mxGraph), listo para abrir en draw.io desktop o
app.diagrams.net.

Usado por los skills `docs-c4-context`, `docs-c4-containers`,
`docs-c4-components` y `docs-arch-cloud`. **No tiene SKILL.md** — no es un
skill por sí mismo, sino una librería interna.

---

## CLI

```bash
python3 skills/_lib/drawio/render.py <flavor> <modelo.json> [salida.drawio]
```

Flavors:
- `c4`     — paleta C4 oficial (Structurizr): person, system, container,
  database, queue, component. Layout en 3 capas (actores arriba, scope en
  medio, externos abajo).
- `aws`    — íconos oficiales AWS `mxgraph.aws4.*` + grupos VPC/AZ/Region.
  Layout anidado por `parent`.
- `gcp`    — íconos oficiales GCP `mxgraph.gcp2.*` + grupos Project/Region/
  Zone/VPC. Layout anidado.
- `onprem` — shapes `mxgraph.networks.*` + cilindro + actor para data center
  y red corporativa. Layout anidado.

---

## Estructura

```
_lib/drawio/
├── __init__.py
├── core.py              # XML mxGraph + layout + validación
├── render.py            # CLI: render.py <flavor> <input.json> <output.drawio>
├── c4_shapes.py         # paleta C4 (Catalog)
├── aws_shapes.py        # catálogo AWS (Catalog + SERVICES + GROUPS)
├── gcp_shapes.py        # catálogo GCP (Catalog + SERVICES + GROUPS)
├── onprem_shapes.py     # catálogo OnPremise (Catalog + SERVICES + GROUPS)
└── README.md            # este archivo
```

---

## Esquema del modelo JSON

```json
{
  "diagramType": "Context|Container|Component|Cloud|Architecture",
  "title": "Título visible",
  "scopeBoundary": "Nombre del boundary",   // solo C4
  "elements": [
    {
      "id": "<id_unico>",
      "type": "<del catálogo>",
      "name": "Nombre visible",
      "technology": "Opcional",
      "description": "Responsabilidad",
      "external": false,                     // C4
      "scope": true,                         // C4
      "parent": "<id de grupo padre>"        // cloud / on-prem
    }
  ],
  "groups": [
    {
      "id": "<id_unico>",
      "type": "<del catálogo de grupos>",
      "name": "Etiqueta",
      "parent": "<id de grupo padre>"
    }
  ],
  "relationships": [
    {
      "source": "<id>",
      "target": "<id>",
      "description": "Propósito",
      "technology": "Protocolo",
      "async": false
    }
  ]
}
```

---

## Interfaz de un catálogo (`Catalog`)

Para agregar un nuevo flavor, expón en su módulo una clase con estos
métodos estáticos (o `@staticmethod`):

```python
class Catalog:
    name: str

    @staticmethod
    def has_element(type_: str) -> bool: ...
    @staticmethod
    def has_group(type_: str) -> bool: ...
    @staticmethod
    def use_nested_layout() -> bool: ...
    @staticmethod
    def element_size() -> tuple[int, int]: ...
    @staticmethod
    def rank(el: dict) -> int: ...                # solo si use_nested_layout=False
    @staticmethod
    def element_style(el: dict) -> str: ...       # estilo mxGraph
    @staticmethod
    def element_stereotype(el: dict) -> str: ...  # texto que va bajo el nombre
    @staticmethod
    def group_style(g: dict) -> str: ...
    @staticmethod
    def group_label(g: dict) -> str: ...
```

Luego regístralo en `render.py`:

```python
from . import nuevo_shapes
CATALOGS["nuevo"] = nuevo_shapes.Catalog
```

---

## Validación

`core.build_xml` llama a `validate()` antes de emitir el XML. Lanza
`ModelError` si:
- Falta `id` o `type` en un elemento/grupo.
- Hay `id` duplicado entre elements y groups.
- Un `type` no existe en el catálogo activo.
- `parent` apunta a un id inexistente.
- `source`/`target` de una relación apunta a un id inexistente.

El CLI captura `ModelError` y aborta con mensaje claro.

---

## Sin dependencias externas

Solo librería estándar de Python 3.10+ (`json`, `html`, `uuid`, `pathlib`,
`xml.etree.ElementTree` para tests si quieres). No requiere `pip install`.
