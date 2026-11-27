import { useState, useEffect } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../store/authStore.js';
import { getIncident, startIncident, resolveIncident, updateIncident, deleteIncident } from '../services/incidentService.js';
import { AuthError, PermissionError } from '../api/odooClient.js';
import StateWrapper from '../components/StateWrapper.jsx';

const STATE_LABELS    = { pending: 'Pendiente', in_progress: 'En progreso', resolved: 'Resuelta' };
const PRIORITY_LABELS = { 0: 'Baja', 1: 'Media', 2: 'Alta' };

export default function IncidentDetailPage() {
  const { id } = useParams();
  const { logout } = useAuth();
  const navigate = useNavigate();
  const [incident,      setIncident]      = useState(null);
  const [loading,       setLoading]       = useState(true);
  const [error,         setError]         = useState(null);
  const [actionError,   setActionError]   = useState(null);
  const [actionLoading, setActionLoading] = useState(false);
  const [techInput,     setTechInput]     = useState('');
  const [showAssign,    setShowAssign]    = useState(false);

  function fetchIncident() {
    setLoading(true);
    setError(null);
    getIncident(Number(id))
      .then(setIncident)
      .catch((err) => {
        if (err instanceof AuthError) { logout(); navigate('/login'); return; }
        setError(err);
      })
      .finally(() => setLoading(false));
  }

  useEffect(fetchIncident, [id]);

  async function handleAction(fn) {
    setActionLoading(true);
    setActionError(null);
    try {
      await fn();
      fetchIncident();
    } catch (err) {
      if (err instanceof AuthError) { logout(); navigate('/login'); return; }
      setActionError(err instanceof PermissionError ? 'No tienes permiso para esta acción' : err.message);
    } finally {
      setActionLoading(false);
    }
  }

  return (
    <div style={styles.page}>
      <Link to="/incidents" style={styles.back}>← Volver a incidencias</Link>
      <StateWrapper loading={loading} error={error} empty={!loading && !incident} emptyMessage="Incidencia no encontrada">
        {incident && (
          <div style={styles.card}>
            <div style={styles.cardHeader}>
              <h2 style={styles.incidentName}>{incident.name}</h2>
              <span style={styles.stateBadge}>{STATE_LABELS[incident.state] ?? incident.state}</span>
            </div>
            <dl style={styles.dl}>
              <dt>Dispositivo</dt>   <dd>{incident.device_id ? <Link to={`/devices/${incident.device_id[0]}`} style={{ color: '#1d4ed8' }}>{incident.device_id[1]}</Link> : '—'}</dd>
              <dt>Prioridad</dt>     <dd>{PRIORITY_LABELS[incident.priority] ?? '—'}</dd>
              <dt>Técnico</dt>       <dd>{incident.technician_id ? incident.technician_id[1] : 'Sin asignar'}</dd>
              <dt>Origen</dt>        <dd>{incident.origin ?? '—'}</dd>
              <dt>Causa raíz</dt>    <dd>{incident.root_cause ?? '—'}</dd>
              <dt>Detectada</dt>     <dd>{incident.date_detected ? new Date(incident.date_detected).toLocaleString('es') : '—'}</dd>
              <dt>Resuelta</dt>      <dd>{incident.date_resolved ? new Date(incident.date_resolved).toLocaleString('es') : '—'}</dd>
            </dl>
            {actionError && <div style={styles.actionError}>{actionError}</div>}
            <div style={styles.actions}>
              {incident.state === 'pending' && (
                <button style={styles.btnAction} disabled={actionLoading}
                  onClick={() => handleAction(() => startIncident(Number(id)))}>
                  Iniciar atención
                </button>
              )}
              {incident.state === 'in_progress' && (
                <button style={{ ...styles.btnAction, background: '#16a34a' }} disabled={actionLoading}
                  onClick={() => handleAction(() => resolveIncident(Number(id)))}>
                  Marcar resuelta
                </button>
              )}
              {incident.state !== 'resolved' && (
                <>
                  <button style={{ ...styles.btnAction, background: '#6b7280' }} disabled={actionLoading}
                    onClick={() => setShowAssign((v) => !v)}>
                    Asignar técnico
                  </button>
                  {showAssign && (
                    <div style={styles.assignBox}>
                      <input style={styles.assignInput} type="number" placeholder="ID del técnico"
                        value={techInput} onChange={(e) => setTechInput(e.target.value)} />
                      <button style={styles.btnAssign} disabled={actionLoading}
                        onClick={() => handleAction(() => updateIncident(Number(id), { technician_id: Number(techInput) }))}>
                        Confirmar
                      </button>
                    </div>
                  )}
                </>
              )}
              <button style={{ ...styles.btnAction, background: '#dc2626', marginLeft: 'auto' }} disabled={actionLoading}
                onClick={() => { if (window.confirm('¿Eliminar esta incidencia?')) handleAction(async () => { await deleteIncident(Number(id)); navigate('/incidents'); }); }}>
                Eliminar
              </button>
            </div>
          </div>
        )}
      </StateWrapper>
    </div>
  );
}

const styles = {
  page: { padding: '1.5rem 2rem' },
  back: { color: '#1d4ed8', fontSize: '0.9rem', textDecoration: 'none', display: 'inline-block', marginBottom: '1rem' },
  card: { background: '#fff', border: '1px solid #e5e7eb', borderRadius: '8px', padding: '1.5rem' },
  cardHeader: { display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' },
  incidentName: { margin: 0, fontSize: '1.3rem', fontWeight: 700 },
  stateBadge: { padding: '3px 12px', borderRadius: '999px', background: '#dbeafe', color: '#1e40af', fontWeight: 600, fontSize: '0.8rem' },
  dl: { display: 'grid', gridTemplateColumns: 'max-content 1fr', gap: '0.45rem 1.5rem', margin: '0 0 1.25rem', fontSize: '0.9rem' },
  actions: { display: 'flex', gap: '0.75rem', flexWrap: 'wrap', alignItems: 'center', marginTop: '0.5rem' },
  btnAction: { padding: '0.5rem 1.1rem', borderRadius: '6px', border: 'none', background: '#1d4ed8', color: '#fff', fontWeight: 600, cursor: 'pointer', fontSize: '0.9rem' },
  actionError: { padding: '0.6rem 0.9rem', background: '#fef2f2', border: '1px solid #fca5a5', borderRadius: '6px', color: '#b91c1c', fontSize: '0.85rem', marginBottom: '0.75rem' },
  assignBox: { display: 'flex', gap: '0.5rem', alignItems: 'center', width: '100%' },
  assignInput: { padding: '0.5rem 0.75rem', borderRadius: '6px', border: '1px solid #d1d5db', fontSize: '0.9rem', width: '220px' },
  btnAssign: { padding: '0.5rem 1rem', borderRadius: '6px', border: 'none', background: '#1d4ed8', color: '#fff', fontWeight: 600, cursor: 'pointer' },
};
