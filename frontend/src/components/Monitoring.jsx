import { useState, useEffect, useRef, useCallback } from 'react';
import api from '../api';
import {
  Activity,
  Shield,
  Wifi,
  WifiOff,
  Server,
  Clock,
  CheckCircle2,
  AlertTriangle,
  RefreshCw,
  Radar,
  BarChart3,
  Search,
  Zap,
  Radio,
  Eye,
  Skull,
  Ghost,
  ShieldAlert,
  Loader2,
  Play,
} from 'lucide-react';

/* Formats seconds into "Xm Ys" */
const fmtElapsed = (s) => {
  if (s < 60) return `${s}s`;
  return `${Math.floor(s / 60)}m ${s % 60}s`;
};

const SEV_ORDER = { CRITICAL: 0, HIGH: 1, MEDIUM: 2, LOW: 3 };
const SEV_STYLE = {
  CRITICAL: { bg: '#fef2f2', color: '#dc2626', border: '#fecaca' },
  HIGH:     { bg: '#fff7ed', color: '#ea580c', border: '#fed7aa' },
  MEDIUM:   { bg: '#fffbeb', color: '#d97706', border: '#fde68a' },
  LOW:      { bg: '#f0fdf4', color: '#16a34a', border: '#bbf7d0' },
};

const STATUS_ICON = {
  ZOMBIE: Skull,
  SHADOW: Ghost,
  STALE:  Clock,
  ACTIVE: CheckCircle2,
};

