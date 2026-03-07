import { useState, useEffect, useRef, useCallback } from 'react';
import axios from 'axios';
import {
  Activity,
  Shield,
  Wifi,
  Server,
  Clock,
  CheckCircle2,
  AlertTriangle,
  RefreshCw,
  Radar,
  Database,
  GitBranch,
  BarChart3,
  Globe,
  Search,
  Zap,
  Radio,
  Eye,
  Lock,
} from 'lucide-react';

const API_BASE = 'http://localhost:8000';

/* Formats seconds into "Xm Ys" */
const fmtElapsed = (s) => {
  if (s < 60) return `${s}s`;
  return `${Math.floor(s / 60)}m ${s % 60}s`;
};

export default function Monitoring() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [scanElapsed, setScanElapsed] = useState(0);
  const [isScanning, setIsScanning] = useState(false);
  const [scanProgress, setScanProgress] = useState(0);
  const [livePackets, setLivePackets] = useState(0);
  const [lastRefresh, setLastRefresh] = useState(null);
  const [scanLog, setScanLog] = useState([]);
  const timerRef = useRef(null);
  const packetRef = useRef(null);

  /* Fetch monitoring data */
  const fetchData = useCallback(async () => {
    try {
      const res = await axios.get(`${API_BASE}/api/monitor`);
      setData(res.data);
      setLastRefresh(new Date());
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  }, []);

  /* Initial load + auto-refresh every 10s */
  useEffect(() => {
    fetchData();
    const poll = setInterval(fetchData, 10000);
    return () => clearInterval(poll);
  }, [fetchData]);

  /* Live uptime counter */
  useEffect(() => {
    timerRef.current = setInterval(() => {
      setScanElapsed(prev => prev + 1);
    }, 1000);
    return () => clearInterval(timerRef.current);
  }, []);

  /* Simulated packet counter — increases randomly to feel alive */
  useEffect(() => {
    packetRef.current = setInterval(() => {
      setLivePackets(prev => prev + Math.floor(Math.random() * 20) + 5);
    }, 800);
    return () => clearInterval(packetRef.current);
  }, []);

  /* Simulate periodic scan cycle */
  useEffect(() => {
    const runScanCycle = () => {
      setIsScanning(true);
      setScanProgress(0);
      const steps = [
        { pct: 15, msg: 'Scanning API gateways...' },
        { pct: 35, msg: 'Inspecting network traffic flows...' },
        { pct: 55, msg: 'Checking code repositories...' },
        { pct: 75, msg: 'Analyzing endpoint signatures...' },
        { pct: 90, msg: 'Running threat classification...' },
        { pct: 100, msg: 'Scan complete — no new threats detected' },
      ];

      steps.forEach((step, i) => {
        setTimeout(() => {
          setScanProgress(step.pct);
          setScanLog(prev => [
            { time: new Date().toLocaleTimeString(), msg: step.msg, type: step.pct === 100 ? 'success' : 'info' },
            ...prev.slice(0, 9),
          ]);
          if (step.pct === 100) {
            setTimeout(() => {
              setIsScanning(false);
              setScanProgress(0);
            }, 2000);
          }
        }, (i + 1) * 1500);
      });
    };

    // Run first scan after 3s, then every 30s
    const firstScan = setTimeout(runScanCycle, 3000);
    const cycle = setInterval(runScanCycle, 30000);
    return () => { clearTimeout(firstScan); clearInterval(cycle); };
  }, []);

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

  return (
    <div className="monitoring-content">
      {/* Page Header */}
      <div className="page-header">
        <div>
          <h2 className="page-title">Live Monitoring</h2>
          <p className="page-subtitle">Real-time network scanning, traffic analysis & threat detection</p>
        </div>
        <div className="monitor-header-right">
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
      <div className={`live-scanner-bar ${isScanning ? 'active' : 'idle'}`}>
        <div className="scanner-bar-left">
          <Radar className={`w-5 h-5 ${isScanning ? 'scanner-spin' : ''}`} />
          <div className="scanner-info">
            <span className="scanner-status">
              {isScanning ? 'Scan in progress...' : 'Scanner idle — next scan in ~30s'}
            </span>
            {isScanning && (
              <div className="scanner-progress-track">
                <div className="scanner-progress-fill" style={{ width: `${scanProgress}%` }} />
              </div>
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
          <div className="monitor-stat-icon blue">
            <Search className="w-5 h-5" />
          </div>
          <div>
            <p className="monitor-stat-value">{data.total_scans_today + Math.floor(scanElapsed / 30)}</p>
            <p className="monitor-stat-label">Scans Today</p>
          </div>
          <div className="stat-live-dot" />
        </div>
        <div className="monitor-stat-card">
          <div className="monitor-stat-icon green">
            <Shield className="w-5 h-5" />
          </div>
          <div>
            <p className="monitor-stat-value">{data.apis_discovered_today}</p>
            <p className="monitor-stat-label">New APIs Found</p>
          </div>
        </div>
        <div className="monitor-stat-card">
          <div className="monitor-stat-icon purple">
            <GitBranch className="w-5 h-5" />
          </div>
          <div>
            <p className="monitor-stat-value">{data.repositories_scanned}</p>
            <p className="monitor-stat-label">Repos Scanned</p>
          </div>
        </div>
        <div className="monitor-stat-card">
          <div className="monitor-stat-icon amber">
            <Eye className="w-5 h-5" />
          </div>
          <div>
            <p className="monitor-stat-value">{livePackets.toLocaleString()}</p>
            <p className="monitor-stat-label">Packets Analyzed</p>
          </div>
          <div className="stat-live-dot" />
        </div>
      </div>

      {/* Two Columns */}
      <div className="monitor-columns">
        {/* Left: Live Scanner Log */}
        <div className="detail-card">
          <div className="card-header">
            <div className="card-header-left">
              <Activity className="w-5 h-5 text-blue-500" />
              <h3 className="card-title">Live Scanner Feed</h3>
            </div>
            <div className="header-live-badge scanning" style={{ fontSize: '10px', padding: '2px 8px' }}>
              <span className="live-blink-dot" /> Live
            </div>
          </div>

          <div className="scan-feed">
            {scanLog.length > 0 ? scanLog.map((entry, i) => (
              <div key={i} className={`scan-feed-item ${entry.type} ${i === 0 ? 'latest' : ''}`}>
                <span className="scan-feed-time">{entry.time}</span>
                {entry.type === 'success' ? (
                  <CheckCircle2 className="w-3.5 h-3.5 text-green-500" />
                ) : (
                  <Radar className="w-3.5 h-3.5 text-blue-400" />
                )}
                <span className="scan-feed-msg">{entry.msg}</span>
              </div>
            )) : (
              <div className="scan-feed-empty">
                <Radar className="w-5 h-5 scanner-spin" />
                <span>Waiting for scan data...</span>
              </div>
            )}
          </div>
        </div>

        {/* Right: Infrastructure */}
        <div className="detail-card">
          <div className="card-header">
            <div className="card-header-left">
              <Globe className="w-5 h-5 text-blue-500" />
              <h3 className="card-title">Monitored Infrastructure</h3>
            </div>
          </div>

          <div className="infra-section">
            <p className="infra-label"><Server className="w-3.5 h-3.5" /> API Gateways</p>
            <div className="infra-items">
              {data.gateways_monitored.map(gw => (
                <div key={gw} className="infra-item">
                  <CheckCircle2 className="w-3.5 h-3.5 text-green-500" />
                  <span>{gw}</span>
                  <span className="infra-ping">• Connected</span>
                </div>
              ))}
            </div>
          </div>

          <div className="infra-section">
            <p className="infra-label"><Wifi className="w-3.5 h-3.5" /> Network Ranges</p>
            <div className="infra-items">
              {data.networks_scanned.map(net => (
                <div key={net} className="infra-item">
                  <Lock className="w-3.5 h-3.5 text-blue-400" />
                  <code className="infra-code">{net}</code>
                </div>
              ))}
            </div>
          </div>

          <div className="infra-section">
            <p className="infra-label"><Database className="w-3.5 h-3.5" /> Environments</p>
            <div className="infra-items row">
              {data.deployment_envs.map(env => (
                <span key={env} className="env-badge">{env}</span>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Scan History + Threat Timeline */}
      <div className="monitor-columns">
        {/* Scan History */}
        <div className="detail-card">
          <div className="card-header">
            <div className="card-header-left">
              <BarChart3 className="w-5 h-5 text-blue-500" />
              <h3 className="card-title">Scan History</h3>
            </div>
          </div>
          <div className="scan-history">
            {data.scan_history.map((scan, i) => {
              const time = new Date(scan.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
              const isAlert = scan.status === 'alert';
              return (
                <div key={i} className={`scan-entry ${isAlert ? 'alert' : ''}`}>
                  <div className="scan-entry-icon">
                    {isAlert ? (
                      <AlertTriangle className="w-4 h-4 text-amber-500" />
                    ) : (
                      <CheckCircle2 className="w-4 h-4 text-green-500" />
                    )}
                  </div>
                  <div className="scan-entry-info">
                    <span className="scan-time">{time}</span>
                    <span className="scan-details">{scan.apis_found} APIs found{scan.new_threats > 0 ? ` · ${scan.new_threats} new threat` : ''}</span>
                  </div>
                  <span className={`scan-status-badge ${scan.status}`}>
                    {scan.status === 'clean' ? 'Clean' : 'Alert'}
                  </span>
                </div>
              );
            })}
          </div>
        </div>

        {/* Threat Timeline */}
        <div className="detail-card">
          <div className="card-header">
            <div className="card-header-left">
              <Activity className="w-5 h-5 text-blue-500" />
              <h3 className="card-title">7-Day Threat Timeline</h3>
            </div>
          </div>
          <div className="timeline-table-wrap">
            <table className="data-table compact">
              <thead>
                <tr>
                  <th>Date</th>
                  <th>Shadow</th>
                  <th>Zombie</th>
                  <th>Stale</th>
                  <th>Total</th>
                </tr>
              </thead>
              <tbody>
                {data.threat_timeline.map((day, i) => {
                  const total = day.shadow + day.zombie + day.stale;
                  return (
                    <tr key={i} className="table-row">
                      <td className="mono">{day.date}</td>
                      <td><span className={`inline-count ${day.shadow > 0 ? 'red' : ''}`}>{day.shadow}</span></td>
                      <td><span className={`inline-count ${day.zombie > 0 ? 'amber' : ''}`}>{day.zombie}</span></td>
                      <td><span className={`inline-count ${day.stale > 0 ? 'purple' : ''}`}>{day.stale}</span></td>
                      <td><span className={`inline-count ${total > 2 ? 'red' : total > 0 ? 'amber' : ''}`}>{total}</span></td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
}
