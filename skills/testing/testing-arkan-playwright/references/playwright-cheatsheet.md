# Playwright — Cheatsheet operativo

Referencia rápida para escribir y correr pruebas. Basado en la documentación
oficial (playwright.dev).

## Comandos de ejecución

```bash
npx playwright test                      # toda la suite
npx playwright test --project=e2e        # solo el proyecto e2e (autenticado)
npx playwright test ruta/al/archivo.spec.ts
npx playwright test -g "nombre del test" # filtra por título (grep)
npx playwright test --headed             # navegador visible
npx playwright test --ui                 # UI Mode: time-travel + watch + debug
npx playwright test --debug              # Inspector paso a paso
npx playwright test --trace on           # fuerza trace en esta corrida

npx playwright show-report               # abre el reporte HTML
npx playwright show-trace trace.zip      # abre un trace (o trace.playwright.dev)
npx playwright codegen <url>             # graba acciones -> código
```

Scripts npm del harness: `npm test`, `npm run test:ui`, `npm run test:headed`,
`npm run auth`, `npm run report`, `npm run codegen`.

## Anatomía de un test

```ts
import { test, expect } from '@playwright/test';

test.describe('Módulo X', () => {
  test.beforeEach(async ({ page }) => { await page.goto('/modulo-x'); });

  test('hace algo visible', async ({ page }) => {
    await page.getByRole('button', { name: 'Guardar' }).click();
    await expect(page.getByText('Guardado')).toBeVisible(); // web-first, auto-retry
  });
});
```

## Locators (orden de preferencia)

1. `getByRole('button', { name: 'Enviar' })` — rol + nombre accesible.
2. `getByLabel('Correo')` — campos de formulario por su label.
3. `getByPlaceholder('Buscar...')`
4. `getByText('Bienvenido')`
5. `getByTestId('user-row')` — requiere `data-testid` en la app.
6. CSS/XPath — **último recurso**, frágil.

## Web-first assertions (auto-retry — SIEMPRE con `await expect`)

```ts
await expect(loc).toBeVisible();
await expect(loc).toHaveText('Total: 5');
await expect(loc).toHaveValue('abc');
await expect(loc).toHaveCount(3);
await expect(page).toHaveURL(/\/dashboard/);
await expect(page).toHaveTitle(/Arkan/);
await expect.soft(loc).toHaveText('...'); // soft: no aborta, acumula fallos
```

Anti-patrón: `expect(await loc.isVisible()).toBe(true)` (sin auto-retry → flaky).

## Filtrar y desambiguar (strict mode)

```ts
// Acota por contenido antes de actuar
page.getByRole('listitem').filter({ hasText: 'Producto 2' })
    .getByRole('button', { name: 'Agregar' }).click();

page.getByRole('row').filter({ has: page.getByText('Activo') });
locator.and(otro);          // intersección
locator.or(otro).first();   // alternativa (diálogo opcional)
locator.first() / .last() / .nth(0);  // opt-out de strict mode
await locator.count();      // no lanza strict violation
```

`strict mode violation: ... resolved to N elements` → tu locator matchea varios;
acótalo con `filter()` o `getByRole(... name)`, no abuses de `nth()`.

## Navegación y esperas

```ts
await page.goto('/ruta');                  // usa baseURL
await page.waitForURL(/\/dashboard/);
await page.waitForLoadState('networkidle'); // útil tras navegaciones SPA
await page.getByRole('button').click();     // auto-espera a accionable
```

## Popups, pestañas, diálogos, descargas

```ts
const popupPromise = page.waitForEvent('popup');   // registrar ANTES del click
await page.getByRole('link', { name: 'Abrir' }).click();
const popup = await popupPromise;
await popup.waitForLoadState();

page.on('dialog', (d) => d.accept());              // o d.dismiss() para cancelar

const dl = page.waitForEvent('download');
await page.getByText('Exportar').click();
await (await dl).saveAs('descarga.xlsx');
```

## Reportes y diagnóstico

- `trace: 'on-first-retry'` (config) → trace al reintentar; ábrelo con `show-trace`.
- `screenshot: 'only-on-failure'`, `video: 'retain-on-failure'`.
- Reporte HTML embebe screenshots, video y trace de cada fallo.
