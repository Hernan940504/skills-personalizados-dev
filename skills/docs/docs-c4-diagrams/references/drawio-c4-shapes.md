# Notación C4 en draw.io — colores, formas y edición

Cómo el generador mapea el modelo C4 a formas nativas de draw.io, y tips para editar el
resultado. El `.drawio` usa formas estándar (rectángulos redondeados, cilindro) con el
esquema de color oficial C4, de modo que **abre en cualquier draw.io sin instalar librerías**.

---

## Esquema de color (canónico C4 / Structurizr)

| Elemento (`type`) | Relleno | Borde | Texto | Forma |
|---|---|---|---|---|
| `person` (interno) | `#08427B` azul oscuro | `#052E56` | blanco | rect. muy redondeado (arcSize 40) |
| `person` (`external`) | `#686868` gris | `#4D4D4D` | blanco | rect. muy redondeado |
| `system` (interno) | `#1168BD` azul | `#0B4884` | blanco | rect. redondeado |
| `system` (`external`) | `#999999` gris | `#6B6B6B` | blanco | rect. redondeado |
| `container` | `#438DD5` azul medio | `#2E6295` | blanco | rect. redondeado |
| `database` | `#438DD5` azul medio | `#2E6295` | blanco | **cilindro** |
| `queue` | `#438DD5` azul medio | `#2E6295` | blanco | rect. redondeado |
| `component` | `#85BBF0` azul claro | `#5D82A8` | **negro** | rect. redondeado |
| `scopeBoundary` | sin relleno | `#444444` punteado | gris | rectángulo dashed |

Las relaciones son flechas con `endArrow=block`, color `#707070`, etiqueta sobre fondo blanco.
`async:true` → flecha **punteada** (eventos / colas / pub-sub).

## Etiqueta de cada caja

El generador construye el label en HTML:

```
<b>{name}</b>
[{estereotipo}]            ← p.ej. [Person], [Software System, External], [Container: Java, Spring MVC]
{description}
```

El estereotipo se deriva del `type` (+ `, External` si aplica) y, para
container/component/database/queue, incluye la `technology` si la diste.

---

## Por qué formas estándar y no la librería "C4" de draw.io

draw.io trae una librería de shapes C4 (`mxgraph.c4.*`), pero depende de que esa librería esté
habilitada y sus nombres de stencil son frágiles entre versiones. Usar rectángulos redondeados
+ cilindro con los colores C4 garantiza que el archivo **renderiza idéntico en cualquier
instalación** (web, desktop, export), que es justo lo que se necesita para compartir.

Si el usuario quiere las formas oficiales de draw.io (con el iconito de persona, etc.), puede,
tras abrir: activar `More Shapes… > Software > C4` y reemplazar las cajas. No es necesario.

---

## Editar el resultado en draw.io

- **Mover/reorganizar:** selecciona cajas y arrástralas; las flechas se re-enrutan solas.
- **Auto-layout:** `Arrange (Organizar) > Layout` → prueba *Vertical Tree* o *Horizontal Flow*.
- **Editar texto:** doble clic en una caja; el formato HTML del label se conserva.
- **Cambiar estilo:** clic derecho > `Edit Style…` para tocar el string de estilo mxGraph.
- **Exportar:** `File > Export as…` → PNG/SVG/PDF para presentaciones (mantén el `.drawio` como fuente).

## Abrir el archivo

- **Desktop:** doble clic en el `.drawio`.
- **Web (app.diagrams.net):** `File > Open` o arrastra el archivo a la ventana; también `File > Import from > Device`.

---

## Estructura del XML (referencia)

```
mxfile
└── diagram (name = título)
    └── mxGraphModel
        └── root
            ├── mxCell id=0
            ├── mxCell id=1 (capa raíz)
            ├── mxCell boundary (si hay scopeBoundary) — se declara primero → queda detrás
            ├── mxCell <id-elemento> vertex=1   (una por elemento)
            └── mxCell relN edge=1               (una por relación)
```

Los `id` de los `<mxCell>` de elementos son exactamente los `id` del modelo JSON, así que las
relaciones (`source`/`target`) referencian esos mismos ids. Mantén los ids cortos y únicos.
