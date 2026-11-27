/**
 * appStore.js
 *
 * Estado global mínimo de la aplicación (filtros, notificaciones flash, etc.).
 * Se implementa con Context + useReducer; no se usa Redux.
 *
 * Este store es intencional­mente pequeño: cada página gestiona su propio
 * estado de carga/error mediante hooks locales, y solo delega aquí lo
 * que realmente necesita compartir entre páginas.
 */
import { createContext, useContext, useReducer } from 'react';

const initialState = {
  // Filtro global de incidencias (se recuerda al navegar entre páginas)
  incidentStateFilter: null,
  // Mensaje flash para notificaciones breves
  flashMessage: null,
};

function appReducer(state, action) {
  switch (action.type) {
    case 'SET_INCIDENT_FILTER':
      return { ...state, incidentStateFilter: action.payload };
    case 'SET_FLASH':
      return { ...state, flashMessage: action.payload };
    case 'CLEAR_FLASH':
      return { ...state, flashMessage: null };
    default:
      return state;
  }
}

const AppContext = createContext(null);

export function AppProvider({ children }) {
  const [state, dispatch] = useReducer(appReducer, initialState);

  function setIncidentFilter(filter) {
    dispatch({ type: 'SET_INCIDENT_FILTER', payload: filter });
  }

  function setFlash(message) {
    dispatch({ type: 'SET_FLASH', payload: message });
  }

  function clearFlash() {
    dispatch({ type: 'CLEAR_FLASH' });
  }

  return (
    <AppContext.Provider value={{ ...state, setIncidentFilter, setFlash, clearFlash }}>
      {children}
    </AppContext.Provider>
  );
}

export function useApp() {
  const ctx = useContext(AppContext);
  if (!ctx) throw new Error('useApp debe usarse dentro de <AppProvider>');
  return ctx;
}
