import { defineConfig, devices } from '@playwright/test';
import { config, STORAGE_STATE } from './lib/env';

/**
 * Config canónica del harness Playwright compartido.
 * - `setup`  : hace login UNA vez y guarda la sesión (storageState).
 * - `e2e`    : pruebas funcionales por módulo (ya autenticadas).
 * - `manual` : captura una imagen por pantalla para el manual de usuario.
 *
 * Las credenciales y la baseURL salen de `.env` vía `lib/env.ts`. Nunca se
 * hardcodean. El storageState (`playwright/.auth/`) es secreto y está gitignored.
 */
export default defineConfig({
  testDir: './tests',
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  reporter: [['list'], ['html', { open: 'never' }]],
  use: {
    baseURL: config.baseURL,
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
    video: 'retain-on-failure',
    actionTimeout: 15_000,
    navigationTimeout: 30_000,
  },
  projects: [
    // 1) Autenticación: corre antes que todo y produce storageState.
    { name: 'setup', testMatch: /.*\.setup\.ts/ },

    // 2) Suite E2E funcional por módulo (excluye la captura del manual).
    {
      name: 'e2e',
      testMatch: /.*\.spec\.ts/,
      testIgnore: /manual\.capture\.spec\.ts/,
      use: { ...devices['Desktop Chrome'], storageState: STORAGE_STATE },
      dependencies: ['setup'],
    },

    // 3) Captura del manual de usuario (una imagen por pantalla).
    {
      name: 'manual',
      testMatch: /manual\.capture\.spec\.ts/,
      use: {
        ...devices['Desktop Chrome'],
        storageState: STORAGE_STATE,
        viewport: { width: 1440, height: 900 },
      },
      dependencies: ['setup'],
    },
  ],
});
