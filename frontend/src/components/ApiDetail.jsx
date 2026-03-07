import { useState } from 'react';
import axios from 'axios';
import {
  ArrowLeft,
  ShieldAlert,
  Shield,
  ShieldCheck,
  ShieldX,
  Lock,
  Unlock,
  Key,
  Wifi,
  Zap,
  AlertTriangle,
  CheckCircle2,
  XCircle,
  AlertCircle,
  Clock,
  Activity,
  TrendingUp,
  Eye,
  FileWarning,
  Trash2,
  Ghost,
  Skull,
  Server,
  Database,
  Globe,
  Mail,
  RefreshCw,
} from 'lucide-react';

const API_BASE = 'http://localhost:8000';

/* ── Security Check Row ── */
const SecurityCheck = ({ label, data }) => {
  if (!data) return null;
  const statusIcon = {
    pass: <CheckCircle2 className="w-4 h-4 text-green-500" />,
    warning: <AlertCircle className="w-4 h-4 text-amber-500" />,
    fail: <XCircle className="w-4 h-4 text-red-500" />,
  };
  const statusColor = {
    pass: 'check-pass',
    warning: 'check-warning',
    fail: 'check-fail',
  };

  return (
    <div className={`security-check ${statusColor[data.status]}`}>
      <div className="check-header">
        {statusIcon[data.status]}
        <span className="check-label">{label}</span>
        <span className={`check-status-badge ${data.status}`}>
          {data.status === 'pass' ? 'PASS' : data.status === 'warning' ? 'WARNING' : 'FAIL'}
        </span>
      </div>
      {data.type && <p className="check-type">{data.type || data.protocol}</p>}
      {data.protocol && !data.type && <p className="check-type">{data.protocol}</p>}
      {data.limit && <p className="check-type">Limit: {data.limit}</p>}
      {data.risk && <p className="check-type">Risk Level: {data.risk}</p>}
      <p className="check-details">{data.details}</p>
      {data.pii_fields && data.pii_fields.length > 0 && (
        <div className="pii-tags">
          {data.pii_fields.map(f => (
            <span key={f} className="pii-tag">{f}</span>
          ))}
        </div>
      )}
    </div>
  );
};

/* ── Recommendation Card ── */
const RecommendationCard = ({ rec, index }) => {
  const priorityStyles = {
    critical: { bg: '#fef2f2', border: '#fecaca', color: '#dc2626', label: '🔴 CRITICAL' },
    high: { bg: '#fff7ed', border: '#fed7aa', color: '#ea580c', label: '🟠 HIGH' },
    medium: { bg: '#fffbeb', border: '#fde68a', color: '#d97706', label: '🟡 MEDIUM' },
    low: { bg: '#f0fdf4', border: '#bbf7d0', color: '#16a34a', label: '🟢 LOW' },
    info: { bg: '#eff6ff', border: '#bfdbfe', color: '#2563eb', label: 'ℹ INFO' },
  };
  const s = priorityStyles[rec.priority] || priorityStyles.info;

  return (
    <div className="recommendation-card" style={{ borderLeft: `3px solid ${s.color}` }}>
      <div className="rec-priority" style={{ color: s.color, background: s.bg }}>{s.label}</div>
      <p className="rec-action">{rec.action}</p>
    </div>
  );
};

