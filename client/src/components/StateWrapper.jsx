/**
 * StateWrapper.jsx
 *
 * Componente de presentación que muestra uno de cuatro estados posibles:
 *   - loading: spinner o mensaje de carga
 *   - error: mensaje de error (con distinción entre AuthError/PermissionError)
 *   - empty: mensaje cuando no hay registros
 *   - success: renderiza children
 *
 * Uso:
 *   <StateWrapper loading={loading} error={error} empty={data.length === 0}>
 *     <MiLista data={data} />
 *   </StateWrapper>
 */
import { PermissionError } from '../api/odooClient.js';

export default function StateWrapper({ loading, error, empty, emptyMessage, children }) {
  if (loading) {
    return (
      <div style={styles.center}>
        <div style={styles.spinner} aria-label="Cargando" />
        <p style={styles.muted}>Cargando...</p>
      </div>
    );
  }

  if (error) {
    // Distingue el tipo de error para mostrar el mensaje correcto
    const isPermission = error instanceof PermissionError || error?.name === 'PermissionError';
    const message = isPermission
      ? 'No tienes permiso para esta acción'
      : (error.message ?? String(error));

    return (
      <div style={styles.errorBox} role="alert">
        <strong>Error: </strong>{message}
      </div>
    );
  }

  if (empty) {
    return (
      <div style={styles.center}>
        <p style={styles.muted}>{emptyMessage ?? 'No hay registros'}</p>
      </div>
    );
  }

  return children;
}

const styles = {
  center: {
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    padding: '3rem 1rem',
    gap: '0.75rem',
  },
  muted: { color: '#6b7280', fontSize: '1rem' },
  errorBox: {
    margin: '1rem 0',
    padding: '0.85rem 1.1rem',
    borderRadius: '6px',
    background: '#fef2f2',
    border: '1px solid #fca5a5',
    color: '#b91c1c',
    fontSize: '0.95rem',
  },
  spinner: {
    width: '36px',
    height: '36px',
    border: '4px solid #e5e7eb',
    borderTopColor: '#3b82f6',
    borderRadius: '50%',
    animation: 'spin 0.8s linear infinite',
  },
};
