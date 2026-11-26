import { useState, useEffect } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../store/authStore.js';
import { getDevice } from '../services/deviceService.js';
import { listIncidentsByDevice } from '../services/incidentService.js';
import { AuthError } from '../api/odooClient.js';
import StateWrapper from '../components/StateWrapper.jsx';
import IncidentCard from '../components/IncidentCard.jsx';

const STATUS_LABELS = { up: 'Activo', down: 'Caído', unknown: 'Desconocido' };
const STATUS_COLORS = { up: '#16a34a', down: '#dc2626', unknown: '#d97706' };

export default function DeviceDetailPage() {
  const { id } = useParams();
  const { logout } = useAuth();
  const navigate = useNavigate();
  const [device,    setDevice]    = useState(null);
  const [incidents, setIncidents] = useState([]);
  const [loading,   setLoading]   = useState(true);
  const [error,     setError]     = useState(null);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError(null);
    Promise.all([getDevice(Number(id)), listIncidentsByDevice(Number(id))])
      .then(([dev, incs]) => {
        if (cancelled) return;
        setDevice(dev);
        setIncidents(incs ?? []);
      })
      .catch((err) => {
        if (cancelled) return;
        if (err instanceof AuthError) { logout(); navigate('/login'); return; }
        setError(err);
      })
      .finally(() => { if (!cancelled) setLoading(false); });
    return () => { cancelled = true; };
  }, [id]);

  return (
    <div style={styles.page}>
      <Link to="/devices" style={styles.back}>← Volver a dispositivos</Link>
      <StateWrapper loading={loading} error={error} empty={!loading && !device} emptyMessage="Dispositivo no encontrado">
        {device && (
          <>
            <div style={styles.card}>
              <div style={styles.cardHeader}>
                <h2 style={styles.deviceName}>{device.name}</h2>
                <span style={{ color: STATUS_COLORS[device.status] ?? '#6b7280', fontWeight: 600 }}>
                  {STATUS_LABELS[device.status] ?? device.status}
                </span>
              </div>
              <dl style={styles.dl}>
                <dt>Tipo</dt>             <dd>{device.device_type ?? '—'}</dd>
                <dt>Criticidad</dt>       <dd>{device.criticality === 'critical' ? 'Crítico' : 'Normal'}</dd>
                <dt>GNS3 Node ID</dt>     <dd style={styles.mono}>{device.gns3_node_id ?? '—'}</dd>
                <dt>Último contacto</dt>  <dd>{device.last_seen ? new Date(device.last_seen).toLocaleString('es') : '—'}</dd>
                <dt>Incidencias abiertas</dt> <dd>{device.open_incident_count ?? 0}</dd>
              </dl>
            </div>
            <div style={styles.section}>
              <div style={styles.sectionHeader}>
                <h3 style={styles.sectionTitle}>Incidencias</h3>
                <button style={styles.btnSmall}
                  onClick={() => navigate('/incidents/new', { state: { deviceId: device.id, deviceName: device.name } })}>
                  + Nueva incidencia
                </button>
              </div>
              {incidents.length === 0
                ? <p style={styles.empty}>No hay incidencias para este dispositivo</p>
                : <div style={styles.list}>{incidents.map((inc) => <IncidentCard key={inc.id} incident={inc} />)}</div>}
            </div>
          </>
        )}
      </StateWrapper>
    </div>
  );
}

const styles = {
  page: { padding: '1.5rem 2rem' },
  back: { color: '#1d4ed8', fontSize: '0.9rem', textDecoration: 'none', display: 'inline-block', marginBottom: '1rem' },
  card: { background: '#fff', border: '1px solid #e5e7eb', borderRadius: '8px', padding: '1.5rem', marginBottom: '1.5rem' },
  cardHeader: { display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' },
  deviceName: { margin: 0, fontSize: '1.3rem', fontWeight: 700 },
  dl: { display: 'grid', gridTemplateColumns: 'max-content 1fr', gap: '0.4rem 1.5rem', margin: 0, fontSize: '0.9rem' },
  mono: { fontFamily: 'monospace', fontSize: '0.85rem' },
  section: {},
  sectionHeader: { display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.75rem' },
  sectionTitle: { margin: 0, fontSize: '1.1rem', fontWeight: 600 },
  btnSmall: { padding: '0.4rem 0.9rem', borderRadius: '6px', border: 'none', background: '#1d4ed8', color: '#fff', fontWeight: 600, cursor: 'pointer', fontSize: '0.85rem' },
  list: { display: 'flex', flexDirection: 'column', gap: '0.75rem' },
  empty: { color: '#6b7280', fontSize: '0.9rem' },
};
