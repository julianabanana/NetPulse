import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../store/authStore.js';
import { createDevice } from '../services/deviceService.js';
import { AuthError } from '../api/odooClient.js';

export default function CreateDevicePage() {
  const { logout } = useAuth();
  const navigate = useNavigate();
  const [form, setForm] = useState({ name: '', device_type: 'router', criticality: 'normal', gns3_node_id: '' });
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
      const newId = await createDevice({
        name: form.name,
        device_type: form.device_type,
        criticality: form.criticality,
        gns3_node_id: form.gns3_node_id || false,
      });
      navigate(`/devices/${newId}`);
    } catch (err) {
      if (err instanceof AuthError) { logout(); navigate('/login'); return; }
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div style={styles.page}>
      <Link to="/devices" style={styles.back}>← Volver a dispositivos</Link>
      <h2 style={styles.title}>Nuevo dispositivo</h2>
      <form style={styles.form} onSubmit={handleSubmit} noValidate>
        {error && <div style={styles.errorBox}>{error}</div>}
        <label style={styles.label}>Nombre *</label>
        <input name="name" style={styles.input} type="text" value={form.name} onChange={handleChange} required disabled={loading} />
        <label style={styles.label}>Tipo</label>
        <select name="device_type" style={styles.input} value={form.device_type} onChange={handleChange} disabled={loading}>
          <option value="router">Router</option>
          <option value="switch">Switch</option>
          <option value="other">Otro</option>
        </select>
        <label style={styles.label}>Criticidad</label>
        <select name="criticality" style={styles.input} value={form.criticality} onChange={handleChange} disabled={loading}>
          <option value="normal">Normal</option>
          <option value="critical">Crítico</option>
        </select>
        <label style={styles.label}>GNS3 Node ID</label>
        <input name="gns3_node_id" style={styles.input} type="text" value={form.gns3_node_id} onChange={handleChange} disabled={loading} placeholder="Opcional" />
        <div style={styles.buttons}>
          <button type="button" style={styles.btnSecondary} onClick={() => navigate(-1)} disabled={loading}>Cancelar</button>
          <button type="submit" style={styles.btnPrimary} disabled={loading || !form.name}>{loading ? 'Guardando...' : 'Crear dispositivo'}</button>
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
