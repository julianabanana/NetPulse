import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../store/authStore.js';
import { useApp } from '../store/appStore.jsx';
import { listIncidents } from '../services/incidentService.js';
import { AuthError } from '../api/odooClient.js';
import StateWrapper from '../components/StateWrapper.jsx';
import IncidentCard from '../components/IncidentCard.jsx';

const STATE_OPTIONS = [
  { value: '', label: 'Todas' },
  { value: 'pending', label: 'Pendientes' },
  { value: 'in_progress', label: 'En progreso' },
  { value: 'resolved', label: 'Resueltas' },
];

export default function IncidentsPage() {
  const { logout } = useAuth();
  const { incidentStateFilter, setIncidentFilter } = useApp();
  const navigate = useNavigate();
  const [incidents, setIncidents] = useState([]);
  const [loading,   setLoading]   = useState(true);
  const [error,     setError]     = useState(null);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError(null);
    listIncidents(incidentStateFilter || null)
      .then((data) => { if (!cancelled) setIncidents(data ?? []); })
      .catch((err) => {
        if (cancelled) return;
        if (err instanceof AuthError) { logout(); navigate('/login'); return; }
        setError(err);
      })
      .finally(() => { if (!cancelled) setLoading(false); });
    return () => { cancelled = true; };
  }, [incidentStateFilter]);

  return (
    <div style={styles.page}>
      <div style={styles.header}>
        <h2 style={styles.title}>Incidencias</h2>
        <button style={styles.btnPrimary} onClick={() => navigate('/incidents/new')}>
          + Nueva incidencia
        </button>
      </div>
      <div style={styles.filterBar}>
        {STATE_OPTIONS.map((opt) => (
          <button key={opt.value}
            style={{ ...styles.filterBtn, ...(incidentStateFilter === opt.value ? styles.filterBtnActive : {}) }}
            onClick={() => setIncidentFilter(opt.value)}>
            {opt.label}
          </button>
        ))}
      </div>
      <StateWrapper loading={loading} error={error} empty={!loading && incidents.length === 0} emptyMessage="No hay incidencias">
        <div style={styles.list}>
          {incidents.map((inc) => <IncidentCard key={inc.id} incident={inc} />)}
        </div>
      </StateWrapper>
    </div>
  );
}

const styles = {
  page: { padding: '1.5rem 2rem' },
  header: { display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' },
  title: { margin: 0, fontSize: '1.4rem', fontWeight: 700, color: '#111827' },
  btnPrimary: { padding: '0.5rem 1.1rem', borderRadius: '6px', border: 'none', background: '#1d4ed8', color: '#fff', fontWeight: 600, cursor: 'pointer', fontSize: '0.9rem' },
  filterBar: { display: 'flex', gap: '0.5rem', marginBottom: '1.25rem', flexWrap: 'wrap' },
  filterBtn: { padding: '0.35rem 0.9rem', borderRadius: '999px', border: '1px solid #d1d5db', background: '#fff', color: '#374151', cursor: 'pointer', fontSize: '0.85rem', fontWeight: 500 },
  filterBtnActive: { background: '#1d4ed8', color: '#fff', border: '1px solid #1d4ed8' },
  list: { display: 'flex', flexDirection: 'column', gap: '0.75rem' },
};