export default function ApiDetail({ apiId, apiPath, onBack }) {
  const [detail, setDetail] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [decommissioning, setDecommissioning] = useState(false);
  const [decommissioned, setDecommissioned] = useState(false);
  const [decommissionResult, setDecommissionResult] = useState(null);

  useState(() => {
    (async () => {
      try {
        const params = apiId && !apiId.startsWith('SHADOW-')
          ? { api_id: apiId }
          : { path: apiPath };
        const res = await axios.get(`${API_BASE}/api/detail`, { params });
        setDetail(res.data);
        // Check if already decommissioned (persisted in MongoDB)
        if (res.data.is_decommissioned && res.data.decommission_record) {
          setDecommissioned(true);
          setDecommissionResult(res.data.decommission_record);
        }
      } catch (err) {
        setError('Failed to load API details.');
        console.error(err);
      } finally {
        setLoading(false);
      }
    })();
  });

  const handleDecommission = async () => {
    if (!detail) return;
    setDecommissioning(true);
    try {
      const res = await axios.post(`${API_BASE}/api/decommission`, {
        api_id: detail.id,
        path: detail.path,
        reason: 'Security risk — decommissioned via Project Lazarus platform.',
      });
      setDecommissionResult(res.data);
      setDecommissioned(true);
    } catch (err) {
      console.error('Decommission failed:', err);
    } finally {
      setDecommissioning(false);
    }
  };

  if (loading) {
    return (
      <div className="detail-loading">
        <RefreshCw className="w-6 h-6 animate-spin text-blue-500" />
        <p>Loading API analysis...</p>
      </div>
    );
  }

  if (error || !detail) {
    return (
      <div className="detail-error">
        <AlertTriangle className="w-8 h-8 text-red-400" />
        <p>{error || 'API not found.'}</p>
        <button className="btn-back" onClick={onBack}>← Back to Dashboard</button>
      </div>
    );
  }

  const posture = detail.security_posture || {};
  const classification = detail.classification || {};
  const trafficData = detail.traffic || {};
  const score = posture.overall_score ?? 0;

  const scoreColor = score >= 80 ? '#16a34a' : score >= 50 ? '#d97706' : '#dc2626';
  const scoreLabel = score >= 80 ? 'Good' : score >= 50 ? 'Fair' : 'Critical';

  const statusColors = {
    ACTIVE: { bg: '#f0fdf4', border: '#bbf7d0', text: '#16a34a' },
    ZOMBIE: { bg: '#fffbeb', border: '#fde68a', text: '#d97706' },
    STALE: { bg: '#f5f3ff', border: '#ddd6fe', text: '#7c3aed' },
    SHADOW: { bg: '#fef2f2', border: '#fecaca', text: '#dc2626' },
  };
  const sc = statusColors[detail.status] || statusColors.ACTIVE;

  return (
    <div className="api-detail">
      {/* Back Navigation */}
      <button className="btn-back" onClick={onBack} id="btn-back-dashboard">
        <ArrowLeft className="w-4 h-4" />
        Back to Dashboard
      </button>

      {/* API Header */}
      <div className="detail-header" style={{ borderLeft: `4px solid ${sc.text}` }}>
        <div className="detail-header-top">
          <div>
            <div className="detail-status-row">
              <span className="detail-status-badge" style={{ background: sc.bg, color: sc.text, border: `1px solid ${sc.border}` }}>
                {detail.status}
              </span>
              {posture.risk_level && (
                <span className={`risk-badge ${posture.risk_level.toLowerCase()}`}>{posture.risk_level} RISK</span>
              )}
              {decommissioned && (
                <span className="decom-badge">🔒 DECOMMISSIONED</span>
              )}
            </div>
            <h2 className="detail-title">{detail.name || detail.path}</h2>
            <p className="detail-description">{detail.description}</p>
          </div>
          <div className="detail-score-ring">
            <svg viewBox="0 0 100 100" className="score-svg">
              <circle cx="50" cy="50" r="42" fill="none" stroke="#e2e8f0" strokeWidth="8" />
              <circle
                cx="50" cy="50" r="42" fill="none"
                stroke={scoreColor} strokeWidth="8"
                strokeDasharray={`${(score / 100) * 264} 264`}
                strokeLinecap="round"
                transform="rotate(-90 50 50)"
                style={{ transition: 'stroke-dasharray 1s ease' }}
              />
            </svg>
            <div className="score-text">
              <span className="score-number" style={{ color: scoreColor }}>{score}</span>
              <span className="score-label">{scoreLabel}</span>
            </div>
          </div>
        </div>

        {/* Meta Info */}
        <div className="detail-meta-grid">
          <div className="meta-item">
            <Globe className="w-3.5 h-3.5" />
            <span className="meta-label">Path</span>
            <code className="meta-value">{detail.path}</code>
          </div>
          <div className="meta-item">
            <Activity className="w-3.5 h-3.5" />
            <span className="meta-label">Method</span>
            <span className="meta-value">{detail.method}</span>
          </div>
          <div className="meta-item">
            <Server className="w-3.5 h-3.5" />
            <span className="meta-label">Version</span>
            <span className="meta-value">{detail.version || '—'}</span>
          </div>
          <div className="meta-item">
            <Mail className="w-3.5 h-3.5" />
            <span className="meta-label">Owner</span>
            <span className="meta-value">{detail.owner || '—'}</span>
          </div>
          <div className="meta-item">
            <Clock className="w-3.5 h-3.5" />
            <span className="meta-label">Last Updated</span>
            <span className="meta-value">{detail.last_updated ? new Date(detail.last_updated).toLocaleDateString() : '—'}</span>
          </div>
          <div className="meta-item">
            <Database className="w-3.5 h-3.5" />
            <span className="meta-label">In Catalog</span>
            <span className="meta-value">{detail.is_in_catalog ? 'Yes' : 'No — Undocumented'}</span>
          </div>
        </div>
      </div>

      {/* Two-Column Layout */}
      <div className="detail-columns">
        {/* Left Column */}
        <div className="detail-col-left">
          {/* Classification Reasoning */}
          {classification.reasoning && (
            <div className="detail-card">
              <div className="card-header">
                <div className="card-header-left">
                  <Eye className="w-5 h-5 text-blue-500" />
                  <h3 className="card-title">Classification Analysis</h3>
                </div>
                <span className="card-badge" style={{ background: sc.bg, color: sc.text, border: `1px solid ${sc.border}` }}>
                  {classification.label || detail.status}
                </span>
              </div>
              <p className="classification-subtitle">
                Why this API is classified as <strong style={{ color: sc.text }}>{detail.status}</strong>:
              </p>
              <ul className="reasoning-list">
                {classification.reasoning.map((reason, i) => (
                  <li key={i} className="reasoning-item">
                    <span className="reasoning-bullet" style={{ background: sc.text }} />
                    <span>{reason}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Security Posture */}
          <div className="detail-card">
            <div className="card-header">
              <div className="card-header-left">
                <Shield className="w-5 h-5 text-blue-500" />
                <h3 className="card-title">Security Posture Assessment</h3>
              </div>
              <span className="security-score" style={{ color: scoreColor }}>{score}/100</span>
            </div>
            <div className="security-checks">
              <SecurityCheck label="Authentication" data={posture.authentication} />
              <SecurityCheck label="Encryption" data={posture.encryption} />
              <SecurityCheck label="Rate Limiting" data={posture.rate_limiting} />
              <SecurityCheck label="Data Exposure" data={posture.data_exposure} />
              <SecurityCheck label="Input Validation" data={posture.input_validation} />
            </div>
          </div>
        </div>

        {/* Right Column */}
        <div className="detail-col-right">
          {/* Traffic Analysis */}
          {trafficData && (
            <div className="detail-card">
              <div className="card-header">
                <div className="card-header-left">
                  <TrendingUp className="w-5 h-5 text-blue-500" />
                  <h3 className="card-title">Traffic Analysis</h3>
                </div>
              </div>
              <div className="traffic-stats">
                <div className="traffic-stat">
                  <span className="traffic-stat-value">{(trafficData.hit_count ?? 0).toLocaleString()}</span>
                  <span className="traffic-stat-label">Total Hits</span>
                </div>
                <div className="traffic-stat">
                  <span className="traffic-stat-value">{trafficData.avg_latency || '—'}</span>
                  <span className="traffic-stat-label">Avg Latency</span>
                </div>
                <div className="traffic-stat">
                  <span className="traffic-stat-value">{trafficData.error_rate || '—'}</span>
                  <span className="traffic-stat-label">Error Rate</span>
                </div>
              </div>
              {trafficData.response_codes && Object.keys(trafficData.response_codes).length > 0 && (
                <div className="response-codes">
                  <p className="rc-label">Response Code Distribution</p>
                  <div className="rc-bars">
                    {Object.entries(trafficData.response_codes).map(([code, count]) => {
                      const total = Object.values(trafficData.response_codes).reduce((a, b) => a + b, 0);
                      const pct = ((count / total) * 100).toFixed(1);
                      const barColor = code.startsWith('2') ? '#16a34a' : code.startsWith('4') ? '#d97706' : '#dc2626';
                      return (
                        <div key={code} className="rc-bar-row">
                          <span className="rc-code">{code}</span>
                          <div className="rc-bar-track">
                            <div className="rc-bar-fill" style={{ width: `${pct}%`, background: barColor }} />
                          </div>
                          <span className="rc-pct">{pct}%</span>
                          <span className="rc-count">{count.toLocaleString()}</span>
                        </div>
                      );
                    })}
                  </div>
                </div>
              )}
              {trafficData.request_source_ips && trafficData.request_source_ips.length > 0 && trafficData.request_source_ips[0] !== '0.0.0.0' && (
                <div className="source-ips">
                  <p className="rc-label">Source IPs</p>
                  <div className="ip-tags">
                    {trafficData.request_source_ips.map(ip => (
                      <span key={ip} className="ip-tag"><Wifi className="w-3 h-3" />{ip}</span>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Recommendations */}
          {classification.recommendations && (
            <div className="detail-card">
              <div className="card-header">
                <div className="card-header-left">
                  <Zap className="w-5 h-5 text-amber-500" />
                  <h3 className="card-title">Recommendations</h3>
                </div>
                <span className="card-count">{classification.recommendations.length} actions</span>
              </div>
              <div className="recommendations-list">
                {classification.recommendations.map((rec, i) => (
                  <RecommendationCard key={i} rec={rec} index={i} />
                ))}
              </div>
            </div>
          )}

          {/* Decommission Workflow */}
          {(detail.status === 'ZOMBIE' || detail.status === 'STALE' || detail.status === 'SHADOW') && (
            <div className="detail-card decommission-card">
              <div className="card-header">
                <div className="card-header-left">
                  <Trash2 className="w-5 h-5 text-red-500" />
                  <h3 className="card-title">Decommission Workflow</h3>
                </div>
              </div>
              {!decommissioned ? (
                <>
                  <p className="decom-desc">
                    Initiate an automated decommissioning workflow that will reroute traffic, revoke credentials,
                    update API gateway rules, and archive documentation.
                  </p>
                  <div className="decom-steps-preview">
                    <p className="decom-steps-title">Steps that will be executed:</p>
                    {[
                      'Reroute active traffic to fallback endpoint',
                      'Block endpoint at API gateway level',
                      'Remove DNS records',
                      'Revoke all associated credentials & tokens',
                      'Archive documentation',
                      'Notify stakeholders via email',
                    ].map((step, i) => (
                      <div key={i} className="decom-step-preview">
                        <span className="decom-step-num">{i + 1}</span>
                        <span>{step}</span>
                      </div>
                    ))}
                  </div>
                  <button
                    className="btn-decommission"
                    onClick={handleDecommission}
                    disabled={decommissioning}
                    id="btn-decommission"
                  >
                    {decommissioning ? (
                      <><RefreshCw className="w-4 h-4 animate-spin" /> Executing Workflow...</>
                    ) : (
                      <><Trash2 className="w-4 h-4" /> Execute Decommission Workflow</>
                    )}
                  </button>
                </>
              ) : (
                <div className="decom-success">
                  <CheckCircle2 className="w-8 h-8 text-green-500" />
                  <h4>Decommission Complete</h4>
                  <p>All steps executed successfully at {decommissionResult?.initiated_at ? new Date(decommissionResult.initiated_at).toLocaleString() : 'now'}.</p>

                  {/* Audit Trail */}
                  <div className="decom-audit-section">
                    <p className="decom-section-title">Execution Audit Trail</p>
                    <div className="decom-steps-done">
                      {decommissionResult?.steps_completed?.map((step, i) => (
                        <div key={i} className="decom-step-done">
                          <CheckCircle2 className="w-3.5 h-3.5 text-green-500" />
                          <div className="decom-step-info">
                            <span className="decom-step-action">{step.action || step}</span>
                            {step.detail && <span className="decom-step-detail">{step.detail}</span>}
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* Post Verification */}
                  {decommissionResult?.post_verification && (
                    <div className="decom-audit-section">
                      <p className="decom-section-title">Post-Decommission Verification</p>
                      <div className="decom-verify-grid">
                        <div className="decom-verify-item pass">
                          <CheckCircle2 className="w-3.5 h-3.5 text-green-500" />
                          <span>Endpoint: {decommissionResult.post_verification.endpoint_status}</span>
                        </div>
                        <div className="decom-verify-item pass">
                          <CheckCircle2 className="w-3.5 h-3.5 text-green-500" />
                          <span>DNS: {decommissionResult.post_verification.dns_resolved ? 'Still active ⚠' : 'Removed ✓'}</span>
                        </div>
                        <div className="decom-verify-item pass">
                          <CheckCircle2 className="w-3.5 h-3.5 text-green-500" />
                          <span>Tokens revoked: {(decommissionResult.post_verification.tokens_revoked || 0).toLocaleString()}</span>
                        </div>
                        <div className="decom-verify-item pass">
                          <CheckCircle2 className="w-3.5 h-3.5 text-green-500" />
                          <span>Gateway rule: {decommissionResult.post_verification.gateway_rule_active ? 'Active ✓' : 'Inactive ⚠'}</span>
                        </div>
                      </div>
                      <div className="decom-verify-result">
                        <Shield className="w-4 h-4" />
                        <span>{decommissionResult.post_verification.result}</span>
                      </div>
                    </div>
                  )}

                  {/* Compliance Summary */}
                  {decommissionResult?.compliance_summary && (
                    <div className="decom-audit-section">
                      <p className="decom-section-title">Compliance Summary</p>
                      <div className="decom-compliance-rows">
                        <div className="decom-compliance-row">
                          <span className="dcr-label">Regulation</span>
                          <span className="dcr-value">{decommissionResult.compliance_summary.regulation}</span>
                        </div>
                        <div className="decom-compliance-row">
                          <span className="dcr-label">Risk Before</span>
                          <span className="dcr-value dcr-red">{decommissionResult.compliance_summary.risk_before}</span>
                        </div>
                        <div className="decom-compliance-row">
                          <span className="dcr-label">Risk After</span>
                          <span className="dcr-value dcr-green">{decommissionResult.compliance_summary.risk_after}</span>
                        </div>
                        <div className="decom-compliance-row">
                          <span className="dcr-label">Audit Ready</span>
                          <span className="dcr-value dcr-green">{decommissionResult.compliance_summary.audit_ready ? '✓ Yes' : '✗ No'}</span>
                        </div>
                      </div>
                    </div>
                  )}

                  <p className="decom-report-hint">→ View the full audit report in the <strong>Reports</strong> page in the sidebar.</p>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
