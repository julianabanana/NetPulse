import { useState } from 'react';
import { useNavigate, useLocation, Link } from 'react-router-dom';
import { useAuth } from '../store/authStore.js';
import { createIncident } from '../services/incidentService.js';
import { AuthError } from '../api/odooClient.js';

export default function CreateIncidentPage() {
  const { logout } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const preDevice     = location.state?.deviceId   ?? '';
  const preDeviceName = location.state?.deviceName ?? '';

  const [form, setForm] = useState({ name: '', device_id: preDevice ? String(preDevice) : '', priority: '0', origin: 'manual', root_cause: '' });
  const [loading, setLoading] = useState(false);
  const [error,   setError]   = useState(null);

  function handleChange(e) {
    const { name, value } = e.target;
    setForm((prev) => ({ ...prev, [name]: value }));
  }

  async function handleSubmit(e) {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      const newId = await createIncident({
        name:       form.name,
        device_id:  form.device_id ? Number(form.device_id) : false,
        priority:   Number(form.priority),
        origin:     form.origin,
        root_cause: form.root_cause || false,
      });
      navigate(`/incidents/${newId}`);
    } catch (err) {
      if (err instanceof AuthError) { logout(); navigate('/login'); return; }
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div style={styles.page}>
      <Link to="/incidents" style={styles.back}>← Volver a incidencias</Link>
      <h2 style={styles.title}>Nueva incidencia</h2>
      <form style={styles.form} onSubmit={handleSubmit} noValidate>
        {error && <div style={styles.errorBox}>{error}</div>}
        <label style={styles.label}>Nombre *</label>
        <input name="name" style={styles.input} type="text" value={form.name} onChange={handleChange} required disabled={loading} />
        <label style={styles.label}>ID del dispositivo{preDeviceName ? ` (${preDeviceName})` : ''}</label>
        <input name="device_id" style={styles.input} type="number" value={form.device_id} onChange={handleChange} disabled={loading} />
        <label style={styles.label}>Prioridad</label>
        <select name="priority" style={styles.input} value={form.priority} onChange={handleChange} disabled={loading}>
          <option value="0">Baja</option>
          <option value="1">Media</option>
          <option value="2">Alta</option>
        </select>
        <label style={styles.label}>Origen</label>
        <input name="origin" style={styles.input} type="text" value={form.origin} onChange={handleChange} disabled={loading} />
        <label style={styles.label}>Causa raíz</label>
        <textarea name="root_cause" style={{ ...styles.input, minHeight: '80px', resize: 'vertical' }} value={form.root_cause} onChange={handleChange} disabled={loading} />
        <div style={styles.buttons}>
          <button type="button" style={styles.btnSecondary} onClick={() => navigate(-1)} disabled={loading}>Cancelar</button>
          <button type="submit" style={styles.btnPrimary} disabled={loading || !form.name}>{loading ? 'Guardando...' : 'Crear incidencia'}</button>
        </div>
      </form>
    </div>
  );
}

const styles = {
  page: { padding: '1.5rem 2rem', maxWidth: '560px' },
  back: { color: '#1d4ed8', fontSize: '0.9rem', textDecoration: 'none', display: 'inline-block', marginBottom: '1rem' },
  title: { margin: '0 0 1.25rem', fontSize: '1.4rem', fontWeight: 700 },
  form: { display: 'flex', flexDirection: 'column', gap: '0.6rem' },
  label: { fontSize: '0.85rem', fontWeight: 500, color: '#374151' },
  input: { padding: '0.6rem 0.75rem', borderRadius: '6px', border: '1px solid #d1d5db', fontSize: '0.9rem' },
  buttons: { display: 'flex', gap: '0.75rem', marginTop: '0.75rem', justifyContent: 'flex-end' },
  btnPrimary: { padding: '0.55rem 1.2rem', borderRadius: '6px', border: 'none', background: '#1d4ed8', color: '#fff', fontWeight: 600, cursor: 'pointer' },
  btnSecondary: { padding: '0.55rem 1.2rem', borderRadius: '6px', border: '1px solid #d1d5db', background: '#fff', fontWeight: 600, cursor: 'pointer' },
  errorBox: { padding: '0.6rem 0.9rem', background: '#fef2f2', border: '1px solid #fca5a5', borderRadius: '6px', color: '#b91c1c', fontSize: '0.85rem' },
};
