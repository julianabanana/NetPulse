import { createContext, useContext } from 'react';
import * as authService from '../services/authService.js';

export function buildInitialState() {
  const session = authService.getSession();
  return {
    uid:             session?.uid   ?? null,
    login:           session?.login ?? null,
    name:            session?.name  ?? null,
    isAuthenticated: !!session?.uid,
    loading:         false,
    error:           null,
  };
}

export function authReducer(state, action) {
  switch (action.type) {
    case 'LOGIN_START':
      return { ...state, loading: true, error: null };
    case 'LOGIN_SUCCESS':
      return {
        ...state,
        loading:         false,
        isAuthenticated: true,
        uid:             action.payload.uid,
        login:           action.payload.login,
        name:            action.payload.name,
        error:           null,
      };
    case 'LOGIN_FAILURE':
      return { ...state, loading: false, error: action.payload };
    case 'LOGOUT':
      return { ...buildInitialState(), isAuthenticated: false, uid: null, login: null, name: null };
    default:
      return state;
  }
}

export const AuthContext = createContext(null);

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth debe usarse dentro de <AuthProvider>');
  return ctx;
}
