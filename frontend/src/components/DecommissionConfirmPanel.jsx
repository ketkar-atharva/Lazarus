import { useState, useEffect, useRef } from 'react';
import {
  CheckCircle2,
  AlertTriangle,
  Loader2,
  Shield,
  Server,
  Copy,
  Check,
  Clock,
  Fingerprint,
  Route,
  Terminal,
} from 'lucide-react';

/**
 * DecommissionConfirmPanel
 *
 * Real-time dual-blocker confirmation panel that animates Kong gateway
 * and Lazarus middleware card states after a successful decommission.
 *
 * Props:
 *   result  – full response from POST /api/decommission
 *   apiPath – the decommissioned API path (for the curl command)
 */
export default function DecommissionConfirmPanel({ result, apiPath }) {
  const [kongState, setKongState]       = useState('pending');   // pending | confirmed | skipped
  const [mwState, setMwState]           = useState('pending');   // pending | confirmed
  const [copied, setCopied]             = useState(false);
  const curlRef = useRef(null);

  // Derive data from response (with safe defaults)
  const kong       = result?.kong       || {};
  const middleware  = result?.middleware || {};
  const timestamp  = result?.timestamp  || result?.initiated_at || new Date().toISOString();

  const kongStatus = kong.status || (result?.kong_result?.error ? 'skipped' : 'ok');
  const mwStatus   = middleware.status || 'ok';
  const pluginId   = kong.plugin_id  || result?.kong_result?.id  || 'N/A';
  const routeId    = kong.route_id   || result?.kong_result?.route?.id || 'N/A';
  const mwPath     = middleware.path  || result?.path || apiPath || '/—';

  // Staggered activation: Kong first, then middleware ~800ms later
  useEffect(() => {
    const t1 = setTimeout(() => {
      setKongState(kongStatus === 'skipped' ? 'skipped' : 'confirmed');
    }, 600);

    const t2 = setTimeout(() => {
      setMwState('confirmed');
    }, 1400);

    return () => { clearTimeout(t1); clearTimeout(t2); };
  }, [kongStatus]);

  const bothDone = kongState !== 'pending' && mwState !== 'pending';

  const handleCopy = () => {
    const cmd = curlRef.current?.textContent;
    if (cmd) {
      navigator.clipboard.writeText(cmd).then(() => {
        setCopied(true);
        setTimeout(() => setCopied(false), 2000);
      });
    }
  };

  const formattedTs = (() => {
    try {
      const d = new Date(timestamp);
      return d.toLocaleString('en-US', {
        month: 'short', day: 'numeric', year: 'numeric',
        hour: '2-digit', minute: '2-digit', second: '2-digit',
      });
    } catch { return timestamp; }
  })();

  const curlCommand = ` http://localhost:8000${mwPath}`;

  return (
    <div className="dcp-root" id="decommission-confirm-panel">
      {/* ── Title ── */}
      <div className="dcp-title-row">
        <Shield className="w-5 h-5" style={{ color: '#16a34a' }} />
        <h4 className="dcp-title">Blocker Confirmation</h4>
      </div>

      {/* ── Dual Cards ── */}
      <div className="dcp-cards">
        {/* Kong Card */}
        <div className={`dcp-card ${kongState}`} id="dcp-kong-card">
          <div className="dcp-card-icon-wrap kong">
            <Server className="w-5 h-5" />
          </div>
          <p className="dcp-card-label">Kong Gateway</p>
          <div className="dcp-card-status">
            {kongState === 'pending' && (
              <Loader2 className="w-4 h-4 animate-spin dcp-spinner" />
            )}
            {kongState === 'confirmed' && (
              <span className="dcp-badge green">
                <CheckCircle2 className="w-3.5 h-3.5" /> Blocked
              </span>
            )}
            {kongState === 'skipped' && (
              <span className="dcp-badge amber">
                <AlertTriangle className="w-3.5 h-3.5" /> Kong offline — middleware active
              </span>
            )}
          </div>
        </div>

        {/* Middleware Card */}
        <div className={`dcp-card ${mwState}`} id="dcp-mw-card">
          <div className="dcp-card-icon-wrap mw">
            <Shield className="w-5 h-5" />
          </div>
          <p className="dcp-card-label">Lazarus Middleware</p>
          <div className="dcp-card-status">
            {mwState === 'pending' ? (
              <Loader2 className="w-4 h-4 animate-spin dcp-spinner" />
            ) : (
              <span className="dcp-badge green">
                <CheckCircle2 className="w-3.5 h-3.5" /> Active
              </span>
            )}
          </div>
        </div>
      </div>

      {/* ── Audit Receipt (appears after both cards resolve) ── */}
      {bothDone && (
        <div className="dcp-audit" id="dcp-audit-receipt">
          <p className="dcp-audit-heading">Audit Receipt</p>

          <div className="dcp-audit-grid">
            <div className="dcp-audit-item">
              <Fingerprint className="w-3.5 h-3.5" />
              <span className="dcp-audit-label">Plugin ID</span>
              <code className="dcp-audit-value">{pluginId}</code>
            </div>
            <div className="dcp-audit-item">
              <Route className="w-3.5 h-3.5" />
              <span className="dcp-audit-label">Route ID</span>
              <code className="dcp-audit-value">{routeId}</code>
            </div>
            <div className="dcp-audit-item">
              <Clock className="w-3.5 h-3.5" />
              <span className="dcp-audit-label">Timestamp</span>
              <code className="dcp-audit-value">{formattedTs}</code>
            </div>
          </div>

          {/* Verify Command */}
          <div className="dcp-verify-cmd">
            <div className="dcp-cmd-header">
              <Terminal className="w-3.5 h-3.5" />
              <span>Verify</span>
              <button className="dcp-copy-btn" onClick={handleCopy} title="Copy to clipboard">
                {copied
                  ? <><Check className="w-3 h-3" /> Copied</>
                  : <><Copy className="w-3 h-3" /> Copy</>
                }
              </button>
            </div>
            <pre className="dcp-cmd-code" ref={curlRef}>{curlCommand}</pre>
          </div>
        </div>
      )}
    </div>
  );
}
