import { useState, useEffect } from 'react';
import {
  ShieldAlert,
  Skull,
  Ghost,
  Eye,
  Zap,
  AlertTriangle,
  CheckCircle2,
  Lock,
  TrendingUp,
  ArrowRight,
  Layers,
  Clock,
  Wifi,
  Target,
  FileWarning,
  ArrowUpRight,
  Shield,
  Activity,
  X,
} from 'lucide-react';

/* ── Animated Counter ── */
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

/* ── Status Badge ── */
const StatusBadge = ({ status }) => {
  const conf = {
    ACTIVE:   { cls: 'status-badge active',   label: 'Active'   },
    SAFE:     { cls: 'status-badge active',   label: 'Verified' },
    SHADOW:   { cls: 'status-badge shadow',   label: 'Shadow'   },
    ZOMBIE:   { cls: 'status-badge zombie',   label: 'Zombie'   },
    STALE:    { cls: 'status-badge stale',    label: 'Stale'    },
    HONEYPOT: { cls: 'status-badge honeypot', label: 'Honeypot' },
  };
  const c = conf[status] || conf.ACTIVE;
  return <span className={c.cls}>{c.label}</span>;
};

/* ── Risk Badge ── */
const RiskBadge = ({ level }) => {
  const cls = {
    CRITICAL: 'risk-badge critical',
    HIGH:     'risk-badge high',
    MEDIUM:   'risk-badge medium',
    LOW:      'risk-badge low',
  };
  return <span className={cls[level] || cls.LOW}>{level}</span>;
};

/* ── Metric Card ── */
const MetricCard = ({ icon: Icon, label, value, color, subtitle, trend, onClick, isActive }) => {
  const palette = {
    blue:   { text: '#2563eb', bg: '#eff6ff', border: '#bfdbfe' },
    red:    { text: '#dc2626', bg: '#fef2f2', border: '#fecaca' },
    amber:  { text: '#d97706', bg: '#fffbeb', border: '#fde68a' },
    green:  { text: '#16a34a', bg: '#f0fdf4', border: '#bbf7d0' },
    purple: { text: '#7c3aed', bg: '#f5f3ff', border: '#ddd6fe' },
  };
  const p = palette[color] || palette.blue;

  return (
    <div
      className={`metric-card ${onClick ? 'clickable' : ''} ${isActive ? 'metric-card-active' : ''}`}
      onClick={onClick}
      role={onClick ? 'button' : undefined}
      style={isActive ? { boxShadow: `0 0 0 2px ${p.text}`, borderColor: p.text } : undefined}
    >
      <div className="metric-card-header">
        <div className="metric-card-icon" style={{ background: p.bg, border: `1px solid ${p.border}` }}>
          <Icon className="w-5 h-5" style={{ color: p.text }} />
        </div>
        {trend && (
          <span className="metric-trend" style={{ color: p.text }}>
            <ArrowUpRight className="w-3.5 h-3.5" />
            {trend}
          </span>
        )}
      </div>
      <p className="metric-label">{label}</p>
      <p className="metric-value" style={{ color: p.text }}>
        <AnimatedNumber value={value} />
      </p>
      {subtitle && <p className="metric-subtitle">{subtitle}</p>}
      {onClick && <p className="metric-cta">{isActive ? 'Showing filtered ↓' : 'Click to filter ↓'}</p>}
    </div>
  );
};

function resolveStatus(api, flow) {
  // CSV-ingested APIs have lazarus_status
  const ls = api.lazarus_status?.toLowerCase();
  if (ls) {
    if (ls === 'zombie') return 'ZOMBIE';
    if (ls === 'shadow') return 'SHADOW';
    if (ls === 'stale')  return 'STALE';
    return 'ACTIVE';
  }
  // Mock-data fallback
  if (api.is_deprecated && flow && flow.hit_count > 0) return 'ZOMBIE';
  if (!flow || flow.hit_count === 0) return 'STALE';
  return 'ACTIVE';
}

function getPath(api) {
  if (api.path) return api.path;
  if (!api.url) return '';
  try { return new URL(api.url).pathname; } catch (e) { return api.url; }
}

