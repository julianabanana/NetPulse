/**
 * AuthProvider.jsx
 *
 * Componente que envuelve la app y provee el contexto de autenticacion.
 * Esta en un .jsx separado de authStore.js para que las pruebas unitarias
 * puedan importar el reducer sin que Vite intente compilar JSX en un .js.
 */
import { useReducer } from 'react';
import * as authService from '../services/authService.js';
import { AuthContext, authReducer, buildInitialState } from './authStore.js';

export function AuthProvider({ children }) {
  const [state, dispatch] = useReducer(authReducer, null, buildInitialState);

  async function login(loginName, apiKey) {
    dispatch({ type: 'LOGIN_START' });
    try {
      const session = await authService.login(loginName, apiKey);
      dispatch({ type: 'LOGIN_SUCCESS', payload: session });
      return session;
    } catch (err) {
      dispatch({ type: 'LOGIN_FAILURE', payload: err.message });
      throw err;
    }
  }

  function logout() {
    authService.logout();
    dispatch({ type: 'LOGOUT' });
  }

  return (
    <AuthContext.Provider value={{ ...state, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
}
