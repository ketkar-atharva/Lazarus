import { useState, useEffect, useRef } from 'react';
import api from '../api';
import {
  ShieldAlert, Shield, ShieldCheck, Skull, Ghost, Clock, Layers,
  Activity, BarChart3, AlertTriangle, CheckCircle2, ArrowRight,
  Zap, Target, Lock, Eye, Server, Wifi, TrendingUp, FileText,
  RefreshCw, ArrowUpRight, Sparkles, Brain, ChevronDown, ChevronUp,
  X, ShieldOff, ExternalLink, Timer, WifiOff, Key, AlertCircle,
} from 'lucide-react';

/* ── Animated counter ─────────────────────────────────────────────────────── */
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

/* ── Status colour map ────────────────────────────────────────────────────── */
const STATUS = {
  zombie:  { color: '#d97706', bg: 'rgba(217,119,6,0.10)',  border: 'rgba(217,119,6,0.30)',  label: 'ZOMBIE',  icon: Skull        },
  shadow:  { color: '#dc2626', bg: 'rgba(220,38,38,0.10)',  border: 'rgba(220,38,38,0.30)',  label: 'SHADOW',  icon: Ghost        },
  stale:   { color: '#7c3aed', bg: 'rgba(124,58,237,0.10)', border: 'rgba(124,58,237,0.30)', label: 'STALE',   icon: Clock        },
  active:  { color: '#16a34a', bg: 'rgba(22,163,74,0.10)',  border: 'rgba(22,163,74,0.30)',  label: 'ACTIVE',  icon: CheckCircle2 },
  unknown: { color: '#64748b', bg: 'rgba(100,116,139,0.10)',border: 'rgba(100,116,139,0.30)',label: '—',       icon: AlertCircle  },
};

