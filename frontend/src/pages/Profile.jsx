import { useState, useEffect } from 'react';
import { getProfiles, getProfile, createProfile, updateProfile, addProject } from '../services/api';

function Profile() {
  const [profiles, setProfiles] = useState([]);
  const [activeProfile, setActiveProfile] = useState(null);
  const [editing, setEditing] = useState(false);
  const [form, setForm] = useState({
    name: '', tax_id: '', country: 'GR',
    turnover_year1: '', turnover_year2: '', turnover_year3: '',
    total_staff: '', phd_count: '', msc_count: '',
    certifications: '', sectors: '', geographic_reach: '',
  });
  const [projectForm, setProjectForm] = useState({
    title: '', sector: '', value_eur: '', year_completed: '', client: '', funding_source: '',
  });
  const [showProjectForm, setShowProjectForm] = useState(false);

  useEffect(() => { loadProfiles(); }, []);

  async function loadProfiles() {
    const res = await getProfiles();
    setProfiles(res.data);
    if (res.data.length > 0) loadProfile(res.data[0].id);
  }

  async function loadProfile(id) {
    const res = await getProfile(id);
    setActiveProfile(res.data);
    setForm({
      name: res.data.name || '',
      tax_id: res.data.tax_id || '',
      country: res.data.country || 'GR',
      turnover_year1: res.data.turnover_year1 || '',
      turnover_year2: res.data.turnover_year2 || '',
      turnover_year3: res.data.turnover_year3 || '',
      total_staff: res.data.total_staff || '',
      phd_count: res.data.phd_count || '',
      msc_count: res.data.msc_count || '',
      certifications: (res.data.certifications || []).join(', '),
      sectors: (res.data.sectors || []).join(', '),
      geographic_reach: (res.data.geographic_reach || []).join(', '),
    });
  }

  async function handleSave() {
    const data = {
      ...form,
      turnover_year1: form.turnover_year1 ? Number(form.turnover_year1) : null,
      turnover_year2: form.turnover_year2 ? Number(form.turnover_year2) : null,
      turnover_year3: form.turnover_year3 ? Number(form.turnover_year3) : null,
      total_staff: form.total_staff ? Number(form.total_staff) : null,
      phd_count: form.phd_count ? Number(form.phd_count) : null,
      msc_count: form.msc_count ? Number(form.msc_count) : null,
      certifications: form.certifications ? form.certifications.split(',').map(s => s.trim()) : [],
      sectors: form.sectors ? form.sectors.split(',').map(s => s.trim()) : [],
      geographic_reach: form.geographic_reach ? form.geographic_reach.split(',').map(s => s.trim()) : [],
    };

    if (activeProfile) {
      await updateProfile(activeProfile.id, data);
    } else {
      await createProfile(data);
    }
    setEditing(false);
    loadProfiles();
  }

  async function handleAddProject() {
    if (!activeProfile) return;
    const data = {
      ...projectForm,
      value_eur: projectForm.value_eur ? Number(projectForm.value_eur) : null,
      year_completed: projectForm.year_completed ? Number(projectForm.year_completed) : null,
    };
    await addProject(activeProfile.id, data);
    setProjectForm({ title: '', sector: '', value_eur: '', year_completed: '', client: '', funding_source: '' });
    setShowProjectForm(false);
    loadProfile(activeProfile.id);
  }

  function handleCreate() {
    setActiveProfile(null);
    setForm({
      name: '', tax_id: '', country: 'GR',
      turnover_year1: '', turnover_year2: '', turnover_year3: '',
      total_staff: '', phd_count: '', msc_count: '',
      certifications: '', sectors: '', geographic_reach: '',
    });
    setEditing(true);
  }

  return (
    <div>
      <div className="page-header">
        <h1>Company Profile</h1>
        <div style={{ display: 'flex', gap: 8 }}>
          {!editing && <button className="btn" onClick={() => setEditing(true)}>Edit</button>}
          <button className="btn primary" onClick={handleCreate}>+ New Profile</button>
        </div>
      </div>

      {editing ? (
        <div className="card">
          <h3 style={{ color: 'var(--text-h)', marginBottom: 16 }}>
            {activeProfile ? 'Edit Profile' : 'Create Profile'}
          </h3>
          <div className="form-grid">
            <div className="form-group">
              <label>Company Name</label>
              <input value={form.name} onChange={e => setForm({ ...form, name: e.target.value })} />
            </div>
            <div className="form-group">
              <label>Tax ID (AFM)</label>
              <input value={form.tax_id} onChange={e => setForm({ ...form, tax_id: e.target.value })} />
            </div>
            <div className="form-group">
              <label>Country</label>
              <input value={form.country} onChange={e => setForm({ ...form, country: e.target.value })} />
            </div>
            <div className="form-group">
              <label>Total Staff</label>
              <input type="number" value={form.total_staff} onChange={e => setForm({ ...form, total_staff: e.target.value })} />
            </div>
            <div className="form-group">
              <label>Turnover Year 1</label>
              <input type="number" value={form.turnover_year1} onChange={e => setForm({ ...form, turnover_year1: e.target.value })} />
            </div>
            <div className="form-group">
              <label>Turnover Year 2</label>
              <input type="number" value={form.turnover_year2} onChange={e => setForm({ ...form, turnover_year2: e.target.value })} />
            </div>
            <div className="form-group">
              <label>Turnover Year 3</label>
              <input type="number" value={form.turnover_year3} onChange={e => setForm({ ...form, turnover_year3: e.target.value })} />
            </div>
            <div className="form-group">
              <label>PhD Staff</label>
              <input type="number" value={form.phd_count} onChange={e => setForm({ ...form, phd_count: e.target.value })} />
            </div>
            <div className="form-group">
              <label>MSc Staff</label>
              <input type="number" value={form.msc_count} onChange={e => setForm({ ...form, msc_count: e.target.value })} />
            </div>
            <div className="form-group">
              <label>Certifications (comma-separated)</label>
              <input value={form.certifications} onChange={e => setForm({ ...form, certifications: e.target.value })} placeholder="ISO 9001, ISO 27001" />
            </div>
            <div className="form-group">
              <label>Sectors (comma-separated)</label>
              <input value={form.sectors} onChange={e => setForm({ ...form, sectors: e.target.value })} placeholder="digital, environment, defence" />
            </div>
            <div className="form-group">
              <label>Geographic Reach (comma-separated)</label>
              <input value={form.geographic_reach} onChange={e => setForm({ ...form, geographic_reach: e.target.value })} placeholder="GR, CY, BG" />
            </div>
          </div>
          <div style={{ marginTop: 20, display: 'flex', gap: 8 }}>
            <button className="btn primary" onClick={handleSave}>Save</button>
            <button className="btn" onClick={() => setEditing(false)}>Cancel</button>
          </div>
        </div>
      ) : activeProfile ? (
        <>
          <div className="card" style={{ marginBottom: 24 }}>
            <h3 style={{ color: 'var(--text-h)', marginBottom: 16 }}>{activeProfile.name}</h3>
            <div className="card-grid" style={{ gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))' }}>
              <div><label>Country</label><div style={{ color: 'var(--text-h)' }}>{activeProfile.country}</div></div>
              <div><label>Staff</label><div style={{ color: 'var(--text-h)' }}>{activeProfile.total_staff || '—'}</div></div>
              <div><label>Avg Turnover</label><div style={{ color: 'var(--text-h)' }}>{activeProfile.avg_turnover ? `${(activeProfile.avg_turnover/1000000).toFixed(1)}M` : '—'}</div></div>
              <div><label>Sectors</label><div style={{ color: 'var(--text-h)' }}>{(activeProfile.sectors || []).join(', ') || '—'}</div></div>
              <div><label>Certifications</label><div style={{ color: 'var(--text-h)' }}>{(activeProfile.certifications || []).join(', ') || '—'}</div></div>
            </div>
          </div>

          <div className="card">
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
              <h3 style={{ color: 'var(--text-h)' }}>Completed Projects ({(activeProfile.completed_projects || []).length})</h3>
              <button className="btn primary" onClick={() => setShowProjectForm(!showProjectForm)}>+ Add Project</button>
            </div>

            {showProjectForm && (
              <div style={{ background: 'var(--bg)', padding: 16, borderRadius: 'var(--radius)', marginBottom: 16 }}>
                <div className="form-grid">
                  <div className="form-group">
                    <label>Title</label>
                    <input value={projectForm.title} onChange={e => setProjectForm({ ...projectForm, title: e.target.value })} />
                  </div>
                  <div className="form-group">
                    <label>Sector</label>
                    <input value={projectForm.sector} onChange={e => setProjectForm({ ...projectForm, sector: e.target.value })} />
                  </div>
                  <div className="form-group">
                    <label>Value (EUR)</label>
                    <input type="number" value={projectForm.value_eur} onChange={e => setProjectForm({ ...projectForm, value_eur: e.target.value })} />
                  </div>
                  <div className="form-group">
                    <label>Year Completed</label>
                    <input type="number" value={projectForm.year_completed} onChange={e => setProjectForm({ ...projectForm, year_completed: e.target.value })} />
                  </div>
                  <div className="form-group">
                    <label>Client</label>
                    <input value={projectForm.client} onChange={e => setProjectForm({ ...projectForm, client: e.target.value })} />
                  </div>
                  <div className="form-group">
                    <label>Funding Source</label>
                    <input value={projectForm.funding_source} onChange={e => setProjectForm({ ...projectForm, funding_source: e.target.value })} placeholder="ESPA, Horizon, etc." />
                  </div>
                </div>
                <div style={{ marginTop: 12, display: 'flex', gap: 8 }}>
                  <button className="btn primary" onClick={handleAddProject}>Add</button>
                  <button className="btn" onClick={() => setShowProjectForm(false)}>Cancel</button>
                </div>
              </div>
            )}

            {(activeProfile.completed_projects || []).length > 0 ? (
              <table>
                <thead>
                  <tr><th>Title</th><th>Sector</th><th>Value</th><th>Year</th><th>Client</th></tr>
                </thead>
                <tbody>
                  {activeProfile.completed_projects.map(p => (
                    <tr key={p.id}>
                      <td style={{ color: 'var(--text-h)' }}>{p.title}</td>
                      <td>{p.sector || '—'}</td>
                      <td>{p.value_eur ? `${(p.value_eur/1000).toFixed(0)}K` : '—'}</td>
                      <td>{p.year_completed || '—'}</td>
                      <td>{p.client || '—'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            ) : (
              <div className="loading">No projects yet. Add your completed projects to improve matching.</div>
            )}
          </div>
        </>
      ) : (
        <div className="card loading">
          No profile yet. Click "+ New Profile" to create your company profile.
        </div>
      )}
    </div>
  );
}

export default Profile;
