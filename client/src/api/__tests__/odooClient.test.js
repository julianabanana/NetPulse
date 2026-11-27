/**
 * Pruebas de integración del cliente HTTP (odooClient).
 * Se mockea fetch a nivel global para simular respuestas de Odoo
 * sin levantar ningún servidor real.
 */
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { jsonrpc, AuthError } from '../odooClient.js';

// Vitest necesita que el entorno tenga BASE_URL definido;
// el vite.config.js usa jsdom, pero import.meta.env no se rellena
// automáticamente en pruebas, así que lo seteamos aquí.
vi.stubEnv('VITE_ODOO_URL', 'http://localhost:8069');

// Helper: crea un mock de fetch que devuelve el cuerpo dado.
function mockFetch(body) {
  global.fetch = vi.fn().mockResolvedValue({
    ok: true,
    json: () => Promise.resolve(body),
  });
}

beforeEach(() => {
  vi.restoreAllMocks();
});

describe('odooClient › jsonrpc', () => {
  it('respuestaExitosa_mapeaResultado: devuelve el array del campo result', async () => {
    // Arrange: fetch simula una respuesta JSON-RPC exitosa con una lista de dispositivos
    mockFetch({ jsonrpc: '2.0', id: 1, result: [{ id: 1, name: 'SW2' }] });

    // Act
    const result = await jsonrpc({
      service: 'object',
      method: 'execute_kw',
      args: ['netpulse', 1, 'key', 'netpulse.device', 'search_read', [[]], {}],
    });

    // Assert
    expect(result).toEqual([{ id: 1, name: 'SW2' }]);
    expect(fetch).toHaveBeenCalledOnce();
  });

  it('accessDenied_lanzaErrorTipado: lanza AuthError cuando Odoo devuelve AccessDenied', async () => {
    // Arrange: fetch simula la respuesta de error que Odoo devuelve con HTTP 200
    mockFetch({
      jsonrpc: '2.0',
      id: 1,
      error: {
        code: 100,
        message: 'Odoo Server Error',
        data: {
          name: 'odoo.exceptions.AccessDenied',
          message: 'Access Denied',
        },
      },
    });

    // Act & Assert: debe lanzar exactamente AuthError, no un Error genérico
    await expect(
      jsonrpc({ service: 'common', method: 'authenticate', args: [] })
    ).rejects.toBeInstanceOf(AuthError);
  });
});
