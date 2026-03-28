import { useState, useEffect } from 'react';
import { getMatches, getProfiles, bookmarkMatch, dismissMatch } from '../services/api';

function Matches() {
  const [matches, setMatches] = useState([]);
  const [profiles, setProfiles] = useState([]);
  const [profileId, setProfileId] = useState(null);
  const [loading, setLoading] = useState(true);
  const [verdictFilter, setVerdictFilter] = useState('');
  const [minScore, setMinScore] = useState(0);

  useEffect(() => {
    getProfiles().then(res => {
      setProfiles(res.data);
      if (res.data.length > 0) {
        setProfileId(res.data[0].id);
      } else {
        setLoading(false);
      }
    }).catch(() => setLoading(false));
  }, []);

  useEffect(() => {
    if (profileId) loadMatches();
  }, [profileId, verdictFilter, minScore]);

  async function loadMatches() {
    setLoading(true);
    try {
      const params = { profile_id: profileId, min_score: minScore, per_page: 100 };
      if (verdictFilter) params.verdict = verdictFilter;
      const res = await getMatches(params);
      setMatches(res.data);
    } catch (err) {
      console.error('Failed to load matches:', err);
    }
    setLoading(false);
  }

  async function handleBookmark(id) {
    await bookmarkMatch(id);
    loadMatches();
  }

  async function handleDismiss(id) {
    await dismissMatch(id);
    loadMatches();
  }

  function verdictBadge(verdict) {
    const cls = verdict === 'go' ? 'go' : verdict === 'consortium' ? 'consortium' : 'no-go';
    const label = verdict === 'go' ? 'GO' : verdict === 'consortium' ? 'CONSORTIUM' : 'NO GO';
    return <span className={`badge ${cls}`}>{label}</span>;
  }

  return (
    <div>
      <div className="page-header">
        <h1>Eligibility Matches</h1>
        <span style={{ fontSize: 13, color: 'var(--text)' }}>{matches.length} results</span>
      </div>

      <div className="filters">
        {profiles.length > 1 && (
          <select value={profileId || ''} onChange={e => setProfileId(Number(e.target.value))}>
            {profiles.map(p => <option key={p.id} value={p.id}>{p.name}</option>)}
          </select>
        )}
        <select value={verdictFilter} onChange={e => setVerdictFilter(e.target.value)}>
          <option value="">All verdicts</option>
          <option value="go">Go</option>
          <option value="consortium">Consortium</option>
          <option value="no_go">No Go</option>
        </select>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <label style={{ margin: 0, whiteSpace: 'nowrap' }}>Min score:</label>
          <input
            type="range" min="0" max="100" value={minScore}
            onChange={e => setMinScore(Number(e.target.value))}
            style={{ width: 120 }}
          />
          <span style={{ fontSize: 13, minWidth: 30 }}>{minScore}</span>
        </div>
      </div>

      <div className="card">
        {loading ? (
          <div className="loading">Loading matches...</div>
        ) : !profileId ? (
          <div className="loading">Create a company profile first to see matches.</div>
        ) : matches.length === 0 ? (
          <div className="loading">No matches found. Adjust filters or run the pipeline.</div>
        ) : (
          <table>
            <thead>
              <tr>
                <th>Call</th>
                <th>Score</th>
                <th>Verdict</th>
                <th style={{ textAlign: 'center' }}>Sector</th>
                <th style={{ textAlign: 'center' }}>Financial</th>
                <th style={{ textAlign: 'center' }}>Geo</th>
                <th>Gaps</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {matches.map(match => (
                <tr key={match.id}>
                  <td style={{ maxWidth: 300 }}>
                    {match.call?.url ? (
                      <a href={match.call.url} target="_blank" rel="noopener noreferrer" style={{ color: 'var(--accent)', fontWeight: 500, textDecoration: 'none' }}>
                        {(match.call?.title || `Call #${match.call_id}`).slice(0, 65)}{(match.call?.title?.length || 0) > 65 ? '...' : ''}
                      </a>
                    ) : (
                      <span style={{ color: 'var(--text-h)', fontWeight: 500 }}>
                        {(match.call?.title || `Call #${match.call_id}`).slice(0, 65)}
                      </span>
                    )}
                    <div style={{ fontSize: 11, color: 'var(--text)', marginTop: 2 }}>
                      {match.call?.source?.toUpperCase()} {match.call?.deadline ? `| Deadline: ${match.call.deadline}` : ''}
                    </div>
                  </td>
                  <td>
                    <div className="score-bar">
                      <span style={{ fontWeight: 700, color: 'var(--text-h)', minWidth: 24 }}>{match.score}</span>
                      <div className="bar">
                        <div
                          className={`fill ${match.score >= 70 ? 'high' : match.score >= 40 ? 'medium' : 'low'}`}
                          style={{ width: `${match.score}%` }}
                        />
                      </div>
                    </div>
                  </td>
                  <td>{verdictBadge(match.verdict)}</td>
                  <td style={{ textAlign: 'center', fontWeight: 600, color: (match.sector_score ?? 0) >= 60 ? 'var(--green)' : (match.sector_score ?? 0) >= 40 ? 'var(--yellow)' : 'var(--red)' }}>{match.sector_score ?? '—'}</td>
                  <td style={{ textAlign: 'center', fontWeight: 600, color: (match.financial_score ?? 0) >= 60 ? 'var(--green)' : (match.financial_score ?? 0) >= 40 ? 'var(--yellow)' : 'var(--red)' }}>{match.financial_score ?? '—'}</td>
                  <td style={{ textAlign: 'center', fontWeight: 600, color: (match.geographic_score ?? 0) >= 60 ? 'var(--green)' : 'var(--red)' }}>{match.geographic_score ?? '—'}</td>
                  <td style={{ maxWidth: 250 }}>
                    {match.gaps && match.gaps.length > 0 ? (
                      <ul className="gaps">
                        {match.gaps.slice(0, 2).map((gap, i) => (
                          <li key={i} className={`severity-${gap.severity}`}>
                            {gap.message.length > 80 ? gap.message.slice(0, 80) + '...' : gap.message}
                          </li>
                        ))}
                      </ul>
                    ) : <span style={{ color: 'var(--green)', fontSize: 12 }}>No gaps</span>}
                  </td>
                  <td>
                    <div style={{ display: 'flex', gap: 4 }}>
                      {match.call?.url && (
                        <a href={match.call.url} target="_blank" rel="noopener noreferrer" className="btn" style={{ fontSize: 11, padding: '3px 8px', textDecoration: 'none' }}>
                          Open
                        </a>
                      )}
                      <button className="btn" onClick={() => handleBookmark(match.id)} style={{ fontSize: 11, padding: '3px 8px' }}>
                        {match.bookmarked ? 'Saved' : 'Save'}
                      </button>
                    </div>
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

export default Matches;
