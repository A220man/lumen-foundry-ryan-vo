import { useEffect, useState } from 'react';
import { apiClient } from '../api/client';

interface Stats {
  total_requests: number;
  total_tokens_generated: number;
  avg_latency_ms: number;
  uptime_seconds: number;
}

function Dashboard() {
  const [stats, setStats] = useState<Stats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function fetchStats() {
      try {
        const response = await apiClient.getGlobalStats();
        setStats(response.data);
      } catch (err) {
        setError('Failed to load statistics');
        console.error(err);
      } finally {
        setLoading(false);
      }
    }

    fetchStats();
    const interval = setInterval(fetchStats, 10000);
    return () => clearInterval(interval);
  }, []);

  if (loading) return <div className="loading">Loading dashboard...</div>;
  if (error) return <div className="error">{error}</div>;
  if (!stats) return <div className="error">No data available</div>;

  const formatUptime = (seconds: number) => {
    const h = Math.floor(seconds / 3600);
    const m = Math.floor((seconds % 3600) / 60);
    const s = Math.floor(seconds % 60);
    return `${h}h ${m}m ${s}s`;
  };

  return (
    <div className="dashboard">
      <h1 className="page-title">Dashboard</h1>
      <p className="page-subtitle">Real-time inference engine monitoring</p>

      <div className="stats-grid">
        <div className="stat-card">
          <div className="stat-icon">📈</div>
          <div className="stat-content">
            <div className="stat-value">{stats.total_requests.toLocaleString()}</div>
            <div className="stat-label">Total Requests</div>
          </div>
        </div>
        <div className="stat-card">
          <div className="stat-icon">🔤</div>
          <div className="stat-content">
            <div className="stat-value">{stats.total_tokens_generated.toLocaleString()}</div>
            <div className="stat-label">Tokens Generated</div>
          </div>
        </div>
        <div className="stat-card">
          <div className="stat-icon">⚡</div>
          <div className="stat-content">
            <div className="stat-value">{stats.avg_latency_ms.toFixed(1)} ms</div>
            <div className="stat-label">Avg Latency</div>
          </div>
        </div>
        <div className="stat-card">
          <div className="stat-icon">🕐</div>
          <div className="stat-content">
            <div className="stat-value">{formatUptime(stats.uptime_seconds)}</div>
            <div className="stat-label">Uptime</div>
          </div>
        </div>
      </div>

      <div className="dashboard-section">
        <h2>Quick Actions</h2>
        <div className="action-buttons">
          <a href="/models" className="btn btn-primary">
            <span>🤖</span> Manage Models
          </a>
          <a href="/inference" className="btn btn-secondary">
            <span>⚡</span> Run Inference
          </a>
        </div>
      </div>

      <div className="dashboard-section">
        <h2>System Status</h2>
        <div className="status-grid">
          <div className="status-item">
            <span className="status-indicator healthy"></span>
            <span>API Server</span>
          </div>
          <div className="status-item">
            <span className="status-indicator healthy"></span>
            <span>Database</span>
          </div>
          <div className="status-item">
            <span className="status-indicator healthy"></span>
            <span>Inference Engine</span>
          </div>
          <div className="status-item">
            <span className="status-indicator warning"></span>
            <span>GPU Monitoring (Demo)</span>
          </div>
        </div>
      </div>
    </div>
  );
}

export default Dashboard;
