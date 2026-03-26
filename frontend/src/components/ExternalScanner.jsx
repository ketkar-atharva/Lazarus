import { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import {
  Globe,
  Search,
  RefreshCw,
  CheckCircle2,
  XCircle,
  AlertTriangle,
  Shield,
  ShieldAlert,
  AlertCircle,
  Lock,
  Unlock,
  Server,
  Radar,
  Wifi,
  Zap,
} from 'lucide-react';

const API_BASE = 'http://localhost:8000';

/* ── Risk badge colours ── */
const RISK_STYLE = {
  CRITICAL: { bg: '#fef2f2', border: '#fecaca', text: '#dc2626' },
  HIGH:     { bg: '#fff7ed', border: '#fed7aa', text: '#ea580c' },
  MEDIUM:   { bg: '#fffbeb', border: '#fde68a', text: '#d97706' },
  LOW:      { bg: '#f0fdf4', border: '#bbf7d0', text: '#16a34a' },
  UNKNOWN:  { bg: '#f8fafc', border: '#e2e8f0', text: '#64748b' },
};

const SEVERITY_STYLE = {
  CRITICAL: { cls: 'risk-badge critical' },
  HIGH:     { cls: 'risk-badge high' },
  MEDIUM:   { cls: 'risk-badge medium' },
  LOW:      { cls: 'risk-badge low' },
};

const RiskBadge = ({ level }) => {
  const s = RISK_STYLE[level] || RISK_STYLE.UNKNOWN;
  return (
    <span
      style={{
        background: s.bg,
        color: s.text,
        border: `1px solid ${s.border}`,
        padding: '2px 10px',
        borderRadius: 99,
        fontWeight: 700,
        fontSize: '0.72rem',
        letterSpacing: '0.04em',
      }}
    >
      {level}
    </span>
  );
};

/* ── Rich Scanning Animation Overlay ── */
const SCAN_STEPS = [
  { icon: Wifi,         label: 'Connecting to target…' },
  { icon: Shield,       label: 'Checking security headers…' },
  { icon: Globe,        label: 'Probing CORS configuration…' },
  { icon: Server,       label: 'Detecting server technology…' },
  { icon: Search,       label: 'Probing shadow endpoints…' },
  { icon: Zap,          label: 'Computing risk score…' },
];

function ScanningOverlay({ url }) {
  const [stepIdx, setStepIdx] = useState(0);
  const [barWidth, setBarWidth] = useState(0);
  const stepRef = useRef(null);

  useEffect(() => {
    let i = 0;
    setStepIdx(0);
    setBarWidth(8);
    stepRef.current = setInterval(() => {
      i += 1;
      if (i < SCAN_STEPS.length) {
        setStepIdx(i);
        setBarWidth(Math.round(((i + 1) / SCAN_STEPS.length) * 88) + 8);
      }
    }, 1400);
    return () => clearInterval(stepRef.current);
  }, []);

  const StepIcon = SCAN_STEPS[stepIdx].icon;

  return (
    <div style={{
      background: '#fff',
      border: '1px solid #e2e8f0',
      borderRadius: 16,
      padding: '36px 32px 32px',
      marginBottom: 24,
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      gap: 20,
      boxShadow: '0 4px 20px rgba(37,99,235,0.07)',
    }}>
      {/* Radar animation */}
      <div className="ext-scan-radar">
        <div className="ext-scan-ring ring1" />
        <div className="ext-scan-ring ring2" />
        <div className="ext-scan-ring ring3" />
        <div className="ext-scan-core">
          <Radar className="ext-scan-radar-icon" />
        </div>
      </div>

      {/* Title */}
      <div style={{ textAlign: 'center' }}>
        <p style={{ fontWeight: 700, fontSize: '1rem', color: '#0f172a', marginBottom: 4 }}>
          Scanning Target
        </p>
        <code style={{ fontSize: '0.78rem', color: '#2563eb', background: '#eff6ff', padding: '3px 10px', borderRadius: 6 }}>
          {url}
        </code>
      </div>

      {/* Active step */}
      <div style={{
        display: 'flex', alignItems: 'center', gap: 10,
        background: '#f8fafc', borderRadius: 10, padding: '10px 18px',
        border: '1px solid #e2e8f0', minWidth: 260, justifyContent: 'center',
      }}>
        <StepIcon style={{ width: 16, height: 16, color: '#2563eb', flexShrink: 0 }} />
        <span style={{ fontSize: '0.85rem', color: '#334155', fontWeight: 500 }}>
          {SCAN_STEPS[stepIdx].label}
        </span>
      </div>

      {/* Step dots */}
      <div style={{ display: 'flex', gap: 6, alignItems: 'center' }}>
        {SCAN_STEPS.map((_, i) => (
          <span
            key={i}
            style={{
              width: i === stepIdx ? 18 : 7,
              height: 7,
              borderRadius: 99,
              background: i <= stepIdx ? '#2563eb' : '#e2e8f0',
              transition: 'all 0.3s ease',
            }}
          />
        ))}
      </div>

      {/* Progress bar */}
      <div style={{ width: '100%', maxWidth: 320 }}>
        <div style={{
          width: '100%', height: 6, background: '#f1f5f9',
          borderRadius: 99, overflow: 'hidden',
        }}>
          <div style={{
            height: '100%',
            width: `${barWidth}%`,
            background: 'linear-gradient(90deg, #2563eb, #6366f1)',
            borderRadius: 99,
            transition: 'width 1.2s ease',
          }} />
        </div>
        <p style={{ fontSize: '0.72rem', color: '#94a3b8', marginTop: 6, textAlign: 'center', fontWeight: 500 }}>
          Step {stepIdx + 1} of {SCAN_STEPS.length} — this may take 10–20 seconds
        </p>
      </div>
    </div>
  );
}

export default function ExternalScanner() {
  const [url, setUrl] = useState('');
  const [scanning, setScanning] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  const handleScan = async () => {
    const trimmed = url.trim();
    if (!trimmed) return;
    setScanning(true);
    setResult(null);
    setError(null);
    try {
      const res = await axios.post(`${API_BASE}/api/scan-external`, { url: trimmed });
      setResult(res.data);
    } catch (err) {
      setError(err?.response?.data?.detail || 'Scan failed. Is the Lazarus backend running?');
    } finally {
      setScanning(false);
    }
  };

  const risk = result?.overall_risk || 'UNKNOWN';
  const riskStyle = RISK_STYLE[risk] || RISK_STYLE.UNKNOWN;

  return (
    <div className="dashboard-content">
      {/* Page Header */}
      <div className="page-header">
        <div>
          <h2 className="page-title">External URL Scanner</h2>
          <p className="page-subtitle">
            Probe any public API or website for security misconfigurations, exposed endpoints, and header weaknesses
          </p>
        </div>
        <div className="header-live-badge" style={{ background: '#eff6ff', borderColor: '#bfdbfe', color: '#2563eb' }}>
          <Globe className="w-4 h-4" />
          <span>Live Probe</span>
        </div>
      </div>

      {/* Input Card */}
      <div className="detail-card" style={{ marginBottom: 24 }}>
        <div className="card-header">
          <div className="card-header-left">
            <Search className="w-5 h-5 text-blue-500" />
            <h3 className="card-title">Target URL</h3>
          </div>
        </div>
        <div style={{ padding: '16px 24px 20px' }}>
          <div style={{ display: 'flex', gap: 12, alignItems: 'center' }}>
            <input
              type="url"
              id="external-scanner-url"
              style={{
                flex: 1,
                padding: '10px 14px',
                border: '1px solid #e2e8f0',
                borderRadius: 8,
                fontSize: '0.9rem',
                fontFamily: 'monospace',
                outline: 'none',
                background: '#f8fafc',
                color: '#1e293b',
                transition: 'border-color 0.2s',
              }}
              placeholder="https://api.example.com"
              value={url}
              onChange={e => setUrl(e.target.value)}
              onKeyDown={e => e.key === 'Enter' && handleScan()}
              disabled={scanning}
              onFocus={e => (e.target.style.borderColor = '#93c5fd')}
              onBlur={e  => (e.target.style.borderColor = '#e2e8f0')}
            />
            <button
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                justifyContent: 'center',
                gap: 8,
                padding: '10px 22px',
                borderRadius: 8,
                border: scanning || !url.trim() ? '1px solid #e2e8f0' : '1px solid #1d4ed8',
                background: scanning || !url.trim() ? '#f1f5f9' : '#2563eb',
                color: scanning || !url.trim() ? '#94a3b8' : '#fff',
                fontWeight: 600,
                fontSize: '0.875rem',
                cursor: scanning || !url.trim() ? 'not-allowed' : 'pointer',
                whiteSpace: 'nowrap',
                fontFamily: 'inherit',
                transition: 'all 0.2s',
                flexShrink: 0,
              }}
              onClick={handleScan}
              disabled={scanning || !url.trim()}
              id="btn-scan-external"
            >
              {scanning ? (
                <><RefreshCw style={{ width: 15, height: 15, animation: 'spin 0.8s linear infinite' }} /> Scanning…</>
              ) : (
                <><Search style={{ width: 15, height: 15 }} /> Scan Now</>
              )}
            </button>
          </div>
          <p style={{ fontSize: '0.78rem', color: '#94a3b8', marginTop: 10 }}>
            Examples:&nbsp;
            <code style={{ background: '#f1f5f9', padding: '1px 6px', borderRadius: 4 }}>https://httpbin.org</code>
            &nbsp;·&nbsp;
            <code style={{ background: '#f1f5f9', padding: '1px 6px', borderRadius: 4 }}>https://jsonplaceholder.typicode.com</code>
          </p>
        </div>
      </div>

      {/* Rich Scanning Animation */}
      {scanning && <ScanningOverlay url={url} />}

      {/* API error (backend unreachable etc.) */}
      {error && !scanning && (
        <div className="detail-card" style={{ borderLeft: '4px solid #dc2626', marginBottom: 24 }}>
          <div style={{ display: 'flex', gap: 14, alignItems: 'flex-start', padding: '16px 24px' }}>
            <AlertTriangle className="w-6 h-6 text-red-500" style={{ flexShrink: 0 }} />
            <div>
              <p style={{ fontWeight: 600, color: '#dc2626', marginBottom: 4 }}>Scan Failed</p>
              <p style={{ color: '#64748b', fontSize: '0.87rem' }}>{error}</p>
            </div>
          </div>
        </div>
      )}

      {/* Results */}
      {result && !scanning && (
        <>
          {/* Unreachable state */}
          {!result.reachable && (
            <div className="detail-card" style={{ borderLeft: '4px solid #dc2626', marginBottom: 24 }}>
              <div style={{ display: 'flex', gap: 14, alignItems: 'flex-start', padding: '16px 24px' }}>
                <XCircle className="w-6 h-6 text-red-500" style={{ flexShrink: 0 }} />
                <div>
                  <p style={{ fontWeight: 600, color: '#dc2626', marginBottom: 4 }}>
                    Target Unreachable
                  </p>
                  <p style={{ color: '#64748b', fontSize: '0.87rem' }}>
                    {result.error || 'The URL could not be reached. Please check the address and try again.'}
                  </p>
                </div>
              </div>
            </div>
          )}

          {/* ── Top Summary Row ── */}
          {result.reachable && (
            <>
              <div className="detail-card" style={{ borderLeft: `4px solid ${riskStyle.text}`, marginBottom: 20 }}>
                <div className="card-header">
                  <div className="card-header-left">
                    <Globe className="w-5 h-5 text-blue-500" />
                    <h3 className="card-title">Scan Summary</h3>
                  </div>
                  <RiskBadge level={risk} />
                </div>
                <div className="detail-meta-grid" style={{ margin: 0, padding: '16px 24px 20px' }}>
                  <div className="meta-item">
                    <Globe className="w-3.5 h-3.5" />
                    <span className="meta-label">URL</span>
                    <code className="meta-value" style={{ wordBreak: 'break-all' }}>{result.url_scanned}</code>
                  </div>
                  <div className="meta-item">
                    <AlertCircle className="w-3.5 h-3.5" />
                    <span className="meta-label">Status Code</span>
                    <span className="meta-value">{result.status_code}</span>
                  </div>
                  <div className="meta-item">
                    <RefreshCw className="w-3.5 h-3.5" />
                    <span className="meta-label">Response Time</span>
                    <span className="meta-value">{result.response_time_ms} ms</span>
                  </div>
                  <div className="meta-item">
                    <span className="meta-label">HTTPS</span>
                    {result.uses_https ? (
                      <span style={{ color: '#16a34a', fontWeight: 600, display: 'flex', alignItems: 'center', gap: 4 }}>
                        <Lock className="w-3.5 h-3.5" /> Secure
                      </span>
                    ) : (
                      <span style={{ color: '#dc2626', fontWeight: 600, display: 'flex', alignItems: 'center', gap: 4 }}>
                        <Unlock className="w-3.5 h-3.5" /> Not HTTPS
                      </span>
                    )}
                  </div>
                  <div className="meta-item">
                    <AlertCircle className="w-3.5 h-3.5" />
                    <span className="meta-label">Scan Time</span>
                    <span className="meta-value">{new Date(result.scan_timestamp).toLocaleString()}</span>
                  </div>
                  <div className="meta-item">
                    <Shield className="w-3.5 h-3.5" />
                    <span className="meta-label">Overall Risk</span>
                    <RiskBadge level={risk} />
                  </div>
                </div>
              </div>

              {/* Two-column layout for findings */}
              <div className="detail-columns">
                {/* Left column */}
                <div className="detail-col-left">

                  {/* Missing Security Headers */}
                  <div className="detail-card">
                    <div className="card-header">
                      <div className="card-header-left">
                        <ShieldAlert className="w-5 h-5 text-red-500" />
                        <h3 className="card-title">Missing Security Headers</h3>
                      </div>
                      <span className="card-count">{result.missing_security_headers.length} missing</span>
                    </div>
                    <div style={{ padding: '12px 24px 20px' }}>
                      {result.missing_security_headers.length === 0 ? (
                        <div style={{ display: 'flex', alignItems: 'center', gap: 8, color: '#16a34a' }}>
                          <CheckCircle2 className="w-4 h-4" />
                          <span style={{ fontSize: '0.875rem' }}>All recommended security headers are present</span>
                        </div>
                      ) : (
                        <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>
                          {result.missing_security_headers.map(h => (
                            <code
                              key={h}
                              style={{
                                background: '#fef2f2',
                                color: '#dc2626',
                                border: '1px solid #fecaca',
                                borderRadius: 6,
                                padding: '4px 10px',
                                fontSize: '0.78rem',
                                fontWeight: 600,
                              }}
                            >
                              {h}
                            </code>
                          ))}
                        </div>
                      )}
                    </div>
                  </div>

                  {/* CORS Warning */}
                  {result.open_cors && (
                    <div className="detail-card" style={{ borderLeft: '3px solid #d97706' }}>
                      <div className="card-header">
                        <div className="card-header-left">
                          <AlertTriangle className="w-5 h-5 text-amber-500" />
                          <h3 className="card-title">Open CORS Misconfiguration</h3>
                        </div>
                        <span className="risk-badge medium">MEDIUM</span>
                      </div>
                      <div style={{ padding: '12px 24px 20px' }}>
                        <p style={{ fontSize: '0.875rem', color: '#64748b', lineHeight: 1.6 }}>
                          The <code>Access-Control-Allow-Origin</code> header is set to <code>*</code>,
                          allowing any website to make cross-origin requests to this API. This can expose
                          sensitive data to malicious sites.
                        </p>
                      </div>
                    </div>
                  )}

                  {/* Server Header Leak */}
                  {result.server_header_leak && (
                    <div className="detail-card" style={{ borderLeft: '3px solid #7c3aed' }}>
                      <div className="card-header">
                        <div className="card-header-left">
                          <Server className="w-5 h-5 text-purple-500" />
                          <h3 className="card-title">Server Technology Exposed</h3>
                        </div>
                        <span className="risk-badge medium">INFO LEAK</span>
                      </div>
                      <div style={{ padding: '12px 24px 20px' }}>
                        <p style={{ fontSize: '0.875rem', color: '#64748b', marginBottom: 10 }}>
                          The <code>Server</code> response header reveals the underlying technology:
                        </p>
                        <code
                          style={{
                            display: 'inline-block',
                            background: '#f5f3ff',
                            color: '#7c3aed',
                            border: '1px solid #ddd6fe',
                            borderRadius: 6,
                            padding: '4px 12px',
                            fontSize: '0.85rem',
                          }}
                        >
                          {result.server_header_leak}
                        </code>
                        <p style={{ fontSize: '0.8rem', color: '#94a3b8', marginTop: 8 }}>
                          Attackers can use this to target known vulnerabilities for this software version.
                        </p>
                      </div>
                    </div>
                  )}

                </div>

                {/* Right column */}
                <div className="detail-col-right">

                  {/* Discovered Endpoints */}
                  <div className="detail-card">
                    <div className="card-header">
                      <div className="card-header-left">
                        <Search className="w-5 h-5 text-blue-500" />
                        <h3 className="card-title">Discovered Endpoints</h3>
                      </div>
                      <span className="card-count">{result.discovered_endpoints.length} found</span>
                    </div>
                    {result.discovered_endpoints.length === 0 ? (
                      <div style={{ padding: '12px 24px 20px', display: 'flex', alignItems: 'center', gap: 8, color: '#16a34a' }}>
                        <CheckCircle2 className="w-4 h-4" />
                        <span style={{ fontSize: '0.875rem' }}>No sensitive endpoints discovered during probing</span>
                      </div>
                    ) : (
                      <div className="table-wrapper">
                        <table className="data-table">
                          <thead>
                            <tr>
                              <th>Path</th>
                              <th>Status</th>
                              <th>Classification</th>
                              <th>Severity</th>
                            </tr>
                          </thead>
                          <tbody>
                            {result.discovered_endpoints.map(ep => (
                              <tr key={ep.path} className="table-row">
                                <td><code style={{ fontSize: '0.8rem' }}>{ep.path}</code></td>
                                <td className="mono">{ep.status_code}</td>
                                <td>
                                  <span style={{ fontSize: '0.78rem', color: '#475569' }}>
                                    {ep.classification}
                                  </span>
                                </td>
                                <td>
                                  <span className={SEVERITY_STYLE[ep.severity]?.cls || 'risk-badge low'}>
                                    {ep.severity}
                                  </span>
                                </td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    )}
                  </div>

                  {/* Summary */}
                  {result.summary && (
                    <div className="detail-card">
                      <div className="card-header">
                        <div className="card-header-left">
                          <AlertCircle className="w-5 h-5 text-blue-500" />
                          <h3 className="card-title">Scan Narrative</h3>
                        </div>
                      </div>
                      <div style={{ padding: '12px 24px 20px' }}>
                        <p style={{ fontSize: '0.875rem', color: '#475569', lineHeight: 1.6 }}>
                          {result.summary}
                        </p>
                      </div>
                    </div>
                  )}

                </div>
              </div>
            </>
          )}
        </>
      )}
    </div>
  );
}
