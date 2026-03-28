import { useState, useEffect } from 'react';
import { getCallStats, getMatches, getMatchStats, getProfiles, runPipeline, getPipelineStatus } from '../services/api';

function Dashboard() {
  const [stats, setStats] = useState(null);
  const [matchStats, setMatchStats] = useState({ total: 0, go: 0, consortium: 0, no_go: 0 });
  const [topMatches, setTopMatches] = useState([]);
  const [pipelineStatus, setPipelineStatus] = useState(null);
  const [running, setRunning] = useState(false);

  useEffect(() => { loadDashboard(); }, []);

  async function loadDashboard() {
    try {
      const [statsRes, statusRes, profilesRes] = await Promise.all([
        getCallStats().catch(() => ({ data: { total: 0, open: 0, closing_soon: 0, sources: {} } })),
        getPipelineStatus().catch(() => ({ data: { status: 'unknown', total_calls_in_db: 0 } })),
        getProfiles().catch(() => ({ data: [] })),
      ]);
      setStats(statsRes.data);
      setPipelineStatus(statusRes.data);

      if (profilesRes.data.length > 0) {
        const pid = profilesRes.data[0].id;
        const [matchStatsRes, matchesRes] = await Promise.all([
          getMatchStats(pid).catch(() => ({ data: { total: 0, go: 0, consortium: 0, no_go: 0 } })),
          getMatches({ profile_id: pid, per_page: 10 }).catch(() => ({ data: [] })),
        ]);
        setMatchStats(matchStatsRes.data);
        setTopMatches(matchesRes.data);
      }
    } catch (err) {
      console.error('Dashboard load failed:', err);
    }
  }

  async function handleRunPipeline() {
    setRunning(true);
    try {
      const res = await runPipeline(7);
      alert(`Pipeline complete! ${res.data.new_calls} new calls, ${res.data.matches_created} matches created.`);
      loadDashboard();
    } catch (err) {
      alert('Pipeline failed: ' + (err.response?.data?.detail || err.message));
    }
    setRunning(false);
  }

  if (!stats) return <div className="loading">Loading dashboard...</div>;

  return (
    <div>
      <div className="page-header">
        <h1>Dashboard</h1>
        <button className="btn primary" onClick={handleRunPipeline} disabled={running}>
          {running ? 'Scanning...' : 'Run Pipeline Now'}
        </button>
      </div>

      <div className="card-grid">
        <div className="card stat-card">
          <div className="value">{stats.total}</div>
          <div className="label">Total Calls</div>
        </div>
        <div className="card stat-card">
          <div className="value" style={{ color: 'var(--green)' }}>{matchStats.go}</div>
          <div className="label">Go</div>
        </div>
        <div className="card stat-card">
          <div className="value" style={{ color: 'var(--yellow)' }}>{matchStats.consortium}</div>
          <div className="label">Consortium</div>
        </div>
        <div className="card stat-card">
          <div className="value" style={{ color: 'var(--red)' }}>{matchStats.no_go}</div>
          <div className="label">No Go</div>
        </div>
      </div>

      <div className="card" style={{ marginBottom: 24 }}>
        <h3 style={{ color: 'var(--text-h)', marginBottom: 12 }}>Sources</h3>
        <div style={{ display: 'flex', gap: 24 }}>
          {Object.entries(stats.sources || {}).map(([source, count]) => (
            count > 0 && <div key={source}>
              <span style={{ color: 'var(--text-h)', fontWeight: 600 }}>{count}</span>{' '}
              <span style={{ textTransform: 'uppercase', fontSize: 11 }}>{source}</span>
            </div>
          ))}
        </div>
      </div>

      {topMatches.length > 0 && (
        <div className="card">
          <h3 style={{ color: 'var(--text-h)', marginBottom: 12 }}>Top Matches</h3>
          <table>
            <thead>
              <tr>
                <th>Call</th>
                <th>Score</th>
                <th>Verdict</th>
                <th>Deadline</th>
              </tr>
            </thead>
            <tbody>
              {topMatches.map(match => (
                <tr key={match.id}>
                  <td style={{ maxWidth: 400 }}>
                    {match.call?.url ? (
                      <a href={match.call.url} target="_blank" rel="noopener noreferrer" style={{ color: 'var(--accent)', textDecoration: 'none', fontWeight: 500 }}>
                        {(match.call?.title || `Call #${match.call_id}`).slice(0, 70)}{(match.call?.title?.length || 0) > 70 ? '...' : ''}
                      </a>
                    ) : (match.call?.title || `Call #${match.call_id}`)}
                    <div style={{ fontSize: 11, color: 'var(--text)' }}>{match.call?.source?.toUpperCase()} | {match.call?.authority_name?.slice(0, 40) || ''}</div>
                  </td>
                  <td>
                    <div className="score-bar">
                      <span style={{ fontWeight: 600 }}>{match.score}</span>
                      <div className="bar">
                        <div
                          className={`fill ${match.score >= 70 ? 'high' : match.score >= 40 ? 'medium' : 'low'}`}
                          style={{ width: `${match.score}%` }}
                        />
                      </div>
                    </div>
                  </td>
                  <td><span className={`badge ${match.verdict.replace('_', '-')}`}>{match.verdict === 'no_go' ? 'NO GO' : match.verdict.toUpperCase()}</span></td>
                  <td>{match.call?.deadline || '—'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {pipelineStatus && (
        <div style={{ marginTop: 16, fontSize: 12, color: 'var(--text)' }}>
          Pipeline: {pipelineStatus.status} | Last update: {pipelineStatus.latest_call_date || 'never'}
        </div>
      )}
    </div>
  );
}

export default Dashboard;
