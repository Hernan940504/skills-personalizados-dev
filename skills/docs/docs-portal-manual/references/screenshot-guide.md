# Guía de capturas estables para el manual

Cómo producir screenshots **repetibles y limpios** con Playwright. Basado en la
API oficial `page.screenshot` / `locator.screenshot`.

## Captura de pantalla completa

```ts
await page.screenshot({
  path: 'pantalla.png',
  fullPage: true,            // toda la página scrollable, no solo el viewport
  animations: 'disabled',    // congela animaciones/transiciones (evita borrosos)
  caret: 'hide',             // oculta el cursor de texto parpadeante
  scale: 'css',              // 1px CSS = 1px imagen (consistente en high-DPI)
});
```

## Ocultar zonas dinámicas o sensibles

```ts
await page.screenshot({
  path: 'pantalla.png',
  fullPage: true,
  mask: [page.locator('.reloj'), page.locator('.datos-personales')], // tapa regiones
  maskColor: '#FFFFFF',      // color del recuadro (def. rosa #FF00FF)
  style: '.cookie-banner, .toast { display: none !important; }',     // oculta volátiles
});
```

`mask` es ideal para **datos personales** en un manual: tapa cédulas, nombres,
saldos, etc. sin perder el resto de la pantalla.

## Captura de un solo elemento (panel/tarjeta)

```ts
await page.getByRole('region', { name: 'Resumen' }).screenshot({ path: 'resumen.png' });
```

## Exportar una pantalla a PDF (solo Chromium headless)

```ts
await page.emulateMedia({ media: 'screen' }); // ver como en pantalla, no en print
await page.pdf({ path: 'pantalla.pdf', format: 'A4', printBackground: true });
```

## Estabilidad: checklist

- [ ] `animations: 'disabled'` y `caret: 'hide'` siempre.
- [ ] Espera estabilidad antes de capturar: `await page.waitForLoadState('networkidle')`
      o `await expect(algoVisible).toBeVisible()`.
- [ ] `mask` para relojes, banners, anuncios y datos sensibles.
- [ ] Viewport fijo (lo define el proyecto `manual`: 1440×900) para tamaños iguales.
- [ ] Nombres ordenados `01-slug.png`, `02-slug.png` para que el manual quede en orden.

## ARIA snapshot (estructura textual de una pantalla)

Útil para describir la jerarquía de una pantalla en el texto del manual:

```ts
console.log(await page.locator('main').ariaSnapshot()); // YAML de roles y nombres
```
