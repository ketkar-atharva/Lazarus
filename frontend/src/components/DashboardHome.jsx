import { useState, useEffect } from 'react';
import axios from 'axios';
import {
  ShieldAlert,
  Shield,
  ShieldCheck,
  Skull,
  Ghost,
  Clock,
  Layers,
  Activity,
  BarChart3,
  AlertTriangle,
  CheckCircle2,
  ArrowRight,
  Zap,
  Target,
  Lock,
  Eye,
  Server,
  Wifi,
  TrendingUp,
  FileText,
  RefreshCw,
  ArrowUpRight,
  Sparkles,
  Brain,
} from 'lucide-react';

const API_BASE = 'http://localhost:8000';

/* Animated counter */
const AnimatedNumber = ({ value, duration = 1000 }) => {
  const [display, setDisplay] = useState(0);
  useEffect(() => {
    let start = 0;
    const end = value;
    if (end === 0) { setDisplay(0); return; }
    const step = Math.max(1, Math.floor(end / (duration / 16)));
    const timer = setInterval(() => {
      start += step;
      if (start >= end) { setDisplay(end); clearInterval(timer); }
      else setDisplay(start);
    }, 16);
    return () => clearInterval(timer);
  }, [value, duration]);
  return <span>{display.toLocaleString()}</span>;
};

