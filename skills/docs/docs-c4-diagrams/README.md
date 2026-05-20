# docs-c4-diagrams

> Skill de diagramas de arquitectura **modelo C4** — genera archivos **`.drawio` nativos** (que abren directo en draw.io) con notación y colores oficiales C4, a partir de la descripción del sistema.

---

## Qué hace este skill

El agente actúa como Arquitecto de Software / Empresarial experto en C4 y:

1. **Determina el enfoque** — Arquitectura Empresarial (estratégico/negocio) vs Arquitectura de Soluciones (técnico/implementación).
2. **Elige el nivel C4 adecuado** — Contexto (N1), Contenedores (N2), Componentes (N3), o un diagrama suplementario (Dynamic, Deployment, System Landscape).
3. **Diseña el modelo** respetando la abstracción estricta y la carga cognitiva (≤ ~20 elementos).
4. **Escribe un modelo intermedio JSON** con elementos y relaciones.
5. **Genera un archivo `.drawio` nativo** con `scripts/generate-drawio.py` — layout automático, colores C4, relaciones etiquetadas con propósito + protocolo.
6. **Explica la justificación arquitectónica** y cómo abrir/editar el archivo en draw.io.

El entregable es un **`.drawio` editable**, no una imagen ni un bloque de Mermaid que haya que pegar.

---

## Ejemplos de prompts que activan este skill

```
"Hazme un diagrama C4 de contexto de este sistema de facturación"
"Genera el diagrama de contenedores en draw.io"
"Necesito un .drawio con la arquitectura de soluciones de mi API"
"Diagrama C4 nivel 2 con la base de datos, la cola y los servicios externos"
"Visualiza el flujo dinámico del proceso de checkout"
"Diagrama de despliegue de la app en AWS"
"Dibuja cómo encajan los sistemas de la empresa (system landscape)"
```

---

## Estructura del skill

```
docs-c4-diagrams/
├── SKILL.md                          # Instrucciones para el agente (leer primero)
├── README.md                         # Este archivo
├── scripts/
│   └── generate-drawio.py            # modelo JSON → .drawio nativo (layout + notación C4)
├── templates/
│   └── c4-model.example.json         # modelo de ejemplo (banca por internet, Nivel 2)
└── references/
    ├── c4-model-guide.md             # los 4 niveles + diagramas suplementarios
    ├── enterprise-vs-solution.md     # guía de decisión de enfoque
    ├── best-practices.md             # abstracción, naming, leyenda, layout, relaciones
    └── drawio-c4-shapes.md           # notación, colores y tips de edición en draw.io
```

---

## Cómo el agente usa este skill

```
1. Lee la solicitud → determina enfoque (empresarial vs soluciones) y nivel C4.
2. Diseña el modelo (personas, sistemas, contenedores/componentes, relaciones).
3. Escribe c4-model.json siguiendo templates/c4-model.example.json.
4. Ejecuta: python3 scripts/generate-drawio.py c4-model.json diagrama_arquitectura.drawio
5. Explica la justificación arquitectónica.
6. Entrega el .drawio + guía de apertura en draw.io.
```

### Uso manual del generador

```bash
python3 skills/docs/docs-c4-diagrams/scripts/generate-drawio.py c4-model.json salida.drawio
```

Sin Python extra: solo usa la librería estándar. Valida ids únicos y relaciones bien formadas.

---

## Esquema del modelo JSON

```json
{
  "diagramType": "Context|Container|Component|Dynamic|Deployment",
  "title": "Título del diagrama",
  "scopeBoundary": "Nombre del sistema/contenedor en foco (opcional)",
  "elements": [
    { "id": "api", "type": "container", "name": "API", "technology": "Java, Spring",
      "description": "Expone la lógica de negocio", "scope": true },
    { "id": "ext", "type": "system", "name": "Pasarela de Pagos",
      "description": "Procesa cobros", "external": true }
  ],
  "relationships": [
    { "source": "api", "target": "ext", "description": "Cobra", "technology": "HTTPS/REST" }
  ]
}
```

| `type` | Notación C4 | Forma en draw.io |
|---|---|---|
| `person` | Person | caja muy redondeada (azul oscuro / gris si externo) |
| `system` | Software System | caja redondeada (azul / gris si externo) |
| `container` | Container | caja redondeada azul medio |
| `database` | Container | cilindro |
| `queue` | Container | caja azul medio |
| `component` | Component | caja azul claro |

`external:true` → fuera del alcance, color gris. `scope:true` → dentro del `scopeBoundary`.
`async:true` en una relación → flecha punteada (eventos/colas).

---

## Abrir el resultado en draw.io

- **Desktop:** doble clic en el `.drawio`.
- **Web:** abre https://app.diagrams.net → `File > Open` (o arrastra el archivo) → o `File > Import from > Device`.
- Reorganiza con `Arrange > Layout` y exporta a PNG/SVG/PDF para presentaciones (conserva el `.drawio` como fuente de verdad).

---

## Convenciones de output

- Archivo principal: `diagrama_arquitectura.drawio` en la raíz del proyecto.
- Para arquitectura completa: un archivo por nivel — `c4-contexto.drawio`, `c4-contenedores.drawio`, `c4-componentes-<contenedor>.drawio`.
- Recomendado: versionar los `.drawio` en git (son XML, hacen buen diff) y acompañarlos con un ADR (`docs-adr`).

---

## Limitaciones conocidas

| Limitación | Workaround |
|---|---|
| El layout automático es por capas (actores arriba, externos abajo); diagramas grandes pueden requerir ajuste manual | Reorganizar con `Arrange > Layout` o a mano en draw.io |
| No usa la librería de shapes `mxgraph.c4.*` (iconos de persona, etc.) | Usa formas estándar con colores C4 — render garantizado; el usuario puede sustituir formas si quiere |
| No analiza el código del repositorio automáticamente | El agente construye el modelo desde la descripción del usuario |
| Nivel 4 (Code) no es el foco | Generar diagramas de clases desde el IDE |

---

## Compatibilidad de herramientas

| Herramienta | Comportamiento |
|---|---|
| Claude Code | Nativo — genera el `.drawio` vía script Python |
| Cursor | Funciona — las reglas guían el diseño del modelo C4 |
| Kiro | Funciona — steering file orienta el enfoque y niveles |
| OpenCode | Funciona — con Read/Write/Bash básicas |

---

## Versionado

`0.1.0` — versión inicial. Salida `.drawio` nativa para Contexto, Contenedores, Componentes, Dynamic y Deployment. Enfoques Empresarial y de Soluciones.

---

## Contribuir mejoras

Ver [`docs/CONTRIBUTING-SKILLS.md`](../../../../docs/CONTRIBUTING-SKILLS.md).

Ideas de mejora:
- Salida alternativa en Mermaid C4 y Structurizr DSL desde el mismo modelo JSON.
- Script de análisis de repo para inferir contenedores/externos (docker-compose, manifests).
- Soporte para la librería de shapes oficial `mxgraph.c4.*` como opción.
- Generación de leyenda automática.
