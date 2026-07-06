/**
 * Carga y valida la configuración desde variables de entorno (.env).
 * Fuente única de verdad para credenciales y selectores del portal.
 *
 * El secreto vive SOLO en `.env` (gitignored). Nunca hardcodees credenciales.
 */
import 'dotenv/config';

function required(name: string): string {
  const value = process.env[name];
  if (!value || value.trim() === '') {
    throw new Error(
      `Falta la variable de entorno ${name}. ` +
        `Copia .env.example a .env y rellénala (cp .env.example .env).`,
    );
  }
  return value.trim();
}

function optional(name: string): string | undefined {
  const value = process.env[name];
  return value && value.trim() !== '' ? value.trim() : undefined;
}

export const config = {
  baseURL: required('ARKAN_BASE_URL'),
  user: required('ARKAN_USER'),
  password: required('ARKAN_PASSWORD'),
  selectors: {
    /** CSS/XPath explícitos; si están vacíos se usa la estrategia accesible. */
    user: optional('ARKAN_LOGIN_USER_SELECTOR'),
    password: optional('ARKAN_LOGIN_PASSWORD_SELECTOR'),
    submit: optional('ARKAN_LOGIN_SUBMIT_SELECTOR'),
    loggedIn: optional('ARKAN_LOGGED_IN_SELECTOR'),
  },
} as const;

/** Ruta del estado de sesión autenticada que produce el setup project. */
export const STORAGE_STATE = 'playwright/.auth/user.json';
