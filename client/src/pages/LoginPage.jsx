/**
 * LoginPage.jsx
 *
 * Formulario de login. Las credenciales se envían al AuthProvider,
 * que las delega a authService → odooClient. Nunca se almacenan
 * en el código ni en variables de entorno del cliente.
 */
import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../store/authStore.js';

export default function LoginPage() {
  const { login, loading, error } = useAuth();
  const navigate = useNavigate();

  const [loginName, setLoginName] = useState('');
  const [apiKey, setApiKey]       = useState('');

  async function handleSubmit(e) {
    e.preventDefault();
    try {
      await login(loginName, apiKey);
      navigate('/devices');
    } catch {
      // El error ya queda en el estado del store; no necesitamos hacer nada aquí.
    }
  }

  return (
    <div style={styles.page}>
      <form style={styles.form} onSubmit={handleSubmit} noValidate>
        <h1 style={styles.title}>NetPulse</h1>
        <p style={styles.subtitle}>Monitoreo de red</p>

        {error && (
          <div style={styles.errorBox} role="alert">
            {error}
          </div>
        )}

        <label style={styles.label} htmlFor="login">Usuario</label>
        <input
          id="login"
          style={styles.input}
          type="text"
          value={loginName}
          onChange={(e) => setLoginName(e.target.value)}
          autoComplete="username"
          required
          disabled={loading}
        />

        <label style={styles.label} htmlFor="apiKey">Contraseña / API Key</label>
        <input
          id="apiKey"
          style={styles.input}
          type="password"
          value={apiKey}
          onChange={(e) => setApiKey(e.target.value)}
          autoComplete="current-password"
          required
          disabled={loading}
        />

        <button style={styles.button} type="submit" disabled={loading || !loginName || !apiKey}>
          {loading ? 'Verificando...' : 'Iniciar sesión'}
        </button>
      </form>
    </div>
  );
}

const styles = {
  page: {
    minHeight: '100vh',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    background: '#f3f4f6',
  },
  form: {
    background: '#fff',
    padding: '2.5rem 2rem',
    borderRadius: '10px',
    boxShadow: '0 4px 16px rgba(0,0,0,0.1)',
    display: 'flex',
    flexDirection: 'column',
    gap: '0.6rem',
    width: '100%',
    maxWidth: '360px',
  },
  title: { margin: 0, fontSize: '1.75rem', fontWeight: 700, color: '#1d4ed8' },
  subtitle: { margin: '0 0 0.5rem', color: '#6b7280', fontSize: '0.9rem' },
  label: { fontSize: '0.85rem', fontWeight: 500, color: '#374151' },
  input: {
    padding: '0.6rem 0.75rem',
    borderRadius: '6px',
    border: '1px solid #d1d5db',
    fontSize: '0.95rem',
    outline: 'none',
  },
  button: {
    marginTop: '0.5rem',
    padding: '0.7rem',
    borderRadius: '6px',
    border: 'none',
    background: '#1d4ed8',
    color: '#fff',
    fontWeight: 600,
    fontSize: '0.95rem',
    cursor: 'pointer',
  },
  errorBox: {
    padding: '0.6rem 0.9rem',
    background: '#fef2f2',
    border: '1px solid #fca5a5',
    borderRadius: '6px',
    color: '#b91c1c',
    fontSize: '0.85rem',
  },
};
