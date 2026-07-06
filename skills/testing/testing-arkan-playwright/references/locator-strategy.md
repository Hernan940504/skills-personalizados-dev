# Estrategia de locators y descubrimiento de UI

Cómo localizar elementos de forma **resiliente** y cómo descubrir la estructura
de un módulo desconocido (como los de Arkan) antes de escribir aserciones.

## Principio

Testea **comportamiento visible al usuario**, no detalles de implementación.
Un locator bueno sobrevive a refactors de CSS/markup; uno frágil rompe al primer
cambio de clase.

## Jerarquía de resiliencia

| Nivel | Locator | Cuándo |
|---|---|---|
| 1 (mejor) | `getByRole(rol, { name })` | Botones, links, headings, inputs, checkboxes |
| 2 | `getByLabel` / `getByPlaceholder` | Campos de formulario |
| 3 | `getByText` | Texto visible único |
| 4 | `getByTestId` | Si la app expone `data-testid` |
| 5 (evitar) | CSS / XPath | Solo si no hay alternativa accesible |

## Roles ARIA frecuentes

`button`, `link`, `textbox`, `checkbox`, `radio`, `combobox`, `option`,
`heading`, `dialog`, `alert`, `row`, `cell`, `tab`, `tabpanel`, `menuitem`,
`list`, `listitem`, `navigation`, `banner`, `main`.

## Descubrimiento de un módulo desconocido

1. **Snapshot de accesibilidad**: con Codegen (`Pick Locator`) o, si está el
   Playwright MCP, `browser_snapshot` devuelve el árbol con roles y nombres.
2. **Enumerar listas dinámicas**:
   ```ts
   const filas = page.getByRole('row');
   console.log(await filas.count());
   for (const fila of await filas.all()) {
     console.log(await fila.textContent());
   }
   ```
3. **ARIA snapshot** como mapa textual de la pantalla:
   ```ts
   await expect(page.locator('body')).toMatchAriaSnapshot(); // imprime YAML del árbol
   ```
4. **Acotar antes de actuar**: combina `getByRole` + `filter({ hasText })` para
   evitar `strict mode violation` en tablas/listas.

## Cuándo introducir `data-testid`

Si un elemento no tiene rol ni nombre accesible estable (íconos sin label, celdas
genéricas), lo correcto es pedir al equipo de Arkan que agregue `data-testid`.
Mientras tanto, usa `filter()` por texto del contexto en lugar de `nth()` ciego.

## Anti-patrones

- `page.locator('.btn-3a9f')` → clase auto-generada, rompe al recompilar.
- `page.locator('div > div > span:nth-child(2)')` → acoplado al DOM.
- `nth(2)` sin `filter()` → se rompe si cambia el orden o aparece un elemento.
- Aserciones sin `await expect(...)` → no auto-esperan → flaky.
