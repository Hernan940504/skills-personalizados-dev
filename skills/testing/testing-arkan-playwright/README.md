# testing-arkan-playwright

> Skill para **pruebas E2E del portal Arkan** (Seguros Bolívar) con Playwright.
> Indica un módulo y el skill se autentica, lo explora, genera Page Objects +
> specs resilientes, corre las pruebas y reporta con trazas.

---

## Qué hace

1. Scaffolda un proyecto Playwright autenticado (harness `_lib/playwright`).
2. Inicia sesión **una vez** y reutiliza la sesión (`storageState`).
3. Explora el módulo indicado (Codegen o Playwright MCP).
4. Genera un Page Object + spec por módulo con locators por rol.
5. Ejecuta las pruebas y produce reporte HTML con screenshots y trazas.

---

## Pre-requisitos

- **Node.js 18+** y `npm`.
- Acceso de red a `https://arkan.bolnet.com.co/`.
- Credenciales en `skills/_lib/playwright/.env` (gitignored). Ya vienen
  preconfiguradas para uso local; nunca se commitean.

---

## Prompts que activan este skill

```
"prueba el módulo de pólizas de Arkan"
"haz pruebas E2E del login y del dashboard de arkan"
"automatiza con Playwright el flujo de creación de X en Arkan"
"testea el módulo de usuarios del portal"
```

---

## Uso rápido

```bash
# 1. Scaffold (una vez)
bash skills/testing/testing-arkan-playwright/scripts/setup.sh arkan-e2e

# 2. Login y guardado de sesión
cd arkan-e2e && npm run auth

# 3. Explorar un módulo (Codegen autenticado)
bash skills/testing/testing-arkan-playwright/scripts/explore-module.sh arkan-e2e /modulo

# 4. (Generar pages/<modulo>.page.ts y tests/<modulo>.spec.ts desde templates)

# 5. Correr y ver reporte
npx playwright test --project=e2e -g "Mi módulo"
npm run report
```

---

## Estructura

```
testing-arkan-playwright/
├── SKILL.md
├── README.md
├── scripts/
│   ├── setup.sh             # wrapper -> _lib/playwright/bootstrap.sh
│   └── explore-module.sh    # Codegen autenticado sobre un módulo
├── templates/
│   ├── module.page.ts.tmpl  # Page Object por módulo
│   └── module.spec.ts.tmpl  # spec por módulo
└── references/
    ├── playwright-cheatsheet.md
    ├── locator-strategy.md
    └── arkan-notes.md        # mapa de módulos + descubrimiento del login
```

El motor real (config Playwright, autenticación, login page object) vive en
[`skills/_lib/playwright/`](../../_lib/playwright/), compartido con
`docs-portal-manual`.

---

## Seguridad

- Credenciales solo en `.env` (gitignored). Nunca en specs ni en git.
- `playwright/.auth/*.json` contiene cookies/tokens que suplantan la cuenta:
  está gitignored, nunca se commitea.

---

## Limitaciones conocidas

| Limitación | Workaround |
|---|---|
| El login de Arkan puede no exponer labels accesibles | Fase de descubrimiento → rellena `ARKAN_LOGIN_*_SELECTOR` en `.env` |
| Solo `claude-code` ejecuta los scripts/navegador | En otras herramientas el skill sirve de guía, no ejecuta |
| El skill no conoce los módulos de Arkan a priori | Los descubre explorando; se documentan en `arkan-notes.md` |
