import { test as setup } from '@playwright/test';
import { mkdirSync } from 'node:fs';
import path from 'node:path';
import { LoginPage } from '../pages/login.page';
import { STORAGE_STATE } from '../lib/env';

/**
 * Proyecto `setup`: hace login UNA sola vez y persiste la sesión en
 * STORAGE_STATE. Los proyectos `e2e` y `manual` dependen de este y arrancan
 * ya autenticados, sin re-login por test.
 */
setup('authenticate', async ({ page }) => {
  mkdirSync(path.dirname(STORAGE_STATE), { recursive: true });

  const login = new LoginPage(page);
  await login.goto();
  await login.login();

  await page.context().storageState({ path: STORAGE_STATE });
});