/* ── Per-API analysis row ─────────────────────────────────────────────────── */
function ApiAnalysisRow({ entry }) {
  const [open, setOpen] = useState(false);
  const ls    = (entry.lazarus_status || 'unknown').toLowerCase();
  const meta  = STATUS[ls] || STATUS.unknown;
  const Icon  = meta.icon;

  const reachable    = entry.reachable;
  const authExposed  = entry.auth_exposed;
  const httpCode     = entry.http_code;
  const responseMs   = entry.response_time_ms;
  const lastTraffic  = entry.last_traffic_at;
  const unknown      = entry.last_traffic_unknown;
  const probedAt     = entry.probed_at;

  /* Risk scoring for display */
  const risks = [];
  if (!reachable)   risks.push({ text: 'Unreachable endpoint',       sev: 'critical' });
  if (authExposed)  risks.push({ text: 'No auth required (exposed)',  sev: 'critical' });
  if (ls === 'stale' && unknown) risks.push({ text: 'No traffic signal found',         sev: 'high'     });
  if (ls === 'stale' && !unknown) risks.push({ text: 'Last traffic > 90 days ago',     sev: 'high'     });
  if (ls === 'zombie')            risks.push({ text: 'API dead — classified ZOMBIE',    sev: 'critical' });
  if (responseMs > 3000)          risks.push({ text: `Slow response (${responseMs}ms)`, sev: 'medium'  });
  if (httpCode >= 500)            risks.push({ text: `Server error ${httpCode}`,         sev: 'high'    });

  const sevColor = { critical: '#dc2626', high: '#d97706', medium: '#ca8a04', low: '#16a34a' };

  return (
    <div
      style={{
        border: `1px solid ${open ? meta.border : 'rgba(0,0,0,0.06)'}`,
        borderRadius: 10,
        marginBottom: 8,
        background: open ? meta.bg : '#ffffff',
        boxShadow: open ? 'none' : '0 1px 2px rgba(0,0,0,0.02)',
        transition: 'all 0.2s ease',
        overflow: 'hidden',
      }}
    >
      {/* Summary row */}
      <div
        onClick={() => setOpen(o => !o)}
        style={{
          display: 'flex', alignItems: 'center', gap: 12,
          padding: '12px 16px', cursor: 'pointer',
        }}
      >
        {/* Status badge */}
        <span style={{
          display: 'inline-flex', alignItems: 'center', gap: 5,
          padding: '3px 10px', borderRadius: 20, fontSize: '0.7rem', fontWeight: 700,
          background: meta.bg, color: meta.color, border: `1px solid ${meta.border}`,
          whiteSpace: 'nowrap', minWidth: 72, justifyContent: 'center',
        }}>
          <Icon style={{ width: 11, height: 11 }} />
          {meta.label}
        </span>

        {/* api_id */}
        <code style={{ fontSize: '0.78rem', color: '#94a3b8', minWidth: 90 }}>
          {entry.api_id}
        </code>

        {/* URL */}
        <span style={{ flex: 1, fontSize: '0.82rem', color: '#334155', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', fontWeight: 500 }}>
          <span style={{ color: '#94a3b8', marginRight: 4, fontWeight: 400 }}>{entry.method}</span>
          {entry.url}
        </span>

        {/* Quick signals */}
        <div style={{ display: 'flex', gap: 8, alignItems: 'center', flexShrink: 0 }}>
          {httpCode && (
            <span style={{ fontSize: '0.72rem', color: httpCode < 400 ? '#16a34a' : '#dc2626', fontWeight: 600 }}>
              {httpCode}
            </span>
          )}
          {authExposed && (
            <span title="Auth exposed" style={{ color: '#dc2626' }}>
              <ShieldOff style={{ width: 13, height: 13 }} />
            </span>
          )}
          {!reachable && (
            <span title="Unreachable" style={{ color: '#64748b' }}>
              <WifiOff style={{ width: 13, height: 13 }} />
            </span>
          )}
          {risks.length > 0 && (
            <span style={{
              fontSize: '0.68rem', background: sevColor[risks[0].sev] + '22',
              color: sevColor[risks[0].sev], padding: '2px 8px', borderRadius: 12,
              border: `1px solid ${sevColor[risks[0].sev]}44`, fontWeight: 700,
            }}>
              {risks.length} risk{risks.length !== 1 ? 's' : ''}
            </span>
          )}
        </div>

        {open ? <ChevronUp style={{ width: 14, height: 14, color: '#64748b', flexShrink: 0 }} />
               : <ChevronDown style={{ width: 14, height: 14, color: '#64748b', flexShrink: 0 }} />}
      </div>

      {/* Expanded analysis */}
      {open && (
        <div style={{ padding: '0 16px 16px', display: 'flex', flexDirection: 'column', gap: 12 }}>
          {/* Metric chips */}
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>
            {[
              {
                icon: reachable ? Wifi : WifiOff,
                label: 'Reachable',
                value: reachable ? 'Yes' : 'No',
                color: reachable ? '#16a34a' : '#dc2626',
              },
              {
                icon: Timer,
                label: 'Response',
                value: responseMs != null ? `${responseMs} ms` : '—',
                color: responseMs > 3000 ? '#d97706' : '#16a34a',
              },
              {
                icon: Key,
                label: 'Auth Exposed',
                value: authExposed ? 'YES' : 'No',
                color: authExposed ? '#dc2626' : '#16a34a',
              },
              {
                icon: Clock,
                label: 'Last Traffic',
                value: unknown ? 'Unknown' : (lastTraffic ? new Date(lastTraffic).toLocaleDateString() : '—'),
                color: unknown ? '#d97706' : '#94a3b8',
              },
              {
                icon: Activity,
                label: 'HTTP Code',
                value: httpCode ?? '—',
                color: !httpCode ? '#64748b' : httpCode < 400 ? '#16a34a' : '#dc2626',
              },
            ].map(({ icon: Ic, label, value, color }) => (
              <div key={label} style={{
                display: 'flex', alignItems: 'center', gap: 6, padding: '6px 12px',
                background: `${color}12`, border: `1px solid ${color}30`,
                borderRadius: 8, fontSize: '0.76rem',
              }}>
                <Ic style={{ width: 12, height: 12, color }} />
                <span style={{ color: '#64748b' }}>{label}:</span>
                <span style={{ color: color, fontWeight: 600 }}>{String(value)}</span>
              </div>
            ))}
          </div>

          {/* Risk findings */}
          {risks.length > 0 && (
            <div>
              <p style={{ fontSize: '0.72rem', color: '#64748b', textTransform: 'uppercase', letterSpacing: 1, marginBottom: 6 }}>
                Risk Findings
              </p>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
                {risks.map((r, i) => (
                  <div key={i} style={{
                    display: 'flex', alignItems: 'center', gap: 8,
                    padding: '5px 10px', borderRadius: 6,
                    background: `${sevColor[r.sev]}12`, border: `1px solid ${sevColor[r.sev]}30`,
                  }}>
                    <AlertCircle style={{ width: 12, height: 12, color: sevColor[r.sev], flexShrink: 0 }} />
                    <span style={{ fontSize: '0.78rem', color: sevColor[r.sev], fontWeight: 700, textTransform: 'uppercase', minWidth: 56 }}>
                      {r.sev}
                    </span>
                    <span style={{ fontSize: '0.78rem', color: '#475569' }}>{r.text}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Recommendations */}
          <div>
            <p style={{ fontSize: '0.72rem', color: '#64748b', textTransform: 'uppercase', letterSpacing: 1, marginBottom: 6 }}>
              Recommendation
            </p>
            <p style={{ fontSize: '0.8rem', color: '#475569', lineHeight: 1.6 }}>
              {ls === 'zombie' && 'This endpoint is unreachable. Verify the URL, check gateway rules, and consider removing it from the catalog if decommissioned.'}
              {ls === 'stale'  && (unknown
                ? 'No traffic signal found. Confirm whether this API is still in use before decommissioning.'
                : 'No traffic in over 90 days. Schedule a review — decommission if no longer needed.')}
              {ls === 'shadow' && 'Undocumented endpoint detected in traffic. Register it in the catalog or investigate if it is unauthorised.'}
              {ls === 'active' && !authExposed && 'API appears healthy. Continue routine monitoring and ensure auth policies are enforced.'}
              {ls === 'active' && authExposed && 'API is reachable without authentication. Enforce authorization middleware immediately.'}
            </p>
          </div>

          {probedAt && (
            <p style={{ fontSize: '0.7rem', color: '#475569', marginTop: 2 }}>
              Probed at: {new Date(probedAt).toLocaleString()}
            </p>
          )}
        </div>
      )}
    </div>
  );
}

/* ── Drill-down panel shown below stat cards ──────────────────────────────── */
function DrillDownPanel({ filter, catalog, traffic = [], deployedPaths = new Set(), onClose }) {
  const meta      = STATUS[filter] || STATUS.unknown;
  const Icon      = meta.icon;
  const panelRef  = useRef(null);

  useEffect(() => {
    panelRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' });
  }, [filter]);

  let filtered = [];

  if (filter === 'shadow') {
    const getPath = (a) => {
      if (a.path) return a.path;
      if (!a.url) return '';
      try { return new URL(a.url).pathname; } catch (e) { return a.url; }
    };
    const catalogPaths = new Set(catalog.map(getPath));
    
    traffic.forEach((flow, i) => {
      if (!catalogPaths.has(flow.path) && !deployedPaths.has(flow.path)) {
        filtered.push({
          api_id: 'SHADOW-' + flow.path.replace(/\//g, '-'),
          url: flow.path,
          method: flow.method || 'GET',
          lazarus_status: 'shadow',
          reachable: true,
          auth_exposed: true,
          http_code: flow.response_codes ? parseInt(Object.keys(flow.response_codes)[0]) || 200 : 200,
          response_time_ms: parseInt(flow.avg_latency) || null,
          last_traffic_at: flow.last_seen,
          last_traffic_unknown: false,
          probed_at: new Date().toISOString()
        });
      }
    });
  } else {
    filtered = catalog.filter(a => (a.lazarus_status || '').toLowerCase() === filter);
  }

  return (
    <div
      ref={panelRef}
      style={{
        marginTop: 24,
        border: `1.5px solid ${meta.border}`,
        borderRadius: 14,
        background: '#ffffff',
        boxShadow: '0 4px 20px rgba(0,0,0,0.04)',
        overflow: 'hidden',
      }}
    >
      {/* Panel header */}
      <div style={{
        display: 'flex', alignItems: 'center', justifyContent: 'space-between',
        padding: '14px 20px',
        borderBottom: `1px solid ${meta.border}`,
        background: meta.bg,
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <Icon style={{ width: 18, height: 18, color: meta.color }} />
          <h3 style={{ margin: 0, fontSize: '0.95rem', fontWeight: 700, color: meta.color }}>
            {meta.label} APIs
          </h3>
          <span style={{
            background: meta.bg, color: meta.color, border: `1px solid ${meta.border}`,
            borderRadius: 20, padding: '2px 10px', fontSize: '0.72rem', fontWeight: 700,
          }}>
            {filtered.length} found
          </span>
        </div>
        <button
          onClick={onClose}
          style={{ background: 'none', border: 'none', cursor: 'pointer', color: '#64748b', display: 'flex', alignItems: 'center' }}
        >
          <X style={{ width: 16, height: 16 }} />
        </button>
      </div>

      {/* API rows */}
      <div style={{ padding: 16 }}>
        {filtered.length === 0 ? (
          <div style={{ textAlign: 'center', padding: '40px 0', color: '#64748b' }}>
            <CheckCircle2 style={{ width: 32, height: 32, margin: '0 auto 12px', opacity: 0.4 }} />
            <p style={{ margin: 0, fontSize: '0.9rem' }}>No {meta.label} APIs found in the catalog.</p>
            <p style={{ margin: '6px 0 0', fontSize: '0.78rem', opacity: 0.7 }}>Upload a CSV to start probing.</p>
          </div>
        ) : (
          filtered.map((entry, i) => <ApiAnalysisRow key={entry.api_id || i} entry={entry} />)
        )}
      </div>
    </div>
  );
}

export default function DashboardHome({ catalog, traffic, analysis, onViewApi, onNavigate, onOpenChat }) {
  const [dbStatus,          setDbStatus]          = useState(null);
  const [decommissionCount, setDecommissionCount] = useState(0);
  const [activityLog,       setActivityLog]        = useState([]);
  const [activeFilter,      setActiveFilter]       = useState(null); // 'zombie' | 'shadow' | 'stale' | 'active' | null

  useEffect(() => {
    (async () => {
      try {
        const [dbRes, logRes, decomRes] = await Promise.all([
          api.get('/api/db-status').catch(() => ({ data: { connected: false } })),
          api.get('/api/activity-log').catch(() => ({ data: [] })),
          api.get('/api/decommission-log').catch(() => ({ data: [] })),
        ]);
        setDbStatus(dbRes.data);
        setActivityLog(logRes.data.slice(0, 6));
        setDecommissionCount(decomRes.data.length);
      } catch (e) { console.error(e); }
    })();
  }, []);

  /* Counts from catalog */
  const getPath = (a) => {
    if (a.path) return a.path;
    if (!a.url) return '';
    try { return new URL(a.url).pathname; } catch (e) { return a.url; }
  };
  const catalogPaths = new Set(catalog.map(getPath));
  let shadowCount = 0, zombieCount = 0, staleCount = 0, activeCount = 0;
  catalog.forEach(a => {
    const flow = traffic.find(t => t.path === a.path);
    const ls = a.lazarus_status?.toLowerCase();
    if (ls) {
      if      (ls === 'zombie') zombieCount++;
      else if (ls === 'shadow') shadowCount++;
      else if (ls === 'stale')  staleCount++;
      else                      activeCount++;
    } else {
      if (a.is_deprecated && flow && flow.hit_count > 0) zombieCount++;
      else if (!flow || flow.hit_count === 0)            staleCount++;
      else                                               activeCount++;
    }
  });
  traffic.forEach(flow => {
    if (!catalogPaths.has(flow.path)) shadowCount++;
  });

  const totalApis       = catalog.length;
  const threatCount     = shadowCount + zombieCount + staleCount;
  const totalTrafficHits = traffic.reduce((s, t) => s + (t.hit_count || 0), 0);

  const handleCardClick = (filter) => {
    setActiveFilter(prev => prev === filter ? null : filter);
  };

  /* Stat card styles */
  const cardStyle = (filter, color, bg, border) => ({
    display: 'flex', flexDirection: 'column', gap: 8,
    padding: '18px 20px', borderRadius: 12, cursor: 'pointer',
    border: `2px solid ${activeFilter === filter ? border : 'transparent'}`,
    background: activeFilter === filter ? bg : 'rgba(255,255,255,0.03)',
    boxShadow: activeFilter === filter ? `0 0 0 3px ${color}22` : 'none',
    transition: 'all 0.2s ease',
    flex: 1,
  });

  return (
    <div className="dashboard-content">

      {/* Hero */}
      <div className="dashboard-hero">
        <div className="hero-content">
          <div className="hero-badge">
            <ShieldAlert className="w-4 h-4" />
            <span>Zombie API Discovery &amp; Defence</span>
          </div>
          <h1 className="hero-title">Lazarus</h1>
          <p className="hero-description">
            An automated platform that continuously scans the bank's network infrastructure, API gateways,
            and deployment environments to discover <strong>undocumented</strong>, <strong>shadow</strong>,
            and <strong>zombie APIs</strong>. It classifies each API's security posture, provides
            actionable recommendations, and supports automated decommissioning workflows with
            full execution report.
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
          <div className="hero-pulse-ring ring-1" /><div className="hero-pulse-ring ring-2" /><div className="hero-pulse-ring ring-3" />
          <div className="hero-shield-icon"><ShieldCheck className="w-12 h-12" /></div>
          <div className="hero-float-dot dot-1" /><div className="hero-float-dot dot-2" />
          <div className="hero-float-dot dot-3" /><div className="hero-float-dot dot-4" />
        </div>
      </div>

      {/* ── Stat Cards ── */}
      <div style={{ marginBottom: 4 }}>
        <p style={{ fontSize: '0.75rem', color: '#475569', marginBottom: 10, letterSpacing: 0.5 }}>
          CLICK A CATEGORY TO DRILL DOWN ↓
        </p>
      </div>

      <div className="stats-row" style={{ alignItems: 'stretch' }}>

        {/* Total */}
        <div className="stat-card" style={cardStyle(null, '#2563eb', 'rgba(37,99,235,0.07)', '#bfdbfe')}
          onClick={() => onNavigate('inventory')}>
          <div className="stat-icon" style={{ background: '#eff6ff', borderColor: '#bfdbfe' }}>
            <Layers className="w-5 h-5" style={{ color: '#2563eb' }} />
          </div>
          <div className="stat-info">
            <span className="stat-value" style={{ color: '#2563eb' }}><AnimatedNumber value={totalApis} /></span>
            <span className="stat-label">TOTAL APIS</span>
          </div>
          <span style={{ fontSize: '0.68rem', color: '#64748b' }}>Discovered endpoints</span>
          <span style={{ fontSize: '0.68rem', color: '#2563eb', fontWeight: 600 }}>View inventory ↓</span>
        </div>

        {/* Shadow */}
        <div className="stat-card" style={cardStyle('shadow', '#dc2626', STATUS.shadow.bg, STATUS.shadow.border)}
          onClick={() => handleCardClick('shadow')}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
            <div className="stat-icon" style={{ background: '#fef2f2', borderColor: '#fecaca' }}>
              <Ghost className="w-5 h-5" style={{ color: '#dc2626' }} />
            </div>
            {shadowCount > 0 && <span style={{ fontSize: '0.65rem', color: '#dc2626', fontWeight: 700 }}>↗ {shadowCount} critical</span>}
          </div>
          <div className="stat-info">
            <span className="stat-value" style={{ color: '#dc2626' }}><AnimatedNumber value={shadowCount} /></span>
            <span className="stat-label">SHADOW APIS</span>
          </div>
          <span style={{ fontSize: '0.68rem', color: '#64748b' }}>Undocumented</span>
          <span style={{ fontSize: '0.68rem', color: '#dc2626', fontWeight: 600 }}>
            {activeFilter === 'shadow' ? 'Hide list ↑' : 'Click to filter ↓'}
          </span>
        </div>

        {/* Zombie */}
        <div className="stat-card" style={cardStyle('zombie', '#d97706', STATUS.zombie.bg, STATUS.zombie.border)}
          onClick={() => handleCardClick('zombie')}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
            <div className="stat-icon" style={{ background: '#fffbeb', borderColor: '#fde68a' }}>
              <Skull className="w-5 h-5" style={{ color: '#d97706' }} />
            </div>
            {zombieCount > 0 && <span style={{ fontSize: '0.65rem', color: '#d97706', fontWeight: 700 }}>↗ {zombieCount} found</span>}
          </div>
          <div className="stat-info">
            <span className="stat-value" style={{ color: '#d97706' }}><AnimatedNumber value={zombieCount} /></span>
            <span className="stat-label">ZOMBIE APIS</span>
          </div>
          <span style={{ fontSize: '0.68rem', color: '#64748b' }}>Deprecated but active</span>
          <span style={{ fontSize: '0.68rem', color: '#d97706', fontWeight: 600 }}>
            {activeFilter === 'zombie' ? 'Hide list ↑' : 'Click to filter ↓'}
          </span>
        </div>

        {/* Stale */}
        <div className="stat-card" style={cardStyle('stale', '#7c3aed', STATUS.stale.bg, STATUS.stale.border)}
          onClick={() => handleCardClick('stale')}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
            <div className="stat-icon" style={{ background: '#f5f3ff', borderColor: '#ddd6fe' }}>
              <Clock className="w-5 h-5" style={{ color: '#7c3aed' }} />
            </div>
            {staleCount > 0 && <span style={{ fontSize: '0.65rem', color: '#7c3aed', fontWeight: 700 }}>↗ {staleCount} found</span>}
          </div>
          <div className="stat-info">
            <span className="stat-value" style={{ color: '#7c3aed' }}><AnimatedNumber value={staleCount} /></span>
            <span className="stat-label">STALE APIS</span>
          </div>
          <span style={{ fontSize: '0.68rem', color: '#64748b' }}>Zero traffic</span>
          <span style={{ fontSize: '0.68rem', color: '#7c3aed', fontWeight: 600 }}>
            {activeFilter === 'stale' ? 'Hide list ↑' : 'Click to filter ↓'}
          </span>
        </div>

        {/* Active */}
        <div className="stat-card" style={cardStyle('active', '#16a34a', STATUS.active.bg, STATUS.active.border)}
          onClick={() => handleCardClick('active')}>
          <div className="stat-icon" style={{ background: '#f0fdf4', borderColor: '#bbf7d0' }}>
            <ShieldCheck className="w-5 h-5" style={{ color: '#16a34a' }} />
          </div>
          <div className="stat-info">
            <span className="stat-value" style={{ color: '#16a34a' }}><AnimatedNumber value={activeCount} /></span>
            <span className="stat-label">ACTIVE APIS</span>
          </div>
          <span style={{ fontSize: '0.68rem', color: '#64748b' }}>Healthy &amp; reachable</span>
          <span style={{ fontSize: '0.68rem', color: '#16a34a', fontWeight: 600 }}>
            {activeFilter === 'active' ? 'Hide list ↑' : 'Click to filter ↓'}
          </span>
        </div>


      </div>

      {/* ── Drill-down Panel ── */}
      {activeFilter && (
        <DrillDownPanel
          filter={activeFilter}
          catalog={catalog}
          traffic={traffic}
          onClose={() => setActiveFilter(null)}
        />
      )}

      {/* Two-Column Layout */}
      <div className="dashboard-grid-2col" style={{ marginTop: 28 }}>

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
              { icon: Wifi,     title: 'Continuous Network Scanning',  desc: 'Scans API gateways, code repositories, and deployment environments in real-time',              color: '#2563eb' },
              { icon: Eye,      title: 'Shadow API Discovery',          desc: 'Detects undocumented endpoints in live traffic not present in the API catalog',                color: '#dc2626' },
              { icon: Skull,    title: 'Zombie API Detection',          desc: 'Identifies deprecated APIs still receiving production traffic — a critical risk',               color: '#d97706' },
              { icon: Lock,     title: 'Security Posture Assessment',   desc: 'Evaluates authentication, encryption, rate limiting, data exposure & input validation',        color: '#7c3aed' },
              { icon: Zap,      title: 'Automated Decommissioning',     desc: 'Traffic rerouting, gateway blocking, DNS removal, credential revocation — all automated',      color: '#dc2626' },
              { icon: FileText, title: 'Compliance Reporting',          desc: 'Post-remediation audit trails, evidence chain, and RBI/PCI-DSS compliance reports',           color: '#16a34a' },
            ].map((cap, i) => {
              const Ic = cap.icon;
              return (
                <div key={i} className="capability-item">
                  <div className="capability-icon" style={{ background: cap.color + '12', borderColor: cap.color + '30' }}>
                    <Ic className="w-4 h-4" style={{ color: cap.color }} />
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
              <span className="report-status-pill"><CheckCircle2 className="w-3.5 h-3.5" /> Operational</span>
            </div>
            <div className="health-grid">
              <div className="health-item"><CheckCircle2 className="w-4 h-4 text-green-500" /><span className="health-label">Scanner</span><span className="health-value green">Active</span></div>
              <div className="health-item"><CheckCircle2 className="w-4 h-4 text-green-500" /><span className="health-label">Kong Gateway</span><span className="health-value green">Connected</span></div>
              <div className="health-item">
                {dbStatus?.connected ? <CheckCircle2 className="w-4 h-4 text-green-500" /> : <AlertTriangle className="w-4 h-4 text-amber-500" />}
                <span className="health-label">MongoDB</span>
                <span className={`health-value ${dbStatus?.connected ? 'green' : 'amber'}`}>{dbStatus?.connected ? 'Connected' : 'Disconnected'}</span>
              </div>
              <div className="health-item"><CheckCircle2 className="w-4 h-4 text-green-500" /><span className="health-label">Email SMTP</span><span className="health-value green">Gmail</span></div>
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
              {[
                { label: 'Shadow', count: shadowCount, color: '#dc2626', filter: 'shadow' },
                { label: 'Zombie', count: zombieCount, color: '#d97706', filter: 'zombie' },
                { label: 'Stale',  count: staleCount,  color: '#7c3aed', filter: 'stale'  },
                { label: 'Remediated', count: decommissionCount, color: '#16a34a', filter: null },
              ].map(({ label, count, color, filter }) => (
                <div key={label} className="threat-bar-row"
                  style={{ cursor: filter ? 'pointer' : 'default' }}
                  onClick={() => filter && handleCardClick(filter)}>
                  <span className="threat-bar-label" style={{ color: filter && activeFilter === filter ? color : undefined }}>{label}</span>
                  <div className="threat-bar-track">
                    <div className="threat-bar-fill" style={{ width: `${totalApis ? (count / totalApis) * 100 : 0}%`, background: color }} />
                  </div>
                  <span className="threat-bar-count" style={{ color }}>{count}</span>
                </div>
              ))}
            </div>
          </div>

          {/* AI Security Insights */}
          <div className="detail-card ai-dashboard-widget">
            <div className="card-header">
              <div className="card-header-left">
                <Sparkles className="w-5 h-5 text-purple-500" />
                <h3 className="card-title">AI Security Insights</h3>
              </div>
              <span className="ai-powered-badge"><Sparkles className="w-3 h-3" /> AI</span>
            </div>
            <div className="ai-widget-body">
              <p className="ai-widget-desc">
                Get AI-powered security analysis, plain-English risk explanations, and automated compliance reports for your entire API landscape.
              </p>
              <div className="ai-widget-actions">
                <button className="ai-widget-btn primary" onClick={() => onNavigate('ai')}><Brain className="w-4 h-4" /> AI Insights</button>
                <button className="ai-widget-btn secondary" onClick={onOpenChat}><Sparkles className="w-4 h-4" /> Ask AI</button>
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
                  <span>No activity yet. Upload a CSV to start probing APIs.</span>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Key Metrics Bar */}
      <div className="metrics-bar">
        <div className="metrics-bar-item"><TrendingUp className="w-4 h-4 text-blue-500" /><span className="mb-value">{totalTrafficHits.toLocaleString()}</span><span className="mb-label">Total API Hits</span></div>
        <div className="metrics-bar-divider" />
        <div className="metrics-bar-item"><Server className="w-4 h-4 text-blue-500" /><span className="mb-value">{totalApis}</span><span className="mb-label">Endpoints Monitored</span></div>
        <div className="metrics-bar-divider" />
        <div className="metrics-bar-item"><Shield className="w-4 h-4 text-green-500" /><span className="mb-value">{decommissionCount}</span><span className="mb-label">APIs Remediated</span></div>
      </div>
    </div>
  );
}
