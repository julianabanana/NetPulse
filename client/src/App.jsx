/**
 * App.jsx
 *
 * Raíz de la aplicación. Define el árbol de providers y el router.
 *
 * Estructura de providers (de exterior a interior):
 *   AuthProvider  → estado de sesión
 *   AppProvider   → estado global mínimo
 *   BrowserRouter → enrutamiento
 *
 * Las rutas protegidas redirigen al login si no hay sesión activa.
 */
import { BrowserRouter, Routes, Route, Navigate, Outlet } from 'react-router-dom';
import { AuthProvider } from './store/AuthProvider.jsx';
import { useAuth } from './store/authStore.js';
import { AppProvider } from './store/appStore.jsx';

import LoginPage           from './pages/LoginPage.jsx';
import DevicesPage         from './pages/DevicesPage.jsx';
import DeviceDetailPage    from './pages/DeviceDetailPage.jsx';
import CreateDevicePage    from './pages/CreateDevicePage.jsx';
import IncidentsPage       from './pages/IncidentsPage.jsx';
import IncidentDetailPage  from './pages/IncidentDetailPage.jsx';
import CreateIncidentPage  from './pages/CreateIncidentPage.jsx';

// ── Guard de rutas protegidas ────────────────────────────────────────────────

function PrivateRoute() {
  const { isAuthenticated } = useAuth();
  if (!isAuthenticated) return <Navigate to="/login" replace />;
  return (
    <div style={appStyles.layout}>
      <Nav />
      <main style={appStyles.main}>
        <Outlet />
      </main>
    </div>
  );
}

// ── Barra de navegación ──────────────────────────────────────────────────────

function Nav() {
  const { login: loginName, logout } = useAuth();
  return (
    <nav style={appStyles.nav}>
      <span style={appStyles.navBrand}>NetPulse</span>
      <div style={appStyles.navLinks}>
        <a href="/devices"   style={appStyles.navLink}>Dispositivos</a>
        <a href="/incidents" style={appStyles.navLink}>Incidencias</a>
      </div>
      <div style={appStyles.navUser}>
        <span style={appStyles.navUsername}>{loginName}</span>
        <button style={appStyles.btnLogout} onClick={logout}>Salir</button>
      </div>
    </nav>
  );
}

// ── Componente raíz ──────────────────────────────────────────────────────────

export default function App() {
  return (
    <AuthProvider>
      <AppProvider>
        <BrowserRouter>
          <Routes>
            <Route path="/login" element={<LoginPage />} />

            {/* Rutas protegidas: requieren sesión activa */}
            <Route element={<PrivateRoute />}>
              <Route path="/devices"          element={<DevicesPage />} />
              <Route path="/devices/new"      element={<CreateDevicePage />} />
              <Route path="/devices/:id"      element={<DeviceDetailPage />} />
              <Route path="/incidents"        element={<IncidentsPage />} />
              <Route path="/incidents/new"    element={<CreateIncidentPage />} />
              <Route path="/incidents/:id"    element={<IncidentDetailPage />} />
            </Route>

            {/* Redirigir la raíz a dispositivos */}
            <Route path="/" element={<Navigate to="/devices" replace />} />
            <Route path="*" element={<Navigate to="/devices" replace />} />
          </Routes>
        </BrowserRouter>
      </AppProvider>
    </AuthProvider>
  );
}

// ── Estilos del layout ───────────────────────────────────────────────────────

const appStyles = {
  layout: { minHeight: '100vh', display: 'flex', flexDirection: 'column', background: '#f9fafb' },
  nav: {
    display: 'flex',
    alignItems: 'center',
    padding: '0 2rem',
    height: '56px',
    background: '#1e3a8a',
    color: '#fff',
    gap: '1.5rem',
    flexShrink: 0,
  },
  navBrand: { fontWeight: 700, fontSize: '1.1rem', marginRight: '1rem' },
  navLinks: { display: 'flex', gap: '1.25rem', flex: 1 },
  navLink: { color: '#bfdbfe', textDecoration: 'none', fontSize: '0.9rem', fontWeight: 500 },
  navUser: { display: 'flex', alignItems: 'center', gap: '0.75rem', marginLeft: 'auto' },
  navUsername: { fontSize: '0.85rem', color: '#bfdbfe' },
  btnLogout: {
    padding: '0.3rem 0.8rem',
    borderRadius: '5px',
    border: '1px solid #93c5fd',
    background: 'transparent',
    color: '#fff',
    cursor: 'pointer',
    fontSize: '0.8rem',
  },
  main: { flex: 1, overflowY: 'auto' },
};
