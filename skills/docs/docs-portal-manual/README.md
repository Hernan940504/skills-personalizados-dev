# docs-portal-manual

> Skill que **genera el manual de usuario** de un portal web recorriéndolo con
> Playwright: inicia sesión, captura una imagen por pantalla y ensambla un
> Markdown con índice, capturas y pasos. Por defecto apunta a **Arkan**.

---

## Qué hace

1. Reusa el harness Playwright autenticado (`_lib/playwright`).
2. Recorre los módulos definidos en `manual.config.json`.
3. Captura una imagen estable por pantalla (`fullPage`, sin animaciones).
4. Ensambla `manual-output/manual.md` con índice, capturas y pasos de uso.

---

## Pre-requisitos

- **Node.js 18+** y `npm`.
- Acceso de red al portal (`https://arkan.bolnet.com.co/`).
- Credenciales en `skills/_lib/playwright/.env` (gitignored).

---

## Prompts que activan este skill

```
"haz el manual de usuario del portal Arkan"
"documenta el portal con pantallazos de cada módulo"
"genera una guía de uso de arkan con capturas"
"necesito el manual funcional del módulo de pólizas"
```

---

## Uso rápido

```bash
# 1. Scaffold (o reusa el de testing-arkan-playwright)
bash skills/docs/docs-portal-manual/scripts/setup.sh arkan-e2e
cd arkan-e2e && npm run auth

# 2. Define módulos
cp ../skills/docs/docs-portal-manual/templates/manual.config.example.json manual.config.json
cp ../skills/docs/docs-portal-manual/templates/manual.capture.spec.ts.tmpl tests/manual.capture.spec.ts
# (edita manual.config.json con tus módulos)

# 3. Captura y ensambla
npm run manual
node ../skills/docs/docs-portal-manual/scripts/build-manual.mjs
# -> manual-output/manual.md
```

---

## Estructura

```
docs-portal-manual/
├── SKILL.md
├── README.md
├── scripts/
│   ├── setup.sh             # wrapper -> _lib/playwright/bootstrap.sh
│   └── build-manual.mjs     # config + capturas -> manual.md (sin dependencias)
├── templates/
│   ├── manual.config.example.json   # módulos a documentar
│   ├── manual.capture.spec.ts.tmpl  # captura una imagen por pantalla
│   └── manual.md.tmpl               # esqueleto de la salida
└── references/
    ├── screenshot-guide.md   # capturas estables, mask, PDF
    └── manual-structure.md   # cómo estructurar y redactar el manual
```

Comparte el motor [`skills/_lib/playwright/`](../../_lib/playwright/) con
`testing-arkan-playwright` (misma autenticación y sesión).

---

## Seguridad

- Credenciales solo en `.env` (gitignored).
- Usa `mask` en `manual.config.json` para tapar datos personales en las capturas.
- No commitees `manual-output/` si contiene datos reales sensibles.

---

## Limitaciones conocidas

| Limitación | Workaround |
|---|---|
| `page.pdf()` solo funciona en Chromium headless | Genera Markdown y conviértelo, o usa Chromium |
| El skill no conoce los módulos a priori | Defínelos en `manual.config.json` o descúbrelos navegando |
| Solo `claude-code` ejecuta el navegador | En otras herramientas sirve de guía |
