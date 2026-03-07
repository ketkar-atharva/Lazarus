import { useState, useEffect } from 'react';
import axios from 'axios';
import {
  FileText,
  CheckCircle2,
  XCircle,
  Clock,
  Shield,
  AlertTriangle,
  RefreshCw,
  Download,
  Mail,
  Hash,
  User,
  Wifi,
  Lock,
  Eye,
  BarChart3,
  ArrowRight,
} from 'lucide-react';

const API_BASE = 'http://localhost:8000';

export default function Reports() {
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedLog, setSelectedLog] = useState(null);

  useEffect(() => {
    (async () => {
      try {
        const res = await axios.get(`${API_BASE}/api/decommission-log`);
        setLogs(res.data);
        if (res.data.length > 0) setSelectedLog(res.data[0]);
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  if (loading) {
    return (
      <div className="detail-loading">
        <RefreshCw className="w-6 h-6 animate-spin text-blue-500" />
        <p>Loading reports...</p>
      </div>
    );
  }

  if (logs.length === 0) {
    return (
      <div className="reports-content">
        <div className="page-header">
          <div>
            <h2 className="page-title">Audit & Compliance Reports</h2>
            <p className="page-subtitle">Post-decommission evidence and regulatory compliance documentation</p>
          </div>
        </div>
        <div className="empty-reports">
          <FileText className="w-12 h-12 text-gray-300" />
          <h3>No Decommission Reports Yet</h3>
          <p>Reports will appear here after you execute a Decommission Workflow on a Zombie, Shadow, or Stale API from the API Detail page.</p>
        </div>
      </div>
    );
  }

  const log = selectedLog || logs[0];
  const steps = log.steps_completed || [];
  const verify = log.post_verification || {};
  const notifs = log.stakeholder_notifications || [];
  const compliance = log.compliance_summary || {};

  return (
    <div className="reports-content">
      {/* Page Header */}
      <div className="page-header">
        <div>
          <h2 className="page-title">Audit & Compliance Reports</h2>
          <p className="page-subtitle">Post-decommission evidence for regulatory compliance (RBI / PCI-DSS)</p>
        </div>
        <div className="header-live-badge" style={{ background: '#f0fdf4', borderColor: '#bbf7d0', color: '#16a34a' }}>
          <Shield className="w-4 h-4" />
          <span>{logs.length} Report{logs.length !== 1 ? 's' : ''}</span>
        </div>
      </div>

      {/* Report Selector (if multiple) */}
      {logs.length > 1 && (
        <div className="report-selector">
          {logs.map((l, i) => (
            <button
              key={i}
              className={`report-selector-item ${selectedLog === l ? 'active' : ''}`}
              onClick={() => setSelectedLog(l)}
            >
              <span className="report-selector-path">{l.path}</span>
              <span className="report-selector-date">{new Date(l.initiated_at || l.timestamp).toLocaleDateString()}</span>
            </button>
          ))}
        </div>
      )}

      {/* Report Header Card */}
      <div className="detail-card report-header-card">
        <div className="card-header">
          <div className="card-header-left">
            <FileText className="w-5 h-5 text-blue-500" />
            <h3 className="card-title">Decommission Compliance Report</h3>
          </div>
          <span className="report-status-pill">
            <CheckCircle2 className="w-3.5 h-3.5" /> Audit Ready
          </span>
        </div>
        <div className="report-meta-grid">
          <div className="report-meta">
            <span className="report-meta-label">API Path</span>
            <code className="report-meta-value">{log.path}</code>
          </div>
          <div className="report-meta">
            <span className="report-meta-label">API ID</span>
            <span className="report-meta-value">{log.api_id}</span>
          </div>
          <div className="report-meta">
            <span className="report-meta-label">Operator</span>
            <span className="report-meta-value">{log.operator || 'admin@lazarus'}</span>
          </div>
          <div className="report-meta">
            <span className="report-meta-label">Approval</span>
            <span className="report-meta-value">{log.approval || 'Auto-approved'}</span>
          </div>
          <div className="report-meta">
            <span className="report-meta-label">Initiated</span>
            <span className="report-meta-value">{log.initiated_at ? new Date(log.initiated_at).toLocaleString() : '—'}</span>
          </div>
          <div className="report-meta">
            <span className="report-meta-label">Completed</span>
            <span className="report-meta-value">{log.completed_at ? new Date(log.completed_at).toLocaleString() : '—'}</span>
          </div>
        </div>
      </div>

      {/* Two Columns */}
      <div className="report-columns">
        {/* Left: Execution Audit Trail */}
        <div className="detail-card">
          <div className="card-header">
            <div className="card-header-left">
              <BarChart3 className="w-5 h-5 text-blue-500" />
              <h3 className="card-title">Execution Audit Trail</h3>
            </div>
            <span className="card-count">{steps.length} steps</span>
          </div>
          <div className="audit-trail">
            {steps.map((step, i) => (
              <div key={i} className="audit-step">
                <div className="audit-step-left">
                  <div className="audit-step-icon success">
                    <CheckCircle2 className="w-4 h-4" />
                  </div>
                  {i < steps.length - 1 && <div className="audit-step-line" />}
                </div>
                <div className="audit-step-content">
                  <div className="audit-step-header">
                    <span className="audit-step-action">{step.action}</span>
                    <span className="audit-step-badge success">SUCCESS</span>
                  </div>
                  <p className="audit-step-detail">{step.detail}</p>
                  <span className="audit-step-time">
                    <Clock className="w-3 h-3" />
                    {new Date(step.timestamp).toLocaleTimeString()}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Right: Verification + Compliance */}
        <div>
          {/* Post-Decommission Verification */}
          <div className="detail-card">
            <div className="card-header">
              <div className="card-header-left">
                <Shield className="w-5 h-5 text-green-500" />
                <h3 className="card-title">Post-Decommission Verification</h3>
              </div>
              <span className="report-status-pill">
                <CheckCircle2 className="w-3.5 h-3.5" /> Verified
              </span>
            </div>
            <div className="verify-checks">
              <div className="verify-row pass">
                <CheckCircle2 className="w-4 h-4 text-green-500" />
                <span className="verify-label">Endpoint Status</span>
                <span className="verify-value">{verify.endpoint_status || 'BLOCKED'}</span>
              </div>
              <div className={`verify-row ${!verify.dns_resolved ? 'pass' : 'fail'}`}>
                {!verify.dns_resolved
                  ? <CheckCircle2 className="w-4 h-4 text-green-500" />
                  : <XCircle className="w-4 h-4 text-red-500" />}
                <span className="verify-label">DNS Resolution</span>
                <span className="verify-value">{verify.dns_resolved ? 'Still Active ⚠' : 'Removed ✓'}</span>
              </div>
              <div className="verify-row pass">
                <CheckCircle2 className="w-4 h-4 text-green-500" />
                <span className="verify-label">Active Tokens</span>
                <span className="verify-value">{verify.tokens_active ?? 0} remaining ({(verify.tokens_revoked ?? 0).toLocaleString()} revoked)</span>
              </div>
              <div className="verify-row pass">
                <CheckCircle2 className="w-4 h-4 text-green-500" />
                <span className="verify-label">Gateway Rule</span>
                <span className="verify-value">{verify.gateway_rule_active ? 'Active — blocking traffic' : 'Not active'}</span>
              </div>
              <div className="verify-result">
                <CheckCircle2 className="w-5 h-5 text-green-500" />
                <span>{verify.result || 'VERIFIED'}</span>
              </div>
            </div>
          </div>

          {/* Compliance Summary */}
          <div className="detail-card">
            <div className="card-header">
              <div className="card-header-left">
                <Lock className="w-5 h-5 text-blue-500" />
                <h3 className="card-title">Regulatory Compliance</h3>
              </div>
            </div>
            <div className="compliance-body">
              <div className="compliance-row">
                <span className="compliance-label">Framework</span>
                <span className="compliance-value">{compliance.regulation || 'RBI / PCI-DSS'}</span>
              </div>
              <div className="compliance-row">
                <span className="compliance-label">Risk Before</span>
                <span className="compliance-value risk-critical">{compliance.risk_before || 'CRITICAL'}</span>
              </div>
              <div className="compliance-row">
                <span className="compliance-label">Risk After</span>
                <span className="compliance-value risk-green">{compliance.risk_after || 'REMEDIATED'}</span>
              </div>
              <div className="compliance-row">
                <span className="compliance-label">Evidence Chain</span>
                <span className="compliance-value">{compliance.evidence_chain || 'Complete'}</span>
              </div>
              <div className="compliance-row">
                <span className="compliance-label">Audit Ready</span>
                <span className={`compliance-value ${compliance.audit_ready ? 'risk-green' : 'risk-critical'}`}>
                  {compliance.audit_ready ? '✓ Yes — ready for auditor review' : '✗ Not ready'}
                </span>
              </div>
            </div>
          </div>

          {/* Stakeholder Notifications */}
          <div className="detail-card">
            <div className="card-header">
              <div className="card-header-left">
                <Mail className="w-5 h-5 text-blue-500" />
                <h3 className="card-title">Stakeholder Notifications</h3>
              </div>
              <span className="card-count">{notifs.length} sent</span>
            </div>
            <div className="notif-list">
              {notifs.map((n, i) => (
                <div key={i} className="notif-row">
                  <CheckCircle2 className="w-3.5 h-3.5 text-green-500" />
                  <span className="notif-recipient">{n.recipient}</span>
                  <span className="notif-channel">{n.channel}</span>
                  <span className="notif-status delivered">{n.status}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
