import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../store/authStore.js';
import { listDevices } from '../services/deviceService.js';
import { AuthError } from '../api/odooClient.js';
import StateWrapper from '../components/StateWrapper.jsx';
import DeviceCard from '../components/DeviceCard.jsx';

export default function DevicesPage() {
  const { logout } = useAuth();
  const navigate = useNavigate();
  const [devices, setDevices] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError]     = useState(null);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError(null);
    listDevices()
      .then((data) => { if (!cancelled) setDevices(data ?? []); })
      .catch((err) => {
        if (cancelled) return;
        if (err instanceof AuthError) { logout(); navigate('/login'); return; }
        setError(err);
      })
      .finally(() => { if (!cancelled) setLoading(false); });
    return () => { cancelled = true; };
  }, []);

  return (
    <div style={styles.page}>
      <div style={styles.header}>
        <h2 style={styles.title}>Dispositivos</h2>
        <button style={styles.btnPrimary} onClick={() => navigate('/devices/new')}>
          + Nuevo dispositivo
        </button>
      </div>
      <StateWrapper loading={loading} error={error} empty={!loading && devices.length === 0} emptyMessage="No hay dispositivos registrados">
        <div style={styles.grid}>
          {devices.map((d) => <DeviceCard key={d.id} device={d} />)}
        </div>
      </StateWrapper>
    </div>
  );
}

const styles = {
  page:       { padding: '1.5rem 2rem' },
  header:     { display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.25rem' },
  title:      { margin: 0, fontSize: '1.4rem', fontWeight: 700, color: '#111827' },
  btnPrimary: { padding: '0.5rem 1.1rem', borderRadius: '6px', border: 'none', background: '#1d4ed8', color: '#fff', fontWeight: 600, cursor: 'pointer', fontSize: '0.9rem' },
  grid:       { display: 'grid', gap: '0.85rem', gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))' },
};
