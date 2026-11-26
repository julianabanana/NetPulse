/**
 * Pruebas unitarias del reducer de autenticación.
 *
 * Se prueba el reducer y el flujo de acciones directamente,
 * sin montar el árbol de React, para mantener las pruebas rápidas
 * y sin dependencias de DOM.
 *
 * authService se mockea completamente: estas pruebas verifican
 * el comportamiento del store, no del servicio de autenticación.
 */
import { describe, it, expect, vi, beforeEach } from 'vitest';

// Mock de authService antes de importar el store
vi.mock('../../services/authService.js', () => ({
  login: vi.fn(),
  logout: vi.fn(),
  getSession: vi.fn(() => null), // sesión vacía por defecto
}));

import * as authService from '../../services/authService.js';
import { authReducer, buildInitialState } from '../authStore.js';

// ── Helpers ──────────────────────────────────────────────────────────────────

/**
 * Simula el flujo que ejecuta el AuthProvider:
 * dispatch LOGIN_START → llamar al servicio → dispatch SUCCESS o FAILURE.
 */
async function runLoginFlow(state, loginName, apiKey) {
  let current = authReducer(state, { type: 'LOGIN_START' });
  try {
    const session = await authService.login(loginName, apiKey);
    current = authReducer(current, { type: 'LOGIN_SUCCESS', payload: session });
    return { state: current, error: null };
  } catch (err) {
    current = authReducer(current, { type: 'LOGIN_FAILURE', payload: err.message });
    return { state: current, error: err };
  }
}

beforeEach(() => {
  vi.clearAllMocks();
});

// ── Pruebas ──────────────────────────────────────────────────────────────────

describe('authStore › authReducer', () => {
  it('login_exitoso_guardaUidYApiKey: estado tiene isAuthenticated=true y uid=2', async () => {
    // Arrange: authService.login devuelve una sesión válida con uid=2
    authService.login.mockResolvedValue({ uid: 2, login: 'admin', apiKey: 'test-key' });

    const initial = buildInitialState();

    // Act
    const { state } = await runLoginFlow(initial, 'admin', 'test-key');

    // Assert
    expect(state.isAuthenticated).toBe(true);
    expect(state.uid).toBe(2);
    expect(state.apiKey).toBe('test-key');
    expect(state.error).toBeNull();
  });

  it('errorDeRed_estadoPasaAError: cuando login lanza error de red, el estado tiene error no vacío', async () => {
    // Arrange: authService.login simula un error de red
    authService.login.mockRejectedValue(new Error('Error de red: Failed to fetch'));

    const initial = buildInitialState();

    // Act
    const { state } = await runLoginFlow(initial, 'admin', 'clave-invalida');

    // Assert
    expect(state.isAuthenticated).toBe(false);
    expect(state.uid).toBeNull();
    expect(state.error).toBeTruthy();
    expect(state.error).toContain('Error de red');
  });
});
