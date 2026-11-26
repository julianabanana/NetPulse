/**
 * DeviceCard.jsx
 *
 * Tarjeta que resume la información de un dispositivo de red.
 * El color del badge de estado comunica visualmente si está activo.
 */
import { useNavigate } from 'react-router-dom';

const STATUS_COLORS = {
  up:      { bg: '#dcfce7', text: '#166534', label: 'Activo' },
  down:    { bg: '#fee2e2', text: '#991b1b', label: 'Caído' },
  unknown: { bg: '#fef9c3', text: '#854d0e', label: 'Desconocido' },
};

const CRITICALITY_LABELS = {
  critical: 'Crítico',
  normal:   'Normal',
};

export default function DeviceCard({ device }) {
  const navigate = useNavigate();
  const statusStyle = STATUS_COLORS[device.status] ?? STATUS_COLORS.unknown;

  return (
    <div
      style={styles.card}
      onClick={() => navigate(`/devices/${device.id}`)}
      role="button"
      tabIndex={0}
      onKeyDown={(e) => e.key === 'Enter' && navigate(`/devices/${device.id}`)}
      aria-label={`Ver detalle de ${device.name}`}
    >
      <div style={styles.header}>
        <span style={styles.name}>{device.name}</span>
        <span style={{ ...styles.badge, background: statusStyle.bg, color: statusStyle.text }}>
          {statusStyle.label}
        </span>
      </div>
      <div style={styles.meta}>
        <span>Tipo: {device.device_type ?? '—'}</span>
        <span>Criticidad: {CRITICALITY_LABELS[device.criticality] ?? device.criticality ?? '—'}</span>
        {device.open_incident_count > 0 && (
          <span style={styles.incidentCount}>
            {device.open_incident_count} incidencia{device.open_incident_count !== 1 ? 's' : ''} abierta{device.open_incident_count !== 1 ? 's' : ''}
          </span>
        )}
      </div>
      {device.last_seen && (
        <div style={styles.lastSeen}>
          Último contacto: {new Date(device.last_seen).toLocaleString('es')}
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
    transition: 'box-shadow 0.15s',
    boxShadow: '0 1px 3px rgba(0,0,0,0.06)',
  },
  header: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: '0.5rem',
  },
  name: { fontWeight: 600, fontSize: '1rem', color: '#111827' },
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
  incidentCount: {
    color: '#dc2626',
    fontWeight: 500,
  },
  lastSeen: {
    marginTop: '0.5rem',
    fontSize: '0.78rem',
    color: '#9ca3af',
  },
};