export default function Monitoring() {
  const [data, setData] = useState(null);
  const [events, setEvents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [scanElapsed, setScanElapsed] = useState(0);
  const [scanning, setScanning] = useState(false);
  const [livePackets, setLivePackets] = useState(0);
  const [lastRefresh, setLastRefresh] = useState(null);
  const timerRef = useRef(null);
  const packetRef = useRef(null);

  /* Fetch monitoring data */
  const fetchData = useCallback(async () => {
    try {
      const [monRes, evRes] = await Promise.all([
        api.get('/api/monitor'),
        api.get('/api/security-events'),
      ]);
      setData(monRes.data);
      setEvents(evRes.data || []);
      setLastRefresh(new Date());
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  }, []);

  /* Initial load + auto-refresh every 15s */
  useEffect(() => {
    fetchData();
    const poll = setInterval(fetchData, 15000);
    return () => clearInterval(poll);
  }, [fetchData]);

  /* Live uptime counter */
  useEffect(() => {
    timerRef.current = setInterval(() => setScanElapsed(p => p + 1), 1000);
    return () => clearInterval(timerRef.current);
  }, []);

  /* Simulated packet counter */
  useEffect(() => {
    packetRef.current = setInterval(() => {
      setLivePackets(p => p + Math.floor(Math.random() * 20) + 5);
    }, 800);
    return () => clearInterval(packetRef.current);
  }, []);

  /* Manual scan trigger */
  const handleScanNow = async () => {
    setScanning(true);
    try {
      const res = await api.post('/api/monitor/scan-now');
      setData(res.data);
      // Refresh events too
      const evRes = await api.get('/api/security-events');
      setEvents(evRes.data || []);
      setLastRefresh(new Date());
    } catch (err) {
      console.error('Scan failed:', err);
    } finally {
      setScanning(false);
    }
  };

  if (loading) {
    return (
      <div className="detail-loading">
        <RefreshCw className="w-6 h-6 animate-spin text-blue-500" />
        <p>Connecting to scanner...</p>
      </div>
    );
  }

  if (!data) {
    return (
      <div className="detail-error">
        <AlertTriangle className="w-8 h-8 text-red-400" />
        <p>Unable to connect to monitoring service.</p>
      </div>
    );
  }

  const results = data.scan_results || [];

  return (
    <div className="monitoring-content">
      {/* Page Header */}
      <div className="page-header">
        <div>
          <h2 className="page-title">Live Monitoring</h2>
          <p className="page-subtitle">Real-time network scanning, traffic analysis & threat detection</p>
        </div>
        <div className="monitor-header-right">
          <button
            className="hero-btn primary"
            onClick={handleScanNow}
            disabled={scanning}
            style={{ display: 'inline-flex', alignItems: 'center', gap: 6, fontSize: '0.8rem' }}
          >
            {scanning ? (
              <><Loader2 className="w-4 h-4 animate-spin" /> Scanning...</>
            ) : (
              <><Play className="w-4 h-4" /> Scan Now</>
            )}
          </button>
          <div className="header-live-badge scanning">
            <Radio className="w-3.5 h-3.5 live-blink" />
            <span>LIVE</span>
          </div>
          {lastRefresh && (
            <span className="monitor-last-refresh">
              Updated {lastRefresh.toLocaleTimeString()}
            </span>
          )}
        </div>
      </div>

      {/* Live Scanner Bar */}
      <div className={`live-scanner-bar ${scanning ? 'active' : 'idle'}`}>
        <div className="scanner-bar-left">
          <Radar className={`w-5 h-5 ${scanning ? 'scanner-spin' : ''}`} />
          <div className="scanner-info">
            <span className="scanner-status">
              {scanning
                ? 'Full re-probe in progress...'
                : data.last_scan
                  ? `Last scan: ${new Date(data.last_scan).toLocaleString()}`
                  : 'No scans yet — click Scan Now'}
            </span>
            {data.next_scan && !scanning && (
              <span style={{ fontSize: '0.72rem', color: '#64748b' }}>
                Next scheduled: {new Date(data.next_scan).toLocaleString()}
              </span>
            )}
          </div>
        </div>
        <div className="scanner-bar-right">
          <span className="scanner-uptime">
            <Clock className="w-3.5 h-3.5" /> Uptime: {fmtElapsed(scanElapsed)}
          </span>
          <span className="scanner-packets">
            <Zap className="w-3.5 h-3.5" /> {livePackets.toLocaleString()} packets
          </span>
        </div>
      </div>

      {/* Live Stats */}
      <div className="monitor-stats-grid">
        <div className="monitor-stat-card">
          <div className="monitor-stat-icon blue"><Search className="w-5 h-5" /></div>
          <div>
            <p className="monitor-stat-value">{data.total_apis || 0}</p>
            <p className="monitor-stat-label">Total APIs</p>
          </div>
          <div className="stat-live-dot" />
        </div>
        <div className="monitor-stat-card">
          <div className="monitor-stat-icon amber"><Skull className="w-5 h-5" /></div>
          <div>
            <p className="monitor-stat-value">{data.zombie_count || 0}</p>
            <p className="monitor-stat-label">Zombie</p>
          </div>
        </div>
        <div className="monitor-stat-card">
          <div className="monitor-stat-icon red"><Ghost className="w-5 h-5" /></div>
          <div>
            <p className="monitor-stat-value">{data.shadow_count || 0}</p>
            <p className="monitor-stat-label">Shadow</p>
          </div>
        </div>
        <div className="monitor-stat-card">
          <div className="monitor-stat-icon purple"><Clock className="w-5 h-5" /></div>
          <div>
            <p className="monitor-stat-value">{data.stale_count || 0}</p>
            <p className="monitor-stat-label">Stale</p>
          </div>
        </div>
        <div className="monitor-stat-card">
          <div className="monitor-stat-icon green"><Shield className="w-5 h-5" /></div>
          <div>
            <p className="monitor-stat-value">{data.active_count || 0}</p>
            <p className="monitor-stat-label">Active</p>
          </div>
        </div>
        <div className="monitor-stat-card">
          <div className="monitor-stat-icon amber"><Eye className="w-5 h-5" /></div>
          <div>
            <p className="monitor-stat-value">{livePackets.toLocaleString()}</p>
            <p className="monitor-stat-label">Packets Analyzed</p>
          </div>
          <div className="stat-live-dot" />
        </div>
      </div>

      {/* Two Columns */}
      <div className="monitor-columns">
        {/* Left: Scan Results Table */}
        <div className="detail-card">
          <div className="card-header">
            <div className="card-header-left">
              <BarChart3 className="w-5 h-5 text-blue-500" />
              <h3 className="card-title">Scan Results</h3>
            </div>
            <span className="card-count">{results.length} endpoints</span>
          </div>
          <div className="timeline-table-wrap">
            <table className="data-table compact">
              <thead>
                <tr>
                  <th>Status</th>
                  <th>API ID</th>
                  <th>URL</th>
                  <th>HTTP</th>
                  <th>Latency</th>
                  <th>Auth</th>
                  <th>Reach</th>
                </tr>
              </thead>
              <tbody>
                {results.length > 0 ? results.map((r, i) => {
                  const ls = (r.lazarus_status || 'ACTIVE').toUpperCase();
                  const StatusIcon = STATUS_ICON[ls] || CheckCircle2;
                  const sev = SEV_STYLE[ls === 'ZOMBIE' ? 'CRITICAL' : ls === 'SHADOW' ? 'HIGH' : ls === 'STALE' ? 'MEDIUM' : 'LOW'];
                  return (
                    <tr key={i} className="table-row">
                      <td>
                        <span style={{
                          display: 'inline-flex', alignItems: 'center', gap: 4,
                          fontSize: '0.7rem', fontWeight: 700, padding: '2px 8px',
                          borderRadius: 20, background: sev.bg, color: sev.color,
                          border: `1px solid ${sev.border}`,
                        }}>
                          <StatusIcon style={{ width: 11, height: 11 }} />
                          {ls}
                        </span>
                      </td>
                      <td><code style={{ fontSize: '0.75rem', color: '#64748b' }}>{r.api_id}</code></td>
                      <td style={{ maxWidth: 200, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', fontSize: '0.78rem' }}>
                        {r.url || '—'}
                      </td>
                      <td>
                        <span style={{
                          fontSize: '0.75rem', fontWeight: 600,
                          color: r.http_code && r.http_code < 400 ? '#16a34a' : r.http_code >= 500 ? '#dc2626' : '#d97706',
                        }}>
                          {r.http_code || '—'}
                        </span>
                      </td>
                      <td style={{ fontSize: '0.75rem', color: '#64748b' }}>
                        {r.response_time_ms != null ? `${r.response_time_ms}ms` : '—'}
                      </td>
                      <td>
                        {r.auth_exposed
                          ? <ShieldAlert style={{ width: 14, height: 14, color: '#dc2626' }} />
                          : <Shield style={{ width: 14, height: 14, color: '#16a34a' }} />
                        }
                      </td>
                      <td>
                        {r.reachable
                          ? <Wifi style={{ width: 14, height: 14, color: '#16a34a' }} />
                          : <WifiOff style={{ width: 14, height: 14, color: '#dc2626' }} />
                        }
                      </td>
                    </tr>
                  );
                }) : (
                  <tr>
                    <td colSpan={7} style={{ textAlign: 'center', padding: 32, color: '#94a3b8' }}>
                      No scan results yet. Click "Scan Now" to start.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>

        {/* Right: Security Events */}
        <div className="detail-card">
          <div className="card-header">
            <div className="card-header-left">
              <Activity className="w-5 h-5 text-red-500" />
              <h3 className="card-title">Security Events</h3>
            </div>
            <span className="card-count">{events.length} total</span>
          </div>
          <div className="scan-feed" style={{ maxHeight: 450 }}>
            {events.length > 0 ? events.map((ev, i) => {
              const sev = SEV_STYLE[ev.severity] || SEV_STYLE.MEDIUM;
              return (
                <div key={i} className="scan-feed-item info" style={{ borderLeft: `3px solid ${sev.color}` }}>
                  <span style={{
                    fontSize: '0.68rem', fontWeight: 700, padding: '1px 7px',
                    borderRadius: 12, background: sev.bg, color: sev.color,
                    border: `1px solid ${sev.border}`, whiteSpace: 'nowrap',
                  }}>
                    {ev.severity}
                  </span>
                  <div style={{ flex: 1, minWidth: 0 }}>
                    <span className="scan-feed-msg" style={{ fontWeight: 600 }}>
                      {ev.anomaly_type?.replace(/_/g, ' ')}
                    </span>
                    <span style={{ fontSize: '0.72rem', color: '#64748b', display: 'block' }}>
                      {ev.api_id} — {String(ev.old_value)} → {String(ev.new_value)}
                    </span>
                  </div>
                  <span className="scan-feed-time">
                    {ev.detected_at ? new Date(ev.detected_at).toLocaleString() : '—'}
                  </span>
                </div>
              );
            }) : (
              <div className="scan-feed-empty">
                <CheckCircle2 className="w-5 h-5 text-green-500" />
                <span>No security anomalies detected yet.</span>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
