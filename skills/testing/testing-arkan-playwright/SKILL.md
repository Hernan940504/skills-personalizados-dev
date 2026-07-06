---
name: testing-arkan-playwright
description: Genera y ejecuta pruebas de extremo a extremo (E2E) de módulos del
  portal Arkan (https://arkan.bolnet.com.co/) con Playwright. Inicia sesión una
  vez y reutiliza la sesión (storageState), explora el módulo indicado, crea Page
  Objects y specs con locators por rol, corre las pruebas y reporta resultados
  con trazas y screenshots. Úsalo cuando el usuario pida probar/testear un módulo
  de Arkan, automatizar pruebas E2E o de UI, o validar un flujo del portal.
version: 0.1.0
author: Hernan940504
category: testing
tags: [playwright, e2e, testing, arkan, browser, autenticacion, ui]
compatibility: [claude-code]
allowed-tools: [Read, Write, Edit, Bash, Grep, Glob]
examples:
  - prompt: "prueba el módulo de pólizas de Arkan"
  - prompt: "haz pruebas E2E del login y del dashboard de arkan"
  - prompt: "automatiza con Playwright el flujo de creación de X en Arkan"
  - prompt: "testea el módulo de usuarios del portal"
---

# testing-arkan-playwright — Pruebas E2E de Arkan con Playwright

Automatizas pruebas de extremo a extremo del portal **Arkan** con Playwright.
El usuario indica un **módulo** y tú: te autenticas (una sola vez), exploras el
módulo, generas Page Objects + specs resilientes, corres las pruebas y reportas.

## Cuándo usar este skill

- El usuario pide "probar", "testear" o "automatizar" un módulo/flujo de Arkan.
- Pide pruebas E2E / de UI / de regresión sobre `arkan.bolnet.com.co`.
- Quiere generar tests de Playwright para un portal autenticado.

## Cuándo NO usar

- Pruebas **unitarias** o de API sin navegador → usa un skill de testing unitario.
- Generar el **manual de usuario** del portal (capturas + documentación) → usa
  `docs-portal-manual` (comparte el mismo harness de autenticación).
- Otra app que no sea Arkan → reutiliza el harness `_lib/playwright` cambiando
  `ARKAN_BASE_URL` y credenciales en `.env`.

## Convenciones (no negociables)

- **Credenciales solo en `.env`** (gitignored). Nunca en specs, ni en git.
- **Sesión reutilizable**: login una vez en el proyecto `setup` → `storageState`;
  los specs corren ya autenticados. No hagas login dentro de cada test.
- **Locators por rol/label/texto/testid**, en ese orden. CSS/XPath = último recurso.
- **Web-first assertions** siempre con `await expect(locator).matcher()` (auto-retry).
- Un **Page Object por módulo** en `pages/`, un **spec por módulo** en `tests/`.
- `playwright/.auth/*.json` es secreto (suplanta la cuenta) → nunca commitear.

## Workflow

### Paso 1 — Preparar el proyecto E2E (una vez)

```bash
bash skills/testing/testing-arkan-playwright/scripts/setup.sh arkan-e2e
```

Scaffolda `arkan-e2e/` desde el harness compartido, copia el `.env` con
credenciales, instala dependencias y baja Chromium. Es idempotente.

### Paso 2 — Autenticar y validar el login

```bash
cd arkan-e2e && npm run auth
```

Si falla (selectores del login no detectados), haz la **fase de descubrimiento**:
abre Codegen en el login, copia los locators reales con *Pick Locator* y
rellénalos en `.env` (`ARKAN_LOGIN_*_SELECTOR`, `ARKAN_LOGGED_IN_SELECTOR`).
Detalle en `references/arkan-notes.md`. Repite `npm run auth` hasta que cree
`playwright/.auth/user.json`.

### Paso 3 — Confirmar el módulo a probar

Pregunta (o toma del prompt): **qué módulo**, su **ruta**, y los **flujos clave**
(camino feliz + validaciones). Anota el módulo en `references/arkan-notes.md`.

### Paso 4 — Explorar el módulo

```bash
bash skills/testing/testing-arkan-playwright/scripts/explore-module.sh arkan-e2e /ruta-del-modulo
```

Graba interacciones ya autenticado y obtén locators sugeridos. Alternativa:
**modo agéntico con Playwright MCP** (ver abajo). Usa `references/locator-strategy.md`
para localizar elementos de forma resiliente.

### Paso 5 — Generar Page Object + spec

Copia y adapta las plantillas (sustituye los `{{...}}`):

- `templates/module.page.ts.tmpl` → `arkan-e2e/pages/<modulo>.page.ts`
- `templates/module.spec.ts.tmpl` → `arkan-e2e/tests/<modulo>.spec.ts`

Cubre al menos: carga del módulo, **camino feliz**, y **validaciones** (errores
esperados). Reusa locators descubiertos; aserciones con `await expect`.

### Paso 6 — Ejecutar y diagnosticar

```bash
cd arkan-e2e
npx playwright test --project=e2e -g "<Nombre del módulo>"
npm run report         # reporte HTML con screenshots/trace de los fallos
```

Para depurar: `npx playwright test --ui` (time-travel) o `--debug`.

### Paso 7 — Reportar resultados

Resume al usuario: tests corridos, **pass/fail**, y para cada fallo el mensaje,
el paso y dónde ver la traza (`npm run report` → trace embebido). Propón los
siguientes flujos a cubrir.

## Modo agéntico opcional (Playwright MCP)

Para exploración interactiva donde tú manejas el navegador en tiempo real:

```bash
claude mcp add playwright npx @playwright/mcp@latest
```

Úsalo con la sesión guardada para no re-loguear:
`--isolated --storage-state=arkan-e2e/playwright/.auth/user.json`. Flujo típico:
`browser_navigate` → `browser_snapshot` (obtiene refs) → `browser_click`/`browser_type`
→ `browser_wait_for`. Tras explorar, **materializa specs** (Paso 5) para tener
pruebas repetibles y versionables.

## Recursos

- `scripts/setup.sh` — scaffold del proyecto E2E (wrapper de `_lib/playwright`).
- `scripts/explore-module.sh` — Codegen autenticado sobre un módulo.
- `templates/module.page.ts.tmpl` — Page Object por módulo.
- `templates/module.spec.ts.tmpl` — spec por módulo (describe + escenarios).
- `references/playwright-cheatsheet.md` — comandos, locators, assertions, esperas.
- `references/locator-strategy.md` — resiliencia y descubrimiento de UI.
- `references/arkan-notes.md` — mapa de módulos y descubrimiento del login.
- `../../_lib/playwright/` — harness compartido (config, auth, login page object).

## Anti-patrones

- Hardcodear usuario/contraseña en specs o en la config → van en `.env`.
- Loguear dentro de cada test en vez de reutilizar `storageState`.
- Selectores frágiles (`.css-xyz`, `nth(2)` sin `filter()`) → ver locator-strategy.
- `expect(await loc.isVisible()).toBe(true)` → sin auto-retry, flaky.
- Commitear `.env` o `playwright/.auth/*.json` (secretos).
- Automatizar acciones destructivas en datos reales sin confirmar entorno de prueba.
