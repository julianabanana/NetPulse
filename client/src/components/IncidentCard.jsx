/**
 * IncidentCard.jsx
 *
 * Tarjeta resumen de una incidencia. Muestra estado, prioridad
 * y el dispositivo afectado con un enlace al detalle.
 */
import { useNavigate } from 'react-router-dom';

const STATE_STYLES = {
  pending:     { bg: '#fef9c3', text: '#854d0e', label: 'Pendiente' },
  in_progress: { bg: '#dbeafe', text: '#1e40af', label: 'En progreso' },
  resolved:    { bg: '#dcfce7', text: '#166534', label: 'Resuelta' },
};

const PRIORITY_LABELS = { 0: 'Baja', 1: 'Media', 2: 'Alta' };
const PRIORITY_COLORS = { 0: '#6b7280', 1: '#d97706', 2: '#dc2626' };

export default function IncidentCard({ incident }) {
  const navigate = useNavigate();
  const stateStyle = STATE_STYLES[incident.state] ?? STATE_STYLES.pending;
  const priorityColor = PRIORITY_COLORS[incident.priority] ?? '#6b7280';

  return (
    <div
      style={styles.card}
      onClick={() => navigate(`/incidents/${incident.id}`)}
      role="button"
      tabIndex={0}
      onKeyDown={(e) => e.key === 'Enter' && navigate(`/incidents/${incident.id}`)}
      aria-label={`Ver detalle de incidencia ${incident.name}`}
    >
      <div style={styles.header}>
        <span style={styles.name}>{incident.name}</span>
        <span style={{ ...styles.badge, background: stateStyle.bg, color: stateStyle.text }}>
          {stateStyle.label}
        </span>
      </div>
      <div style={styles.meta}>
        {incident.device_id && (
          <span>Dispositivo: {incident.device_id[1] ?? incident.device_id}</span>
        )}
        <span style={{ color: priorityColor, fontWeight: 500 }}>
          Prioridad: {PRIORITY_LABELS[incident.priority] ?? '—'}
        </span>
        {incident.technician_id && (
          <span>Técnico: {incident.technician_id[1] ?? incident.technician_id}</span>
        )}
      </div>
      {incident.date_detected && (
        <div style={styles.date}>
          Detectada: {new Date(incident.date_detected).toLocaleString('es')}
        </div>
      )}
    </div>
  );
}

const styles = {
  card: {
    background: '#fff',
    border: '1px solid #e5e7eb',
    borderRadius: '8px',
    padding: '1rem 1.25rem',
    cursor: 'pointer',
    boxShadow: '0 1px 3px rgba(0,0,0,0.06)',
  },
  header: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: '0.5rem',
  },
  name: { fontWeight: 600, fontSize: '0.95rem', color: '#111827' },
  badge: {
    fontSize: '0.75rem',
    fontWeight: 600,
    padding: '2px 10px',
    borderRadius: '999px',
  },
  meta: {
    display: 'flex',
    gap: '1rem',
    fontSize: '0.85rem',
    color: '#6b7280',
    flexWrap: 'wrap',
  },
  date: {
    marginTop: '0.5rem',
    fontSize: '0.78rem',
    color: '#9ca3af',
  },
};
