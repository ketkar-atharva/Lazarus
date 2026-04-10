import { useState, useRef, useCallback } from 'react';
import {
  Upload, FileText, Download, CheckCircle2, AlertTriangle,
  X, Skull, Ghost, Clock, Zap, RefreshCw, Eye,
} from 'lucide-react';
import api from '../api';

const STATUS_META = {
  zombie:  { color: '#d97706', bg: 'rgba(217,119,6,0.12)',  border: 'rgba(217,119,6,0.25)',  icon: Skull,  label: 'Zombie'  },
  shadow:  { color: '#dc2626', bg: 'rgba(220,38,38,0.12)',   border: 'rgba(220,38,38,0.25)',   icon: Ghost,  label: 'Shadow'  },
  stale:   { color: '#7c3aed', bg: 'rgba(124,58,237,0.12)',  border: 'rgba(124,58,237,0.25)', icon: Clock,  label: 'Stale'   },
  active:  { color: '#16a34a', bg: 'rgba(22,163,74,0.12)',   border: 'rgba(22,163,74,0.25)',  icon: CheckCircle2, label: 'Active'  },
};

export default function CsvUpload() {
  const [dragging, setDragging] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState('');
  const [previewRows, setPreviewRows] = useState([]);
  const [previewHeaders, setPreviewHeaders] = useState([]);
  const [toast, setToast] = useState(null);
  const fileInputRef = useRef(null);

  const showToast = (msg, type = 'success') => {
    setToast({ msg, type });
    setTimeout(() => setToast(null), 5000);
  };

  const parsePreview = (file) => {
    const reader = new FileReader();
    reader.onload = (e) => {
      const lines = e.target.result.split('\n').filter(Boolean);
      if (lines.length < 2) return;
      const headers = lines[0].split(',').map(h => h.trim().replace(/^"|"$/g, ''));
      const rows = lines.slice(1, 6).map(line => {
        const vals = line.split(',').map(v => v.trim().replace(/^"|"$/g, ''));
        return Object.fromEntries(headers.map((h, i) => [h, vals[i] ?? '']));
      });
      setPreviewHeaders(headers);
      setPreviewRows(rows);
    };
    reader.readAsText(file);
  };

  const handleUpload = useCallback(async (file) => {
    if (!file) return;
    if (!file.name.endsWith('.csv')) {
      setError('Only .csv files are accepted.');
      return;
    }

    setError('');
    setResult(null);
    setUploading(true);
    parsePreview(file);

    const formData = new FormData();
    formData.append('file', file);

    try {
      const res = await api.post('/catalog/upload', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
      const data = res.data;
      setResult(data);

      const { total, classification_summary: cs } = data;
      const parts = [];
      if (cs?.zombie > 0)  parts.push(`${cs.zombie} zombie`);
      if (cs?.shadow > 0)  parts.push(`${cs.shadow} shadow`);
      if (cs?.stale > 0)   parts.push(`${cs.stale} stale`);
      if (cs?.active > 0)  parts.push(`${cs.active} active`);

      const msg = `Uploaded ${total} APIs${parts.length ? ' — ' + parts.join(', ') + ' detected' : ''}`;
      showToast(msg, 'success');
    } catch (err) {
      const msg = err.response?.data?.detail?.detail
        || err.response?.data?.detail
        || 'Upload failed. Please try again.';
      setError(typeof msg === 'string' ? msg : JSON.stringify(msg));
      showToast('Upload failed.', 'error');
    } finally {
      setUploading(false);
    }
  }, []);

  const onDrop = (e) => {
    e.preventDefault();
    setDragging(false);
    const file = e.dataTransfer.files[0];
    if (file) handleUpload(file);
  };

  const onFileChange = (e) => {
    const file = e.target.files[0];
    if (file) handleUpload(file);
    e.target.value = '';
  };

  const downloadSample = async () => {
    try {
      const res = await api.get('/catalog/sample', { responseType: 'blob' });
      const url = URL.createObjectURL(res.data);
      const a = document.createElement('a');
      a.href = url;
      a.download = 'api_catalog_template.csv';
      a.click();
      URL.revokeObjectURL(url);
    } catch {
      setError('Failed to download sample template.');
    }
  };

  const exportCatalog = async () => {
    try {
      const res = await api.get('/catalog/export', { responseType: 'blob' });
      const url = URL.createObjectURL(res.data);
      const a = document.createElement('a');
      a.href = url;
      a.download = 'api_catalog_export.csv';
      a.click();
      URL.revokeObjectURL(url);
    } catch {
      setError('No catalog data to export yet. Upload a CSV first.');
    }
  };

  const cs = result?.classification_summary || {};

  return (
    <div className="dashboard-content">
      {/* Toast */}
      {toast && (
        <div className={`csv-toast ${toast.type}`}>
          {toast.type === 'success'
            ? <CheckCircle2 className="w-4 h-4" />
            : <AlertTriangle className="w-4 h-4" />}
          <span>{toast.msg}</span>
          <button onClick={() => setToast(null)}><X className="w-4 h-4" /></button>
        </div>
      )}

      {/* Header */}
      <div className="page-header">
        <div>
          <h2 className="page-title">API Catalog</h2>
          <p className="page-subtitle">Upload a CSV with your API URLs — Lazarus probes each one live and classifies it automatically</p>
        </div>
        <div style={{ display: 'flex', gap: '10px' }}>
          <button className="btn-secondary" onClick={downloadSample} id="download-sample-csv">
            <Download className="w-4 h-4" /> Sample CSV
          </button>
          <button className="btn-secondary" onClick={exportCatalog} id="export-catalog-csv">
            <FileText className="w-4 h-4" /> Export Catalog
          </button>
        </div>
      </div>

      {/* Drop Zone */}
      <div
        className={`csv-dropzone ${dragging ? 'dragging' : ''} ${uploading ? 'uploading' : ''}`}
        onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
        onDragLeave={() => setDragging(false)}
        onDrop={onDrop}
        onClick={() => !uploading && fileInputRef.current?.click()}
        id="csv-dropzone"
      >
        <input
          ref={fileInputRef}
          type="file"
          accept=".csv"
          style={{ display: 'none' }}
          onChange={onFileChange}
          id="csv-file-input"
        />
        <div className="csv-dropzone-inner">
          {uploading ? (
            <>
              <div className="csv-spinner" />
              <p className="csv-drop-title">Probing APIs live… this may take a moment</p>
              <p className="csv-drop-sub">Lazarus is testing each endpoint in real time</p>
            </>
          ) : (
            <>
              <div className="csv-drop-icon">
                <Upload className="w-8 h-8" />
              </div>
              <p className="csv-drop-title">
                {dragging ? 'Drop your CSV here' : 'Drag & drop your API probe CSV'}
              </p>
              <p className="csv-drop-sub">Required columns: api_id · url · method · (optional) last_traffic_at</p>
            </>
          )}
        </div>
      </div>

      {/* Error */}
      {error && (
        <div className="csv-error-banner">
          <AlertTriangle className="w-4 h-4" />
          <span>{error}</span>
        </div>
      )}

      {/* Upload Result Summary */}
      {result && !uploading && (
        <div className="detail-card" style={{ marginTop: '20px' }}>
          <div className="card-header">
            <div className="card-header-left">
              <CheckCircle2 className="w-5 h-5" style={{ color: '#16a34a' }} />
              <h3 className="card-title">Upload Complete</h3>
            </div>
            <span style={{ fontSize: '0.78rem', color: '#64748b' }}>
              {result.uploaded} new &nbsp;·&nbsp; {result.updated} updated
              {result.errors?.length > 0 && <> &nbsp;·&nbsp; <span style={{ color: '#f87171' }}>{result.errors.length} errors</span></>}
            </span>
          </div>

          {/* Classification breakdown */}
          <div className="csv-status-grid">
            {Object.entries(STATUS_META).map(([key, meta]) => {
              const count = cs[key] ?? 0;
              const Icon = meta.icon;
              return (
                <div
                  key={key}
                  className="csv-status-card"
                  style={{ background: meta.bg, border: `1px solid ${meta.border}` }}
                >
                  <Icon className="w-5 h-5" style={{ color: meta.color }} />
                  <span className="csv-status-count" style={{ color: meta.color }}>{count}</span>
                  <span className="csv-status-label">{meta.label}</span>
                </div>
              );
            })}
          </div>

          {/* Error list */}
          {result.errors?.length > 0 && (
            <div className="csv-error-list">
              <p className="csv-error-list-title">Row Errors ({result.errors.length})</p>
              {result.errors.slice(0, 5).map((e, i) => (
                <div key={i} className="csv-error-row">
                  <span>Row {e.row}{e.api_id ? ` [${e.api_id}]` : ''}</span>
                  <span>{e.error}</span>
                </div>
              ))}
              {result.errors.length > 5 && (
                <p style={{ color: '#64748b', fontSize: '0.75rem', marginTop: '4px' }}>
                  …and {result.errors.length - 5} more
                </p>
              )}
            </div>
          )}
        </div>
      )}

      {/* Preview Table */}
      {previewRows.length > 0 && !uploading && (
        <div className="detail-card" style={{ marginTop: '20px' }}>
          <div className="card-header">
            <div className="card-header-left">
              <Eye className="w-5 h-5" style={{ color: '#60a5fa' }} />
              <h3 className="card-title">Preview — First {previewRows.length} Rows</h3>
            </div>
          </div>
          <div className="table-wrapper" style={{ overflowX: 'auto' }}>
            <table className="data-table" style={{ minWidth: '700px' }}>
              <thead>
                <tr>
                  {previewHeaders.map(h => <th key={h}>{h}</th>)}
                </tr>
              </thead>
              <tbody>
                {previewRows.map((row, i) => (
                  <tr key={i} className="table-row">
                    {previewHeaders.map(h => (
                      <td key={h} className="mono" style={{ maxWidth: '160px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                        {row[h]}
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Schema Guide */}
      <div className="detail-card" style={{ marginTop: '20px' }}>
        <div className="card-header">
          <div className="card-header-left">
            <FileText className="w-5 h-5" style={{ color: '#a78bfa' }} />
            <h3 className="card-title">CSV Format</h3>
          </div>
          <button className="btn-secondary" onClick={downloadSample} style={{ fontSize: '0.78rem', padding: '6px 14px' }}>
            <Download className="w-3.5 h-3.5" /> Download Template
          </button>
        </div>
        <div className="csv-schema-grid">
          {[
            { col: 'api_id',          desc: 'Unique identifier for the API',                        req: true  },
            { col: 'url',             desc: 'Full URL to probe e.g. https://api.bank.com/payments', req: true  },
            { col: 'method',          desc: 'HTTP method: GET, POST, PUT, DELETE…',                 req: true  },
            { col: 'last_traffic_at', desc: 'ISO-8601 timestamp of last known request (optional)',  req: false },
          ].map(({ col, desc, req }) => (
            <div key={col} className="csv-schema-row">
              <code className="csv-col-name">{col}</code>
              <span className={`csv-col-req ${req ? 'required' : 'optional'}`}>{req ? 'Required' : 'Optional'}</span>
              <span className="csv-col-desc">{desc}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
