import { type Page, type Locator, expect } from '@playwright/test';
import { config } from '../lib/env';

/**
 * Page Object del login del portal.
 *
 * Estrategia de selectores en dos niveles:
 *  1. Si `.env` define ARKAN_LOGIN_*_SELECTOR, se usan esos (CSS/XPath explícitos).
 *  2. Si no, se usan heurísticas accesibles (getByLabel/getByPlaceholder/role),
 *     que cubren la mayoría de formularios. Si el login real no las satisface,
 *     ejecuta la fase de DESCUBRIMIENTO del skill y rellena los selectores en .env.
 */
export class LoginPage {
  constructor(private readonly page: Page) {}

  private userField(): Locator {
    if (config.selectors.user) return this.page.locator(config.selectors.user);
    return this.page
      .getByLabel(/usuario|correo|e-?mail|user(name)?/i)
      .or(this.page.getByPlaceholder(/usuario|correo|e-?mail|user/i))
      .or(this.page.locator('input[type="email"], input[name*="user" i], input[id*="user" i]'))
      .first();
  }

  private passwordField(): Locator {
    if (config.selectors.password) return this.page.locator(config.selectors.password);
    return this.page
      .getByLabel(/contrase|password|clave/i)
      .or(this.page.getByPlaceholder(/contrase|password|clave/i))
      .or(this.page.locator('input[type="password"]'))
      .first();
  }

  private submitButton(): Locator {
    if (config.selectors.submit) return this.page.locator(config.selectors.submit);
    return this.page
      .getByRole('button', { name: /ingresar|iniciar|entrar|log\s?in|acceder|continuar/i })
      .or(this.page.locator('button[type="submit"], input[type="submit"]'))
      .first();
  }

  /** Navega a la página de login (raíz del portal por defecto). */
  async goto(): Promise<void> {
    await this.page.goto(config.baseURL, { waitUntil: 'domcontentloaded' });
  }

  /** Rellena credenciales, envía el formulario y verifica el login. */
  async login(): Promise<void> {
    await this.userField().fill(config.user);
    await this.passwordField().fill(config.password);
    await this.submitButton().click();
    await this.assertLoggedIn();
  }

  /** Verifica que la sesión quedó iniciada (señal explícita o ausencia del form). */
  async assertLoggedIn(): Promise<void> {
    if (config.selectors.loggedIn) {
      await expect(this.page.locator(config.selectors.loggedIn)).toBeVisible({ timeout: 30_000 });
      return;
    }
    // Heurística: tras login el campo de contraseña ya no debería existir.
    await expect(this.page.locator('input[type="password"]')).toHaveCount(0, { timeout: 30_000 });
  }
}
