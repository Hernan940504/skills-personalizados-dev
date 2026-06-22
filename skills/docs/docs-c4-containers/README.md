# docs-c4-containers

> Skill especializado en **C4 Nivel 2 (Contenedores)** — genera un `.drawio`
> con las piezas desplegables del sistema (apps, APIs, BDs, colas, file
> systems), su tecnología y sus protocolos. Pensado para conversaciones
> técnicas de **Arquitectura de Soluciones**.

---

## Qué hace

1. Modela los **contenedores** del sistema en foco con su `technology`.
2. Incluye `database`, `queue`, actores y sistemas externos.
3. Etiqueta cada relación con propósito + protocolo (y `async:true` cuando aplique).
4. Genera el `.drawio` vía `skills/_lib/drawio/render.py` (motor compartido).

Salida: `c4-contenedores-<sistema>.drawio`.

---

## Prompts que activan este skill

```
"Diagrama C4 de contenedores con la BD y la cola"
"C4 nivel 2 del sistema de pedidos en draw.io"
"Arquitectura técnica con los microservicios y postgres"
"Muéstrame los contenedores y cómo se comunican"
"Container diagram con las APIs, workers y la BD"
```

---

## Estructura

```
docs-c4-containers/
├── SKILL.md
├── README.md
├── scripts/
│   └── generate.sh                  # wrapper → ../../_lib/drawio/render.py c4
├── templates/
│   └── containers.example.json      # ejemplo Nivel 2 (banca por internet)
└── references/
    ├── c4-containers-guide.md       # qué es un contenedor C4, tipos, technology
    ├── container-vs-component.md    # cuándo N2 vs cuándo N3
    └── best-practices-containers.md # checklist y anti-patrones
```

---

## Uso manual

```bash
python3 skills/_lib/drawio/render.py c4 c4-contenedores.json c4-contenedores.drawio
```

o el wrapper local:

```bash
skills/docs/docs-c4-containers/scripts/generate.sh c4-contenedores.json c4-contenedores.drawio
```

---

## Tipos del modelo JSON (Nivel 2)

| `type`      | Notación C4 | Forma |
|-------------|-------------|-------|
| `container` | Container   | Rectángulo redondeado azul medio |
| `database`  | Container   | Cilindro azul medio |
| `queue`     | Container   | Rectángulo azul medio |
| `person`    | Person      | Rectángulo muy redondeado azul (gris si `external`) |
| `system`    | Software System | Rectángulo (azul propio / gris externo) |

`technology` es obligatoria en `container`, `database` y `queue`. `async:true`
en una relación → flecha punteada (eventos, colas, pub/sub).

---

## Limitaciones conocidas

| Limitación | Workaround |
|---|---|
| No infiere contenedores desde código (docker-compose, k8s manifests) | El agente arma el modelo desde la descripción del usuario |
| Layout en 3 capas; ≥ 15 cajas pueden requerir ajuste manual | Reorganiza con `Arrange > Layout` en draw.io |
| Para íconos cloud-específicos (Lambda, Cloud Run, ECS) | Usa `docs-arch-cloud` (íconos oficiales AWS/GCP/On-Prem) |