export default function DashboardHome({ catalog, traffic, analysis, onViewApi, onNavigate, deployedPaths, onOpenChat }) {
  const [dbStatus, setDbStatus] = useState(null);
  const [decommissionCount, setDecommissionCount] = useState(0);
  const [activityLog, setActivityLog] = useState([]);

  useEffect(() => {
    (async () => {
      try {
        const [dbRes, logRes, decomRes] = await Promise.all([
          axios.get(`${API_BASE}/api/db-status`).catch(() => ({ data: { connected: false } })),
          axios.get(`${API_BASE}/api/activity-log`).catch(() => ({ data: [] })),
          axios.get(`${API_BASE}/api/decommission-log`).catch(() => ({ data: [] })),
        ]);
        setDbStatus(dbRes.data);
        setActivityLog(logRes.data.slice(0, 6));
        setDecommissionCount(decomRes.data.length);
      } catch (e) { console.error(e); }
    })();
  }, []);

  // Compute counts
  const catalogPaths = new Set(catalog.map(a => a.path));
  let shadowCount = 0, zombieCount = 0, staleCount = 0, activeCount = 0, honeypotCount = 0;
  catalog.forEach(api => {
    const flow = traffic.find(t => t.path === api.path);
    if (deployedPaths.has(api.path)) honeypotCount++;
    else if (api.is_deprecated && flow && flow.hit_count > 0) zombieCount++;
    else if (!flow || flow.hit_count === 0) staleCount++;
    else activeCount++;
  });
  traffic.forEach(flow => {
    if (!catalogPaths.has(flow.path)) {
      if (deployedPaths.has(flow.path)) honeypotCount++;
      else shadowCount++;
    }
  });

  const totalApis = catalog.length + shadowCount;
  const threatCount = shadowCount + zombieCount + staleCount;
  const totalTrafficHits = traffic.reduce((sum, t) => sum + (t.hit_count || 0), 0);

  return (
    <div className="dashboard-content">
      {/* Hero / Project About Section */}
      <div className="dashboard-hero">
        <div className="hero-content">
          <div className="hero-badge">
            <ShieldAlert className="w-4 h-4" />
            <span>Zombie API Discovery & Defence</span>
          </div>
          <h1 className="hero-title">Lazarus</h1>
          <p className="hero-description">
            An automated platform that continuously scans the bank's network infrastructure, API gateways,
            and deployment environments to discover <strong>undocumented</strong>, <strong>shadow</strong>,
            and <strong>zombie APIs</strong>. It classifies each API's security posture, provides
            actionable recommendations, and supports automated decommissioning workflows with
            full audit trails for <strong>RBI & PCI-DSS compliance</strong>.
          </p>
          <div className="hero-actions">
            <button className="hero-btn primary" onClick={() => onNavigate('inventory')}>
              <Eye className="w-4 h-4" /> View API Inventory
            </button>
            <button className="hero-btn secondary" onClick={() => onNavigate('monitoring')}>
              <Activity className="w-4 h-4" /> Live Monitoring
            </button>
            <button className="hero-btn secondary" onClick={() => onNavigate('reports')}>
              <FileText className="w-4 h-4" /> Compliance Reports
            </button>
          </div>
        </div>
        <div className="hero-animation">
          <div className="hero-pulse-ring ring-1" />
          <div className="hero-pulse-ring ring-2" />
          <div className="hero-pulse-ring ring-3" />
          <div className="hero-shield-icon">
            <ShieldCheck className="w-12 h-12" />
          </div>
          <div className="hero-float-dot dot-1" />
          <div className="hero-float-dot dot-2" />
          <div className="hero-float-dot dot-3" />
          <div className="hero-float-dot dot-4" />
        </div>
      </div>

      {/* Quick Stats Row */}
      <div className="stats-row">
        <div className="stat-card" onClick={() => onNavigate('inventory')}>
          <div className="stat-icon" style={{ background: '#eff6ff', borderColor: '#bfdbfe' }}>
            <Layers className="w-5 h-5" style={{ color: '#2563eb' }} />
          </div>
          <div className="stat-info">
            <span className="stat-value" style={{ color: '#2563eb' }}><AnimatedNumber value={totalApis} /></span>
            <span className="stat-label">Total APIs</span>
          </div>
        </div>
        <div className="stat-card" onClick={() => { const api = analysis?.shadow_apis?.[0]; if (api) onViewApi(null, api); }}>
          <div className="stat-icon" style={{ background: '#fef2f2', borderColor: '#fecaca' }}>
            <Ghost className="w-5 h-5" style={{ color: '#dc2626' }} />
          </div>
          <div className="stat-info">
            <span className="stat-value" style={{ color: '#dc2626' }}><AnimatedNumber value={shadowCount} /></span>
            <span className="stat-label">Shadow</span>
          </div>
        </div>
        <div className="stat-card" onClick={() => { const api = analysis?.zombie_apis?.[0]; if (api) onViewApi(null, api); }}>
          <div className="stat-icon" style={{ background: '#fffbeb', borderColor: '#fde68a' }}>
            <Skull className="w-5 h-5" style={{ color: '#d97706' }} />
          </div>
          <div className="stat-info">
            <span className="stat-value" style={{ color: '#d97706' }}><AnimatedNumber value={zombieCount} /></span>
            <span className="stat-label">Zombie</span>
          </div>
        </div>
        <div className="stat-card" onClick={() => { const api = analysis?.stale_apis?.[0]; if (api) onViewApi(null, api); }}>
          <div className="stat-icon" style={{ background: '#f5f3ff', borderColor: '#ddd6fe' }}>
            <Clock className="w-5 h-5" style={{ color: '#7c3aed' }} />
          </div>
          <div className="stat-info">
            <span className="stat-value" style={{ color: '#7c3aed' }}><AnimatedNumber value={staleCount} /></span>
            <span className="stat-label">Stale</span>
          </div>
        </div>
        <div className="stat-card">
          <div className="stat-icon" style={{ background: '#f0fdf4', borderColor: '#bbf7d0' }}>
            <ShieldCheck className="w-5 h-5" style={{ color: '#16a34a' }} />
          </div>
          <div className="stat-info">
            <span className="stat-value" style={{ color: '#16a34a' }}><AnimatedNumber value={activeCount} /></span>
            <span className="stat-label">Secure</span>
          </div>
        </div>
        <div className="stat-card">
          <div className="stat-icon" style={{ background: '#f0fdf4', borderColor: '#bbf7d0' }}>
            <Target className="w-5 h-5" style={{ color: '#16a34a' }} />
          </div>
          <div className="stat-info">
            <span className="stat-value" style={{ color: '#16a34a' }}><AnimatedNumber value={honeypotCount} /></span>
            <span className="stat-label">Honeypots</span>
          </div>
        </div>
      </div>

      {/* Two-Column Layout */}
      <div className="dashboard-grid-2col">
        {/* Left — Platform Capabilities */}
        <div className="detail-card">
          <div className="card-header">
            <div className="card-header-left">
              <Shield className="w-5 h-5 text-blue-500" />
              <h3 className="card-title">Platform Capabilities</h3>
            </div>
          </div>
          <div className="capabilities-list">
            {[
              { icon: Wifi, title: 'Continuous Network Scanning', desc: 'Scans API gateways, code repositories, and deployment environments in real-time', color: '#2563eb' },
              { icon: Eye, title: 'Shadow API Discovery', desc: 'Detects undocumented endpoints in live traffic not present in the API catalog', color: '#dc2626' },
              { icon: Skull, title: 'Zombie API Detection', desc: 'Identifies deprecated APIs still receiving production traffic — a critical risk', color: '#d97706' },
              { icon: Lock, title: 'Security Posture Assessment', desc: 'Evaluates authentication, encryption, rate limiting, data exposure & input validation', color: '#7c3aed' },
              { icon: Zap, title: 'Automated Decommissioning', desc: 'Traffic rerouting, gateway blocking, DNS removal, credential revocation — all automated', color: '#dc2626' },
              { icon: FileText, title: 'Compliance Reporting', desc: 'Post-remediation audit trails, evidence chain, and RBI/PCI-DSS compliance reports', color: '#16a34a' },
            ].map((cap, i) => {
              const Icon = cap.icon;
              return (
                <div key={i} className="capability-item">
                  <div className="capability-icon" style={{ background: cap.color + '12', borderColor: cap.color + '30' }}>
                    <Icon className="w-4 h-4" style={{ color: cap.color }} />
                  </div>
                  <div className="capability-text">
                    <span className="capability-title">{cap.title}</span>
                    <span className="capability-desc">{cap.desc}</span>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Right Column */}
        <div>
          {/* System Health */}
          <div className="detail-card">
            <div className="card-header">
              <div className="card-header-left">
                <Activity className="w-5 h-5 text-green-500" />
                <h3 className="card-title">System Health</h3>
              </div>
              <span className="report-status-pill">
                <CheckCircle2 className="w-3.5 h-3.5" /> Operational
              </span>
            </div>
            <div className="health-grid">
              <div className="health-item">
                <CheckCircle2 className="w-4 h-4 text-green-500" />
                <span className="health-label">Scanner</span>
                <span className="health-value green">Active</span>
              </div>
              <div className="health-item">
                <CheckCircle2 className="w-4 h-4 text-green-500" />
                <span className="health-label">API Gateway</span>
                <span className="health-value green">Connected</span>
              </div>
              <div className="health-item">
                {dbStatus?.connected ? (
                  <CheckCircle2 className="w-4 h-4 text-green-500" />
                ) : (
                  <AlertTriangle className="w-4 h-4 text-amber-500" />
                )}
                <span className="health-label">MongoDB</span>
                <span className={`health-value ${dbStatus?.connected ? 'green' : 'amber'}`}>
                  {dbStatus?.connected ? 'Connected' : 'Disconnected'}
                </span>
              </div>
              <div className="health-item">
                <CheckCircle2 className="w-4 h-4 text-green-500" />
                <span className="health-label">Email SMTP</span>
                <span className="health-value green">Gmail</span>
              </div>
            </div>
          </div>

          {/* Threat Overview */}
          <div className="detail-card">
            <div className="card-header">
              <div className="card-header-left">
                <AlertTriangle className="w-5 h-5 text-red-500" />
                <h3 className="card-title">Threat Overview</h3>
              </div>
              <span className="card-count">{threatCount} active</span>
            </div>
            <div className="threat-overview-body">
              <div className="threat-bar-row">
                <span className="threat-bar-label">Shadow</span>
                <div className="threat-bar-track">
                  <div className="threat-bar-fill" style={{ width: `${totalApis ? (shadowCount / totalApis) * 100 : 0}%`, background: '#dc2626' }} />
                </div>
                <span className="threat-bar-count" style={{ color: '#dc2626' }}>{shadowCount}</span>
              </div>
              <div className="threat-bar-row">
                <span className="threat-bar-label">Zombie</span>
                <div className="threat-bar-track">
                  <div className="threat-bar-fill" style={{ width: `${totalApis ? (zombieCount / totalApis) * 100 : 0}%`, background: '#d97706' }} />
                </div>
                <span className="threat-bar-count" style={{ color: '#d97706' }}>{zombieCount}</span>
              </div>
              <div className="threat-bar-row">
                <span className="threat-bar-label">Stale</span>
                <div className="threat-bar-track">
                  <div className="threat-bar-fill" style={{ width: `${totalApis ? (staleCount / totalApis) * 100 : 0}%`, background: '#7c3aed' }} />
                </div>
                <span className="threat-bar-count" style={{ color: '#7c3aed' }}>{staleCount}</span>
              </div>
              <div className="threat-bar-row">
                <span className="threat-bar-label">Remediated</span>
                <div className="threat-bar-track">
                  <div className="threat-bar-fill" style={{ width: `${totalApis ? (decommissionCount / totalApis) * 100 : 0}%`, background: '#16a34a' }} />
                </div>
                <span className="threat-bar-count" style={{ color: '#16a34a' }}>{decommissionCount}</span>
              </div>
            </div>
          </div>

          {/* AI Security Insights Widget */}
          <div className="detail-card ai-dashboard-widget">
            <div className="card-header">
              <div className="card-header-left">
                <Sparkles className="w-5 h-5 text-purple-500" />
                <h3 className="card-title">AI Security Insights</h3>
              </div>
              <span className="ai-powered-badge">
                <Sparkles className="w-3 h-3" /> AI
              </span>
            </div>
            <div className="ai-widget-body">
              <p className="ai-widget-desc">
                Get AI-powered security analysis, plain-English risk explanations, and automated compliance reports for your entire API landscape.
              </p>
              <div className="ai-widget-actions">
                <button className="ai-widget-btn primary" onClick={() => onNavigate('ai')}>
                  <Brain className="w-4 h-4" /> AI Insights
                </button>
                <button className="ai-widget-btn secondary" onClick={onOpenChat}>
                  <Sparkles className="w-4 h-4" /> Ask AI
                </button>
              </div>
            </div>
          </div>

          {/* Recent Activity */}
          <div className="detail-card">
            <div className="card-header">
              <div className="card-header-left">
                <BarChart3 className="w-5 h-5 text-blue-500" />
                <h3 className="card-title">Recent Activity</h3>
              </div>
            </div>
            <div className="activity-list">
              {activityLog.length > 0 ? activityLog.map((entry, i) => (
                <div key={i} className="activity-item">
                  <div className={`activity-dot ${entry.action === 'decommission' ? 'red' : 'blue'}`} />
                  <div className="activity-info">
                    <span className="activity-detail">{entry.detail}</span>
                    <span className="activity-time">{new Date(entry.timestamp).toLocaleString()}</span>
                  </div>
                </div>
              )) : (
                <div className="activity-empty">
                  <span>No activity yet. Decommission or deploy a honeypot to see events here.</span>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Key Metrics Bar */}
      <div className="metrics-bar">
        <div className="metrics-bar-item">
          <TrendingUp className="w-4 h-4 text-blue-500" />
          <span className="mb-value">{totalTrafficHits.toLocaleString()}</span>
          <span className="mb-label">Total API Hits</span>
        </div>
        <div className="metrics-bar-divider" />
        <div className="metrics-bar-item">
          <Server className="w-4 h-4 text-blue-500" />
          <span className="mb-value">{totalApis}</span>
          <span className="mb-label">Endpoints Monitored</span>
        </div>
        <div className="metrics-bar-divider" />
        <div className="metrics-bar-item">
          <Shield className="w-4 h-4 text-green-500" />
          <span className="mb-value">{decommissionCount}</span>
          <span className="mb-label">APIs Remediated</span>
        </div>
        <div className="metrics-bar-divider" />
        <div className="metrics-bar-item">
          <Target className="w-4 h-4 text-green-500" />
          <span className="mb-value">{honeypotCount}</span>
          <span className="mb-label">Honeypots Active</span>
        </div>
      </div>
    </div>
  );
}
