/**
 * main.jsx
 *
 * Punto de entrada de la aplicación React.
 * El modo StrictMode activa advertencias adicionales en desarrollo.
 */
import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import App from './App.jsx';

// Estilos globales mínimos (reset básico + animación del spinner)
const globalStyle = document.createElement('style');
globalStyle.textContent = `
  *, *::before, *::after { box-sizing: border-box; }
  body { margin: 0; font-family: system-ui, -apple-system, sans-serif; }
  dt { font-weight: 500; color: #374151; }
  dd { margin: 0; color: #111827; }
  @keyframes spin { to { transform: rotate(360deg); } }
`;
document.head.appendChild(globalStyle);

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <App />
  </StrictMode>
);
