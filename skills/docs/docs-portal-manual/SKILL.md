---
name: docs-portal-manual
description: Genera el manual de usuario de un portal web (Arkan por defecto,
  https://arkan.bolnet.com.co/) navegándolo con Playwright. Inicia sesión,
  recorre los módulos indicados, captura una imagen estable por pantalla y
  ensambla un manual en Markdown con índice, capturas embebidas y pasos de uso.
  Úsalo cuando el usuario pida el manual de usuario, documentar un portal, una
  guía con pantallazos, o documentación funcional de Arkan.
version: 0.1.0
author: Hernan940504
category: docs
tags: [playwright, manual-usuario, documentacion, screenshots, portal, arkan]
compatibility: [claude-code]
allowed-tools: [Read, Write, Edit, Bash, Grep, Glob]
examples:
  - prompt: "haz el manual de usuario del portal Arkan"
  - prompt: "documenta el portal con pantallazos de cada módulo"
  - prompt: "genera una guía de uso de arkan con capturas"
  - prompt: "necesito el manual funcional del módulo de pólizas"
---

# docs-portal-manual — Manual de usuario con capturas reales (Playwright)

Generas el **manual de usuario** de un portal web recorriéndolo con un navegador
real. Inicias sesión, capturas una imagen por pantalla y ensamblas un Markdown
con índice, capturas y pasos. Por defecto apunta a **Arkan**.

## Cuándo usar este skill

- El usuario pide el "manual de usuario", "guía de uso" o "documentación con
  pantallazos" de Arkan o de un portal autenticado.
- Quiere documentar módulo a módulo cómo se opera el portal.
- Necesita capturas reales y actualizadas de cada pantalla.

## Cuándo NO usar

- **Probar/validar** funcionalidad (pass/fail, aserciones) → usa
  `testing-arkan-playwright` (comparte el mismo harness).
- Documentación de **arquitectura** (C4, diagramas) → usa los skills `docs-c4-*`.
- Documentación de **API** (OpenAPI/Swagger) → usa `docs-openapi`.

## Convenciones (no negociables)

- **Credenciales solo en `.env`** (gitignored). Nunca en la config ni en git.
- **Sesión reutilizable**: login una vez (`setup`) → `storageState`; la captura
  corre ya autenticada.
- **Capturas estables**: `fullPage`, `animations:'disabled'`, `caret:'hide'`.
- **`mask` para datos sensibles** (cédulas, nombres, saldos) en cada pantalla.
- Manual **orientado a tareas** y en segunda persona (ver `references/manual-structure.md`).
- `playwright/.auth/*.json` es secreto → nunca commitear.

## Workflow

### Paso 1 — Preparar el proyecto (reusa el harness)

```bash
bash skills/docs/docs-portal-manual/scripts/setup.sh arkan-e2e
```

Si ya scaffoldeaste con `testing-arkan-playwright`, **reusa esa misma carpeta**
(comparten harness, `.env` y sesión).

### Paso 2 — Autenticar (si no hay sesión)

```bash
cd arkan-e2e && npm run auth
```

Reusa `playwright/.auth/user.json` si ya existe. Si el login no se detecta, haz
la fase de descubrimiento (ver `testing-arkan-playwright/references/arkan-notes.md`).

### Paso 3 — Definir los módulos a documentar

Copia la plantilla y edítala con los módulos (pregunta al usuario cuáles, o
descúbrelos navegando el menú):

```bash
cp skills/docs/docs-portal-manual/templates/manual.config.example.json arkan-e2e/manual.config.json
```

Por cada módulo define `name`, `slug`, `path`, `description`, `steps` y, si hay
datos sensibles, `mask`. Guía de campos en `references/manual-structure.md`.

### Paso 4 — Instalar el spec de captura

```bash
cp skills/docs/docs-portal-manual/templates/manual.capture.spec.ts.tmpl \
   arkan-e2e/tests/manual.capture.spec.ts
```

### Paso 5 — Capturar las pantallas

```bash
cd arkan-e2e && npm run manual
```

Genera `manual-output/img/01-<slug>.png`, `02-...`, una por módulo. Revisa que
no haya animaciones, banners ni datos sensibles visibles; si los hay, añade
selectores a `mask` y repite. Ver `references/screenshot-guide.md`.

### Paso 6 — Ensamblar el manual

```bash
cd arkan-e2e && node ../skills/docs/docs-portal-manual/scripts/build-manual.mjs
```

Produce `manual-output/manual.md` con índice, capturas embebidas y pasos. (Ajusta
la ruta a `build-manual.mjs` según dónde quedó `arkan-e2e`.)

### Paso 7 — Revisar y enriquecer

Lee el `manual.md`, mejora descripciones y pasos, verifica que cada captura
corresponde a su sección. Para PDF: convierte el Markdown, o exporta pantallas
con `page.pdf()` (`references/screenshot-guide.md`).

## Recursos

- `scripts/setup.sh` — scaffold del proyecto (wrapper de `_lib/playwright`).
- `scripts/build-manual.mjs` — ensambla `manual.md` desde config + capturas.
- `templates/manual.config.example.json` — lista de módulos a documentar.
- `templates/manual.capture.spec.ts.tmpl` — captura una imagen por pantalla.
- `templates/manual.md.tmpl` — esqueleto de la salida.
- `references/screenshot-guide.md` — capturas estables, mask, PDF.
- `references/manual-structure.md` — cómo estructurar y redactar el manual.
- `../../_lib/playwright/` — harness compartido (config, auth, login).

## Anti-patrones

- Pegar credenciales o datos personales en `manual.config.json` o en el manual.
- Capturar sin `animations:'disabled'`/`caret:'hide'` → imágenes inconsistentes.
- Documentar features en vez de tareas del usuario.
- Capturas con datos sensibles a la vista (usa `mask`).
- Commitear `manual-output/` con datos reales si el manual no es público-seguro.
