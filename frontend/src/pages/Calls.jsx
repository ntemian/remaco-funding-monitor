import { useState, useEffect } from 'react';
import { getCalls } from '../services/api';

function Calls() {
  const [calls, setCalls] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filters, setFilters] = useState({ status: '', source: '', search: '' });

  useEffect(() => { loadCalls(); }, []);

  async function loadCalls() {
    setLoading(true);
    try {
      const params = {};
      if (filters.status) params.status = filters.status;
      if (filters.source) params.source = filters.source;
      if (filters.search) params.search = filters.search;
      const res = await getCalls(params);
      setCalls(res.data);
    } catch (err) {
      console.error('Failed to load calls:', err);
    }
    setLoading(false);
  }

  function handleFilter(key, value) {
    setFilters(prev => ({ ...prev, [key]: value }));
  }

  useEffect(() => {
    const timeout = setTimeout(loadCalls, 300);
    return () => clearTimeout(timeout);
  }, [filters]);

  function formatBudget(amount) {
    if (!amount) return '—';
    if (amount >= 1_000_000) return `\u20AC${(amount / 1_000_000).toFixed(1)}M`;
    if (amount >= 1_000) return `\u20AC${(amount / 1_000).toFixed(0)}K`;
    return `\u20AC${amount.toFixed(0)}`;
  }

  function statusBadge(status) {
    const cls = status === 'open' ? 'open' : status === 'closing_soon' ? 'closing' : 'closed';
    return <span className={`badge ${cls}`}>{status.replace('_', ' ')}</span>;
  }

  return (
    <div>
      <div className="page-header">
        <h1>Funding Calls</h1>
        <span style={{ fontSize: 13, color: 'var(--text)' }}>{calls.length} results</span>
      </div>

      <div className="filters">
        <input
          placeholder="Search calls..."
          value={filters.search}
          onChange={e => handleFilter('search', e.target.value)}
        />
        <select value={filters.status} onChange={e => handleFilter('status', e.target.value)}>
          <option value="">All statuses</option>
          <option value="open">Open</option>
          <option value="closing_soon">Closing Soon</option>
          <option value="closed">Closed</option>
        </select>
        <select value={filters.source} onChange={e => handleFilter('source', e.target.value)}>
          <option value="">All sources</option>
          <option value="ted">TED</option>
          <option value="ftop">FTOP</option>
        </select>
      </div>

      <div className="card">
        {loading ? (
          <div className="loading">Loading calls...</div>
        ) : calls.length === 0 ? (
          <div className="loading">No calls found. Run the pipeline to fetch data.</div>
        ) : (
          <table>
            <thead>
              <tr>
                <th>Title</th>
                <th>Source</th>
                <th>Authority</th>
                <th>Budget</th>
                <th>Deadline</th>
                <th>Link</th>
              </tr>
            </thead>
            <tbody>
              {calls.map(call => (
                <tr key={call.id}>
                  <td style={{ maxWidth: 400 }}>
                    <div style={{ color: 'var(--text-h)', fontWeight: 500, marginBottom: 2 }}>
                      {call.title && call.title.length > 80 ? call.title.slice(0, 80) + '...' : call.title}
                    </div>
                    {call.sectors && call.sectors.length > 0 && (
                      <div style={{ fontSize: 11, color: 'var(--text)' }}>
                        {call.sectors.filter(s => s && !s.match(/^\d+$/)).slice(0, 3).join(', ')}
                      </div>
                    )}
                  </td>
                  <td><span className={`badge ${call.source === 'ted' ? 'open' : 'go'}`}>{call.source.toUpperCase()}</span></td>
                  <td style={{ fontSize: 13, maxWidth: 180 }}>
                    {call.authority_name ? (call.authority_name.length > 30 ? call.authority_name.slice(0, 30) + '...' : call.authority_name) : '—'}
                    {call.authority_country && <div style={{ fontSize: 11, color: 'var(--text)' }}>{call.authority_country}</div>}
                  </td>
                  <td style={{ whiteSpace: 'nowrap', fontWeight: 600 }}>{formatBudget(call.budget_eur)}</td>
                  <td style={{ whiteSpace: 'nowrap' }}>
                    {call.deadline || '—'}
                  </td>
                  <td>
                    {call.url ? (
                      <a href={call.url} target="_blank" rel="noopener noreferrer" className="btn" style={{ fontSize: 12, padding: '4px 10px' }}>
                        View
                      </a>
                    ) : '—'}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}

export default Calls;
