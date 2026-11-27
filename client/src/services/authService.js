/**
 * authService.js
 *
 * Autenticación contra Odoo. La sesión la maneja el navegador mediante
 * la cookie que Odoo establece en /web/session/authenticate — no
 * guardamos credenciales en sessionStorage.
 */
import { authenticate, sessionDestroy, AuthError } from '../api/odooClient.js';

const SESSION_KEY = 'netpulse_session';

/**
 * Hace login contra Odoo y guarda uid + nombre en sessionStorage.
 * @returns {{ uid: number, name: string }}
 */
export async function login(loginName, password) {
  const { uid, name } = await authenticate(loginName, password);
  const session = { uid, login: loginName, name };
  sessionStorage.setItem(SESSION_KEY, JSON.stringify(session));
  return session;
}

/**
 * Cierra la sesión en Odoo y limpia sessionStorage.
 */
export async function logout() {
  await sessionDestroy();
  sessionStorage.removeItem(SESSION_KEY);
}

/**
 * Recupera la sesión guardada, o null si no existe.
 */
export function getSession() {
  try {
    const raw = sessionStorage.getItem(SESSION_KEY);
    return raw ? JSON.parse(raw) : null;
  } catch {
    return null;
  }
}
