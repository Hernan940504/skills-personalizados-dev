# `_lib/playwright` — Harness E2E compartido

> Código compartido (no es un skill). Motor base de Playwright reutilizado por
> los skills [`testing-arkan-playwright`](../../testing/testing-arkan-playwright/)
> y [`docs-portal-manual`](../../docs/docs-portal-manual/).

Igual que `_lib/drawio`, este módulo existe porque **dos skills** necesitan el
mismo motor no trivial (proyecto Playwright + autenticación reutilizable +
captura). Duplicarlo costaría más que compartirlo. Ver la justificación en
[`docs/ARCHITECTURE.md`](../../../docs/ARCHITECTURE.md#53b-excepción-librerías-compartidas-_lib).

---

## Qué aporta

Un proyecto Playwright **autenticado** y listo para dos usos:

| Proyecto Playwright | Para qué |
|---|---|
| `setup`  | Hace login UNA vez y guarda la sesión en `playwright/.auth/user.json`. |
| `e2e`    | Pruebas funcionales por módulo, ya autenticadas (skill de testing). |
| `manual` | Captura una imagen por pantalla para el manual (skill de docs). |

Patrón oficial de Playwright: un *setup project* + `dependencies` + `storageState`
para no re-loguear en cada test.

---

## Estructura

```
_lib/playwright/
├── bootstrap.sh           # scaffold idempotente -> copia template/ a un destino
├── .env                   # GITIGNORED — credenciales reales (fuente de verdad local)
└── template/              # archivos que se copian al proyecto E2E
    ├── package.json       # scripts npm (test, auth, manual, report, codegen)
    ├── tsconfig.json
    ├── playwright.config.ts
    ├── .env.example       # plantilla de credenciales (sin secretos)
    ├── .gitignore         # ignora .env, .auth/, reportes, manual-output/
    ├── lib/
    │   └── env.ts         # carga + valida .env; expone config y STORAGE_STATE
    ├── pages/
    │   └── login.page.ts  # Page Object del login (selectores env + fallback accesible)
    └── tests/
        └── auth.setup.ts  # login -> storageState
```

---

## Uso

```bash
# Scaffold (instala deps y baja Chromium):
bash bootstrap.sh mi-proyecto-e2e

# Scaffold sin instalar (entornos offline / CI con caché):
bash bootstrap.sh mi-proyecto-e2e --no-deps
```

Los skills lo invocan vía su wrapper `scripts/setup.sh`.

---

## Seguridad (no negociable)

- Las credenciales viven SOLO en `_lib/playwright/.env` (gitignored) y en el
  `.env` del proyecto scaffoldeado. **Nunca** en archivos versionados.
- `playwright/.auth/*.json` contiene cookies/tokens que **suplantan la cuenta**:
  está gitignored y nunca debe commitearse.
- Lo único versionado es `.env.example` (placeholders).
