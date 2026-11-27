/**
 * odooClient.js
 *
 * Cliente HTTP para la API JSON-RPC de Odoo 17.
 * Usa los endpoints web (/web/session/authenticate, /web/dataset/call_kw)
 * que son los que Odoo expone al navegador.
 */

function getBaseUrl() {
  return import.meta.env.VITE_ODOO_URL ?? 'http://localhost:8069';
}

// ── Errores tipados ──────────────────────────────────────────────────────────

export class AuthError extends Error {
  constructor(message = 'Credenciales inválidas o sesión expirada') {
    super(message);
    this.name = 'AuthError';
  }
}

export class PermissionError extends Error {
  constructor(message = 'No tienes permiso para esta acción') {
    super(message);
    this.name = 'PermissionError';
  }
}

export class ValidationError extends Error {
  constructor(message) {
    super(message);
    this.name = 'ValidationError';
  }
}

export class NetworkError extends Error {
  constructor(message) {
    super(message);
    this.name = 'NetworkError';
  }
}

// ── Mapa de excepción Odoo → error tipado ───────────────────────────────────

function mapOdooError(errorBody) {
  const name = errorBody?.data?.name ?? '';
  const message = errorBody?.data?.message ?? errorBody?.message ?? 'Error desconocido';
  if (name.includes('AccessDenied')) return new AuthError(message);
  if (name.includes('AccessError'))  return new PermissionError(message);
  if (name.includes('ValidationError')) return new ValidationError(message);
  return new Error(message);
}

// ── Función de bajo nivel ────────────────────────────────────────────────────

let _id = 1;

async function post(path, params) {
  const payload = { jsonrpc: '2.0', method: 'call', id: _id++, params };
  let response;
  try {
    response = await fetch(`${getBaseUrl()}${path}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'include',         // envía/recibe la cookie de sesión de Odoo
      body: JSON.stringify(payload),
    });
  } catch (err) {
    throw new NetworkError(`Error de red: ${err.message}`);
  }
  if (!response.ok) throw new NetworkError(`HTTP ${response.status}`);
  const data = await response.json();
  if (data.error) throw mapOdooError(data.error);
  return data.result;
}

// ── API pública ──────────────────────────────────────────────────────────────

/**
 * Autentica contra Odoo y devuelve { uid, name }.
 * La sesión queda guardada en la cookie que el navegador maneja automáticamente.
 */
export async function authenticate(login, password) {
  const db = import.meta.env.VITE_ODOO_DB ?? 'netpulse';
  const result = await post('/web/session/authenticate', { db, login, password });
  // Odoo devuelve result = { uid: false } cuando las credenciales son incorrectas
  if (!result?.uid) throw new AuthError('Usuario o contraseña incorrectos');
  return { uid: result.uid, name: result.name ?? login };
}

/**
 * Llama a un método de un modelo Odoo vía /web/dataset/call_kw.
 * La autenticación la gestiona la cookie de sesión.
 */
export function callKw(model, method, args = [], kwargs = {}) {
  return post('/web/dataset/call_kw', { model, method, args, kwargs });
}

/**
 * Cierra la sesión en Odoo.
 */
export function sessionDestroy() {
  return post('/web/session/destroy', {}).catch(() => {});
}
