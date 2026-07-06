# Notas de Arkan — descubrimiento y mapa de módulos

Conocimiento específico del portal **Arkan** (Seguros Bolívar). Vívelo como un
documento que se completa al explorar: cada vez que descubras un selector estable
o un módulo nuevo, anótalo aquí.

## Datos base

| Dato | Valor |
|---|---|
| URL | https://arkan.bolnet.com.co/ |
| Usuario | (en `.env`: `ARKAN_USER`) |
| Contraseña | (en `.env`: `ARKAN_PASSWORD`) |

> Las credenciales NUNCA se escriben aquí ni en ningún archivo versionado. Viven
> solo en `_lib/playwright/.env` (gitignored) y en el `.env` del proyecto E2E.

## Fase de descubrimiento del login (hacer una vez)

El `LoginPage` usa heurísticas accesibles por defecto. Si el login de Arkan no
las satisface, descubre los selectores reales y rellénalos en `.env`:

1. `bash scripts/explore-module.sh arkan-e2e /` — abre Codegen en el login.
2. Con **Pick Locator**, copia el locator de: campo usuario, campo contraseña,
   botón de ingreso, y un elemento que solo exista ya autenticado (menú/dashboard).
3. Pega cada uno en `.env`:
   ```
   ARKAN_LOGIN_USER_SELECTOR=...
   ARKAN_LOGIN_PASSWORD_SELECTOR=...
   ARKAN_LOGIN_SUBMIT_SELECTOR=...
   ARKAN_LOGGED_IN_SELECTOR=...
   ```
4. `npm run auth` — debe terminar sin error y crear `playwright/.auth/user.json`.

## Mapa de módulos (completar al explorar)

| Módulo | Ruta | Estado | Notas / selectores estables |
|---|---|---|---|
| Login | `/` | ⏳ | — |
| _(añade aquí cada módulo que pruebes)_ | | | |

## Particularidades observadas

- _(SPA vs navegación tradicional, tiempos de carga, popups, iframes, etc.)_
- _(Mensajes de error y su texto exacto, para aserciones)_
- _(Datos de prueba seguros: qué se puede crear/editar sin afectar producción)_

## Precaución con datos

Arkan es un sistema real. Antes de automatizar acciones que **escriben**
(crear/editar/borrar), confirma que se usan datos de prueba y que el entorno no
es producción con datos sensibles. Para flujos destructivos prefiere `dismiss()`
en los diálogos de confirmación mientras descubres.
