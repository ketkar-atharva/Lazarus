import React, { useState, useEffect, useCallback } from 'react';
import axios from 'axios';
import { ShieldX, Terminal, Crosshair, Target, Eye, ExternalLink, Activity, Info, Clock, ArrowRight } from 'lucide-react';
import './Honeypots.css';

const API_BASE = 'http://localhost:8000';

export default function Honeypots() {
  const [activeTab, setActiveTab] = useState('activity');
  const [deployedTraps, setDeployedTraps] = useState([]);
  const [activityLog, setActivityLog] = useState([]);
  const [seenHits, setSeenHits] = useState(new Set());
  const [expandedRows, setExpandedRows] = useState(new Set());

  // Fetch data
  const fetchData = useCallback(async () => {
    try {
      const [trapsRes, activityRes] = await Promise.all([
        axios.get(`${API_BASE}/api/honeypots`).catch(() => ({ data: [] })),
        axios.get(`${API_BASE}/api/honeypots/activity`).catch(() => ({ data: [] }))
      ]);
      setDeployedTraps(trapsRes.data);
      setActivityLog(activityRes.data);
    } catch (err) {
      console.error('Failed to fetch honeypot data', err);
    }
  }, []);

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 30000); // Poll every 30s
    return () => clearInterval(interval);
  }, [fetchData]);

  const toggleRow = (index, timestamp) => {
    const newExpanded = new Set(expandedRows);
    if (newExpanded.has(index)) {
      newExpanded.delete(index);
    } else {
      newExpanded.add(index);
      setSeenHits(prev => new Set(prev).add(timestamp));
    }
    setExpandedRows(newExpanded);
  };

  // Metrics Logic
  const oneHourAgo = new Date(Date.now() - 3600 * 1000);
  const oneDayAgo = new Date(Date.now() - 24 * 3600 * 1000);
  
  const hitsTodayCount = activityLog.filter(log => new Date(log.timestamp || log.triggered_at) > oneDayAgo).length;
  const uniqueIpsMap = new Set(
    activityLog
      .filter(log => new Date(log.timestamp || log.triggered_at) > oneDayAgo)
      .map(log => log.ip || log.detail?.match(/IP:\s*([\d.]+)/)?.[1] || 'Unknown')
  );
  
  const hasNewHits = activityLog.some(log => {
    const ts = log.timestamp || log.triggered_at;
    return new Date(ts) > oneHourAgo && !seenHits.has(ts);
  });

  // Calculate hit counts per trap
  const hitCountsByPath = {};
  activityLog.forEach(log => {
      const path = log.target || log.path;
      if (path) {
          hitCountsByPath[path] = (hitCountsByPath[path] || 0) + 1;
      }
  });

  const timeSince = (isoString) => {
    if (!isoString) return 'Unknown';
    const seconds = Math.floor((new Date() - new Date(isoString)) / 1000);
    if (seconds < 60) return `${seconds}s ago`;
    if (seconds < 3600) return `${Math.floor(seconds / 60)}m ago`;
    if (seconds < 86400) return `${Math.floor(seconds / 3600)}h ago`;
    return `${Math.floor(seconds / 86400)}d ago`;
  };

  return (
    <div className="hp-container">
      {/* Header & Metrics */}
      <div className="hp-header">
        <div className="hp-title-section">
          <Crosshair className="w-8 h-8 text-blue-600" />
          <div>
            <h1 className="hp-title">Honeypot Dashboard</h1>
            <p className="hp-subtitle">Manage deception routes and track unauthorized probing attempts.</p>
          </div>
        </div>
        <div className="hp-metrics-row">
          <div className="hp-metric-card">
            <span className="hp-metric-value text-red-400">{hitsTodayCount}</span>
            <span className="hp-metric-label">Hits Today</span>
          </div>
          <div className="hp-metric-card">
            <span className="hp-metric-value text-emerald-400">{deployedTraps.length}</span>
            <span className="hp-metric-label">Active Traps</span>
          </div>
          <div className="hp-metric-card">
            <span className="hp-metric-value text-amber-400">{uniqueIpsMap.size}</span>
            <span className="hp-metric-label">Unique IPs Today</span>
          </div>
        </div>
      </div>

      {hasNewHits && (
        <div className="hp-alert-banner">
          <div className="flex items-center gap-3">
             <div className="hp-pulse-dot" />
             <span className="font-semibold text-red-100">Critical: New honeypot intrusions detected in the last hour!</span>
          </div>
        </div>
      )}

      {/* Tabs */}
      <div className="hp-tabs">
        <button 
          className={`hp-tab ${activeTab === 'activity' ? 'active' : ''}`}
          onClick={() => setActiveTab('activity')}
        >
          <Activity className="w-4 h-4" /> Activity Log
        </button>
        <button 
          className={`hp-tab ${activeTab === 'traps' ? 'active' : ''}`}
          onClick={() => setActiveTab('traps')}
        >
          <Target className="w-4 h-4" /> Active Traps
        </button>
        <button 
          className={`hp-tab ${activeTab === 'preview' ? 'active' : ''}`}
          onClick={() => setActiveTab('preview')}
        >
          <Eye className="w-4 h-4" /> Decoy Preview
        </button>
      </div>

      {/* Content Area */}
      <div className="hp-content">
        
        {/* TAB: ACTIVITY LOG */}
        {activeTab === 'activity' && (
          <div className="hp-tab-panel">
            {activityLog.length === 0 ? (
              <div className="hp-empty-state">
                <ShieldX className="w-12 h-12 text-slate-500 mb-4" />
                <h3>No Recent Activity</h3>
                <p>Traps are armed but no hits have been recorded yet.</p>
              </div>
            ) : (
              <div className="hp-activity-list">
                {activityLog.map((log, idx) => {
                  const ts = log.timestamp || log.triggered_at || new Date().toISOString();
                  const isNew = new Date(ts) > oneHourAgo && !seenHits.has(ts);
                  const isExpanded = expandedRows.has(idx);
                  const path = log.target || log.path || 'Unknown API';
                  
                  // Extract detail properties normally saved as text or JSON
                  let ip = log.ip || "Unknown IP";
                  let method = log.method || "GET";
                  let ua = log.user_agent || "";
                  let body = log.body || "{}";
                  let responseSent = log.response_sent || "{\"status\": \"error\"}";

                  // Attempt to parse out from detail if action was just a logged string
                  if (log.detail && typeof log.detail === 'string') {
                     const ipMatch = log.detail.match(/From IP:\s*([\d.]+)/);
                     if (ipMatch) ip = ipMatch[1];
                  }

                  return (
                    <div key={idx} className={`hp-log-row ${isExpanded ? 'expanded' : ''} ${isNew ? 'new-hit' : ''}`}>
                      <div className="hp-log-header" onClick={() => toggleRow(idx, ts)}>
                        <div className="flex gap-4 items-center flex-1">
                           <span className="hp-method-badge">{method}</span>
                           <span className="hp-log-path font-mono text-sm">{path}</span>
                           {isNew && <span className="hp-new-badge">NEW</span>}
                        </div>
                        <div className="flex items-center gap-6 text-sm text-slate-400">
                           <span className="flex items-center gap-1"><Clock className="w-3 h-3" /> {timeSince(ts)}</span>
                           <span>{ip}</span>
                        </div>
                      </div>
                      
                      {isExpanded && (
                        <div className="hp-log-details">
                          <div className="hp-detail-grid">
                            <div className="hp-detail-group">
                              <label>Source IP</label>
                              <div className="hp-value mono">{ip}</div>
                            </div>
                            <div className="hp-detail-group">
                              <label>User Agent</label>
                              <div className="hp-value text-xs">{ua || 'Unknown'}</div>
                            </div>
                          </div>
                          <div className="hp-detail-grid mt-4">
                            <div className="hp-detail-group">
                              <label>Request Body</label>
                              <pre className="hp-code-block">{typeof body === 'string' ? body : JSON.stringify(body, null, 2)}</pre>
                            </div>
                            <div className="hp-detail-group">
                              <label>Fake Response Sent (HTTP 200)</label>
                              <pre className="hp-code-block success">{typeof responseSent === 'string' ? responseSent : JSON.stringify(responseSent, null, 2)}</pre>
                            </div>
                          </div>
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        )}

        {/* TAB: ACTIVE TRAPS */}
        {activeTab === 'traps' && (
          <div className="hp-tab-panel">
             <div className="hp-traps-grid">
               {deployedTraps.length === 0 ? (
                 <div className="col-span-full hp-empty-state">
                   <Target className="w-12 h-12 text-slate-500 mb-4" />
                   <h3>No Active Traps</h3>
                   <p>Navigate to an API in the dashboard to deploy a honeypot.</p>
                 </div>
               ) : (
                 deployedTraps.map(trap => {
                   const count = hitCountsByPath[trap] || 0;
                   return (
                     <div key={trap} className="hp-trap-card">
                       <div className="flex justify-between items-start mb-3">
                         <span className="hp-trap-badge">Active</span>
                         <span className="hp-trap-counts" title="Total Hits"><Crosshair className="w-3 h-3 inline mr-1 text-red-400" /> {count}</span>
                       </div>
                       <code className="text-sm text-indigo-300 break-all">{trap}</code>
                     </div>
                   );
                 })
               )}
             </div>
          </div>
        )}

        {/* TAB: DECOY PREVIEW */}
        {activeTab === 'preview' && (
          <div className="hp-tab-panel flex flex-col items-center">
            <div className="hp-preview-browser">
              <div className="hp-browser-header">
                <span className="dot bg-red-500"></span>
                <span className="dot bg-amber-500"></span>
                <span className="dot bg-emerald-500"></span>
                <div className="hp-browser-url">
                  <ExternalLink className="w-3 h-3" />
                  https://api.lazarus.bank.internal/api/v1/internal/admin-bypass
                </div>
              </div>
              <div className="hp-browser-body">
                <pre className="hp-code-block text-sm">
                  {`{\n  "status": "ok",\n  "message": "Authenticated via Honeypot",\n  "data": {\n    "session_id": "mock_687A9F1",\n    "role": "admin"\n  }\n}`}
                </pre>
              </div>
            </div>
            
            <div className="hp-preview-note mt-6 max-w-xl text-center">
              <Info className="w-5 h-5 incline-block mx-auto mb-2 text-indigo-400" />
              <p className="text-slate-400 text-sm">
                <strong>Attacker Perspective:</strong> The deceptive service returns a 200 OK with plausible JSON structures to lead attackers on. Simultaneously, the middleware silently captures their full HTTP footprint, IP, and payloads, logging it instantly to your Activity tab.
              </p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
