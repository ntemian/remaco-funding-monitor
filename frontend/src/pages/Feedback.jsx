import { useState, useEffect } from 'react';
import { submitFeedback, getFeedback, getMatchStats, getCallStats, getProfiles } from '../services/api';

function Feedback() {
  const [form, setForm] = useState({ name: 'Georg Dafnos', type: 'feature', message: '' });
  const [submissions, setSubmissions] = useState([]);
  const [submitted, setSubmitted] = useState(false);
  const [matchStats, setMatchStats] = useState(null);
  const [callStats, setCallStats] = useState(null);

  useEffect(() => {
    loadData();
  }, []);

  async function loadData() {
    getFeedback().then(r => setSubmissions(r.data)).catch(() => {});
    getCallStats().then(r => setCallStats(r.data)).catch(() => {});
    getProfiles().then(r => {
      if (r.data.length > 0) {
        getMatchStats(r.data[0].id).then(r2 => setMatchStats(r2.data)).catch(() => {});
      }
    }).catch(() => {});
  }

  async function handleSubmit(e) {
    e.preventDefault();
    if (!form.message.trim()) return;
    try {
      await submitFeedback(form);
      setForm({ ...form, message: '' });
      setSubmitted(true);
      setTimeout(() => setSubmitted(false), 3000);
      loadData();
    } catch (err) {
      alert('Failed to submit: ' + err.message);
    }
  }

  const typeLabels = {
    feature: 'New Feature',
    source: 'New Data Source',
    filter: 'Filter / Sector',
    bug: 'Bug Report',
    other: 'Other',
  };

  // Simple bar chart component
  function BarChart({ data, colors }) {
    const max = Math.max(...data.map(d => d.value), 1);
    return (
      <div style={{ display: 'flex', alignItems: 'flex-end', gap: 16, height: 120, padding: '0 8px' }}>
        {data.map((d, i) => (
          <div key={i} style={{ flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 6 }}>
            <span style={{ fontSize: 14, fontWeight: 700, color: colors[i] }}>{d.value}</span>
            <div style={{
              width: '100%', maxWidth: 60,
              height: `${Math.max((d.value / max) * 80, 4)}px`,
              background: colors[i], borderRadius: '4px 4px 0 0',
              transition: 'height 0.5s ease',
            }} />
            <span style={{ fontSize: 11, color: 'var(--text)', textAlign: 'center', fontWeight: 600 }}>{d.label}</span>
          </div>
        ))}
      </div>
    );
  }

  // Donut chart component
  function DonutChart({ data, colors, size = 120 }) {
    const total = data.reduce((s, d) => s + d.value, 0) || 1;
    let cumulative = 0;
    const segments = data.map((d, i) => {
      const start = cumulative;
      cumulative += (d.value / total) * 360;
      return { ...d, start, end: cumulative, color: colors[i] };
    });

    const gradientParts = segments.map(s => `${s.color} ${s.start}deg ${s.end}deg`).join(', ');

    return (
      <div style={{ display: 'flex', alignItems: 'center', gap: 20 }}>
        <div style={{
          width: size, height: size, borderRadius: '50%',
          background: `conic-gradient(${gradientParts})`,
          display: 'flex', alignItems: 'center', justifyContent: 'center',
        }}>
          <div style={{ width: size * 0.6, height: size * 0.6, borderRadius: '50%', background: 'var(--surface)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <span style={{ fontSize: 20, fontWeight: 800, color: 'var(--text-h)' }}>{total}</span>
          </div>
        </div>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
          {data.map((d, i) => (
            <div key={i} style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: 13 }}>
              <div style={{ width: 10, height: 10, borderRadius: 2, background: colors[i] }} />
              <span style={{ color: 'var(--text)' }}>{d.label}</span>
              <span style={{ fontWeight: 700, color: 'var(--text-h)' }}>{d.value}</span>
            </div>
          ))}
        </div>
      </div>
    );
  }

  return (
    <div>
      <div className="page-header">
        <h1>Feedback & Analytics</h1>
      </div>

      {/* Visualization */}
      {(matchStats || callStats) && (
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 20, marginBottom: 24 }}>
          {matchStats && (
            <div className="card">
              <h3 style={{ color: 'var(--text-h)', marginBottom: 16 }}>Match Distribution</h3>
              <DonutChart
                data={[
                  { label: 'Go', value: matchStats.go },
                  { label: 'Consortium', value: matchStats.consortium },
                  { label: 'No Go', value: matchStats.no_go },
                ]}
                colors={['#0fa968', '#e5a100', '#d94040']}
              />
            </div>
          )}
          {callStats && (
            <div className="card">
              <h3 style={{ color: 'var(--text-h)', marginBottom: 16 }}>Calls by Source</h3>
              <BarChart
                data={Object.entries(callStats.sources || {})
                  .filter(([, v]) => v > 0)
                  .map(([k, v]) => ({ label: k.toUpperCase(), value: v }))}
                colors={['#0056a6', '#0fa968', '#e5a100', '#d94040', '#8b5cf6', '#f97316']}
              />
            </div>
          )}
        </div>
      )}

      {/* System Description */}
      <div className="card" style={{ marginBottom: 24, background: 'linear-gradient(135deg, #0a1a3a 0%, #0d2d5e 100%)', color: '#fff', border: 'none' }}>
        <h3 style={{ color: '#fff', marginBottom: 8 }}>How this system works</h3>
        <p style={{ color: 'rgba(255,255,255,0.75)', fontSize: 14, lineHeight: 1.7 }}>
          The Funding Monitor runs a <strong style={{ color: '#6aa3ff' }}>daily automated pipeline</strong> that
          scans EU and Greek funding portals for new calls for tender, grants, and calls for proposals.
        </p>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12, margin: '16px 0' }}>
          <div style={{ background: 'rgba(255,255,255,0.08)', borderRadius: 8, padding: '12px 16px' }}>
            <div style={{ color: '#6aa3ff', fontWeight: 700, fontSize: 13, marginBottom: 4 }}>EU Direct Financing</div>
            <div style={{ fontSize: 13, color: 'rgba(255,255,255,0.65)' }}>TED (Tenders Electronic Daily), Funding & Tenders Portal (Horizon Europe, Digital Europe, EDF, LIFE, AMIF, CEF)</div>
          </div>
          <div style={{ background: 'rgba(255,255,255,0.08)', borderRadius: 8, padding: '12px 16px' }}>
            <div style={{ color: '#6aa3ff', fontWeight: 700, fontSize: 13, marginBottom: 4 }}>Greek Co-Financed (Planned)</div>
            <div style={{ fontSize: 13, color: 'rgba(255,255,255,0.65)' }}>ESPA 2021-2027, Recovery Fund (Greece 2.0), Green Fund, Just Transition Fund, Migration & Asylum Fund</div>
          </div>
        </div>
        <p style={{ color: 'rgba(255,255,255,0.75)', fontSize: 14, lineHeight: 1.7 }}>
          Each call is <strong style={{ color: '#6aa3ff' }}>automatically scored</strong> against your company profile
          across 5 dimensions: sector alignment, financial capacity, staff expertise, past experience, and geographic eligibility.
          Results are classified as <span style={{ color: '#34d399', fontWeight: 600 }}>GO</span> (bid solo),
          <span style={{ color: '#fbbf24', fontWeight: 600 }}> CONSORTIUM</span> (partner needed), or
          <span style={{ color: '#f87171', fontWeight: 600 }}> NO GO</span> (not eligible).
        </p>
      </div>

      {/* Feedback Form */}
      <div className="card" style={{ marginBottom: 24 }}>
        <h3 style={{ color: 'var(--text-h)', marginBottom: 16 }}>Submit a Request</h3>
        <p style={{ color: 'var(--text)', fontSize: 14, marginBottom: 16 }}>
          Tell us what you'd like to add, change, or improve. Your feedback shapes the next version.
        </p>
        <form onSubmit={handleSubmit}>
          <div className="form-grid" style={{ marginBottom: 16 }}>
            <div className="form-group">
              <label>Your Name</label>
              <input value={form.name} onChange={e => setForm({ ...form, name: e.target.value })} />
            </div>
            <div className="form-group">
              <label>Request Type</label>
              <select value={form.type} onChange={e => setForm({ ...form, type: e.target.value })}>
                <option value="feature">New Feature</option>
                <option value="source">New Data Source</option>
                <option value="filter">Filter / Sector Request</option>
                <option value="bug">Bug Report</option>
                <option value="other">Other</option>
              </select>
            </div>
          </div>
          <div className="form-group" style={{ marginBottom: 16 }}>
            <label>What would you like to add or change?</label>
            <textarea
              value={form.message}
              onChange={e => setForm({ ...form, message: e.target.value })}
              rows={4}
              placeholder="e.g. Add monitoring for ESPA programmes, filter by minimum budget, add email digest, track specific CPV codes..."
              style={{
                background: '#fff', border: '1px solid var(--border)', borderRadius: 'var(--radius)',
                padding: '9px 14px', color: 'var(--text-h)', fontSize: 14, width: '100%', resize: 'vertical',
                fontFamily: 'inherit',
              }}
            />
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
            <button type="submit" className="btn primary">Submit Request</button>
            {submitted && <span style={{ color: 'var(--green)', fontSize: 13, fontWeight: 500 }}>Submitted! We'll review your request.</span>}
          </div>
        </form>
      </div>

      {/* Previous Submissions */}
      {submissions.length > 0 && (
        <div className="card">
          <h3 style={{ color: 'var(--text-h)', marginBottom: 16 }}>Previous Requests ({submissions.length})</h3>
          <table>
            <thead>
              <tr>
                <th>Date</th>
                <th>From</th>
                <th>Type</th>
                <th>Request</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              {submissions.map(s => (
                <tr key={s.id}>
                  <td style={{ whiteSpace: 'nowrap', fontSize: 13 }}>{s.date}</td>
                  <td style={{ fontWeight: 500, color: 'var(--text-h)' }}>{s.name}</td>
                  <td><span className="badge open">{typeLabels[s.type] || s.type}</span></td>
                  <td style={{ fontSize: 13 }}>{s.message}</td>
                  <td>
                    <span className={`badge ${s.reviewed ? 'go' : 'closing'}`}>
                      {s.reviewed ? 'Reviewed' : 'Pending'}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

export default Feedback;