export default function Dashboard({ catalog, traffic, analysis, onViewApi }) {
  const [filterStatus, setFilterStatus] = useState(null); // null = show all

  const catalogPaths = new Set(catalog.map(getPath));

  /* Build unified API list respecting both mock and CSV formats */
  const allApis = [];
  catalog.forEach(api => {
    const apiPath = getPath(api);
    const flow = traffic.find(t => t.path === apiPath);
    const status = resolveStatus(api, flow);
    allApis.push({
      id: api.id || api.api_id,
      path: apiPath,
      name: api.name || apiPath,
      method: flow?.method || api.method,
      status,
      hitCount: flow?.hit_count ?? api.traffic_30d ?? 0,
      avgLatency: flow?.avg_latency ?? '—',
      owner: api.owner || '—',
      riskLevel: (status === 'ZOMBIE' || status === 'SHADOW') ? 'CRITICAL' : status === 'STALE' ? 'MEDIUM' : 'LOW',
    });
  });

  // Shadow APIs from live traffic not in catalog
  traffic.forEach(flow => {
    if (!catalogPaths.has(flow.path)) {
      allApis.push({
        id: 'SHADOW-' + flow.path.replace(/\//g, '-'),
        path: flow.path,
        name: 'Undocumented Endpoint',
        method: flow.method,
        status: 'SHADOW',
        hitCount: flow.hit_count,
        avgLatency: flow.avg_latency,
        owner: 'Unknown',
        riskLevel: 'CRITICAL',
      });
    }
  });

  const shadow    = allApis.filter(a => a.status === 'SHADOW').length;
  const zombie    = allApis.filter(a => a.status === 'ZOMBIE').length;
  const stale     = allApis.filter(a => a.status === 'STALE').length;
  const active    = allApis.filter(a => a.status === 'ACTIVE').length;
  /* Filtered view for the table */
  const displayedApis = filterStatus
    ? allApis.filter(a => a.status === filterStatus)
    : allApis;

  const toggleFilter = (status) => {
    setFilterStatus(prev => (prev === status ? null : status));
    // scroll table into view
    setTimeout(() => document.getElementById('api-inventory-table')?.scrollIntoView({ behavior: 'smooth', block: 'start' }), 50);
  };

  const methodColor = {
    GET: '#16a34a', POST: '#2563eb', PUT: '#d97706', DELETE: '#dc2626', PATCH: '#7c3aed',
  };

  const filterLabel = {
    SHADOW:   { text: 'Shadow APIs', color: '#dc2626' },
    ZOMBIE:   { text: 'Zombie APIs', color: '#d97706' },
    STALE:    { text: 'Stale APIs',  color: '#7c3aed' },
  };

  return (
    <div className="dashboard-content">
      {/* Page Header */}
      <div className="page-header">
        <div>
          <h2 className="page-title">Security Dashboard</h2>
          <p className="page-subtitle">Real-time API threat detection and defense overview</p>
        </div>
        <div className="header-live-badge">
          <span className="live-dot" />
          <span>Live Monitoring</span>
        </div>
      </div>

      {/* Metric Cards */}
      <div className="metrics-grid">
        <MetricCard
          icon={Layers} label="Total APIs" value={allApis.length} color="blue" subtitle="Discovered endpoints"
          isActive={filterStatus === null}
          onClick={() => { setFilterStatus(null); document.getElementById('api-inventory-table')?.scrollIntoView({ behavior: 'smooth', block: 'start' }); }}
        />
        <MetricCard
          icon={Ghost} label="Shadow APIs" value={shadow} color="red" subtitle="Undocumented"
          trend={shadow > 0 ? `${shadow} critical` : null}
          isActive={filterStatus === 'SHADOW'}
          onClick={shadow > 0 ? () => toggleFilter('SHADOW') : undefined}
        />
        <MetricCard
          icon={Skull} label="Zombie APIs" value={zombie} color="amber" subtitle="Deprecated but active"
          trend={zombie > 0 ? `${zombie} found` : null}
          isActive={filterStatus === 'ZOMBIE'}
          onClick={zombie > 0 ? () => toggleFilter('ZOMBIE') : undefined}
        />
        <MetricCard
          icon={Clock} label="Stale APIs" value={stale} color="purple" subtitle="Zero traffic"
          isActive={filterStatus === 'STALE'}
          onClick={stale > 0 ? () => toggleFilter('STALE') : undefined}
        />
      </div>

      {/* Threat Analysis Summary */}
      {analysis && (
        <div className="threat-analysis-card">
          <div className="card-header">
            <div className="card-header-left">
              <Target className="w-5 h-5 text-red-500" />
              <h3 className="card-title">Threat Analysis Summary</h3>
            </div>
            <span className="card-badge">{(analysis.shadow_apis?.length || 0) + (analysis.zombie_apis?.length || 0) + (analysis.stale_apis?.length || 0)} Issues Found</span>
          </div>
          <div className="threat-grid">
            {[
              { key: 'shadow_apis', title: 'Shadow APIs', icon: Ghost,       color: '#dc2626', severity: 'CRITICAL', desc: 'Undocumented endpoints in live traffic' },
              { key: 'zombie_apis', title: 'Zombie APIs', icon: Skull,       color: '#d97706', severity: 'HIGH',     desc: 'Deprecated but still receiving traffic' },
              { key: 'stale_apis',  title: 'Stale APIs',  icon: FileWarning, color: '#7c3aed', severity: 'MEDIUM',   desc: 'Documented but zero traffic' },
            ].map(section => {
              const items = analysis[section.key] || [];
              const Icon = section.icon;
              return (
                <div key={section.key} className="threat-section">
                  <div className="threat-section-header">
                    <Icon className="w-4 h-4" style={{ color: section.color }} />
                    <span className="threat-section-title" style={{ color: section.color }}>{section.title}</span>
                    <span className="threat-count" style={{ background: section.color + '15', color: section.color, border: `1px solid ${section.color}30` }}>{items.length}</span>
                    <span className="threat-severity">{section.severity}</span>
                  </div>
                  {items.length > 0 ? items.map(path => (
                    <button key={path} className="threat-path-item" onClick={() => onViewApi(null, path)}>
                      <span className="threat-dot" style={{ background: section.color }} />
                      <code>{path}</code>
                      <ArrowRight className="w-3 h-3 threat-arrow" />
                    </button>
                  )) : (
                    <div className="threat-path-item empty">
                      <CheckCircle2 className="w-3.5 h-3.5 text-green-500" />
                      <span>No threats detected</span>
                    </div>
                  )}
                  <p className="threat-desc">{section.desc}</p>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* API Inventory Table */}
      <div className="table-card">
        <div className="card-header">
          <div className="card-header-left">
            <Eye className="w-5 h-5 text-blue-500" />
            <h3 className="card-title">API Inventory</h3>
            {filterStatus && filterLabel[filterStatus] && (
              <span
                style={{
                  display: 'inline-flex', alignItems: 'center', gap: '5px',
                  background: filterLabel[filterStatus].color + '15',
                  color: filterLabel[filterStatus].color,
                  border: `1px solid ${filterLabel[filterStatus].color}30`,
                  borderRadius: 99, padding: '2px 10px', fontSize: '0.72rem', fontWeight: 700,
                }}
              >
                {filterLabel[filterStatus].text}
                <button
                  onClick={() => setFilterStatus(null)}
                  style={{ display: 'flex', alignItems: 'center', background: 'none', border: 'none', cursor: 'pointer', color: 'inherit', padding: 0 }}
                  title="Clear filter"
                >
                  <X className="w-3 h-3" />
                </button>
              </span>
            )}
          </div>
          <span className="card-count">{displayedApis.length} / {allApis.length} endpoints</span>
        </div>
        <div className="table-wrapper">
          <table className="data-table" id="api-inventory-table">
            <thead>
              <tr>
                <th>Endpoint</th>
                <th>Method</th>
                <th>Hits</th>
                <th>Latency</th>
                <th>Owner</th>
                <th>Status</th>
                <th>Risk</th>
                <th className="text-right">Action</th>
              </tr>
            </thead>
            <tbody>
              {displayedApis.length === 0 ? (
                <tr>
                  <td colSpan={8} style={{ textAlign: 'center', padding: '32px', color: '#94a3b8' }}>
                    No APIs match the current filter.
                  </td>
                </tr>
              ) : displayedApis.map(api => {
                return (
                  <tr
                    key={api.path}
                    className="table-row clickable"
                    onClick={() => onViewApi(api.id, api.path)}
                    id={`row-${api.path.replace(/\//g, '-')}`}
                  >
                    <td>
                      <div className="endpoint-cell">
                        <span className="endpoint-name">{api.name}</span>
                        <code className="endpoint-path">{api.path}</code>
                      </div>
                    </td>
                    <td>
                      <span className="method-badge" style={{ color: methodColor[api.method] || '#64748b', background: (methodColor[api.method] || '#64748b') + '12' }}>
                        {api.method}
                      </span>
                    </td>
                    <td className="mono">{api.hitCount.toLocaleString()}</td>
                    <td className="mono muted">{api.avgLatency}</td>
                    <td className="muted">{api.owner}</td>
                    <td><StatusBadge status={api.status} /></td>
                    <td><RiskBadge level={api.riskLevel} /></td>
                    <td className="text-right">
                        <button className="btn-view" onClick={(e) => { e.stopPropagation(); onViewApi(api.id, api.path); }}>
                          View Details
                          <ArrowRight className="w-3 h-3" />
                        </button>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
