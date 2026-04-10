import pathlib

extra = """
/* === SIDEBAR USER SECTION === */
.sidebar-user{display:flex;align-items:center;gap:8px;margin-top:10px;padding:8px 10px;border-radius:8px;background:#f8fafc;border:1px solid #e2e8f0}
.sidebar-user-info{display:flex;align-items:center;gap:8px;flex:1;min-width:0}
.sidebar-user-avatar{width:26px;height:26px;border-radius:6px;background:linear-gradient(135deg,#2563eb,#7c3aed);display:flex;align-items:center;justify-content:center;color:#fff;flex-shrink:0}
.sidebar-user-text{display:flex;flex-direction:column;min-width:0}
.sidebar-user-name{font-size:11.5px;font-weight:600;color:#1e293b;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.sidebar-user-dept{font-size:10px;color:#94a3b8;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.sidebar-logout-btn{background:none;border:none;color:#94a3b8;cursor:pointer;padding:4px;border-radius:4px;display:flex;align-items:center;transition:color 0.15s,background 0.15s;flex-shrink:0}
.sidebar-logout-btn:hover{color:#dc2626;background:#fef2f2}
.sidebar-version{font-size:10px;color:#cbd5e1;margin-top:8px}

/* === CSV UPLOAD COMPONENT === */
.csv-dropzone{border:2px dashed #cbd5e1;border-radius:14px;background:#f8fafc;min-height:180px;display:flex;align-items:center;justify-content:center;cursor:pointer;transition:all 0.2s ease;position:relative;overflow:hidden}
.csv-dropzone:hover,.csv-dropzone.dragging{border-color:#2563eb;background:#eff6ff}
.csv-dropzone.uploading{cursor:default;border-color:#93c5fd;background:#eff6ff}
.csv-dropzone-inner{display:flex;flex-direction:column;align-items:center;gap:10px;padding:32px 24px;text-align:center;pointer-events:none}
.csv-drop-icon{width:56px;height:56px;border-radius:14px;background:#eff6ff;border:1px solid #bfdbfe;display:flex;align-items:center;justify-content:center;color:#2563eb;margin-bottom:4px;transition:all 0.2s}
.csv-dropzone:hover .csv-drop-icon,.csv-dropzone.dragging .csv-drop-icon{background:#dbeafe;transform:translateY(-2px)}
.csv-drop-title{font-size:15px;font-weight:600;color:#1e293b}
.csv-drop-sub{font-size:12.5px;color:#94a3b8}
.csv-spinner{width:36px;height:36px;border:3px solid #bfdbfe;border-top-color:#2563eb;border-radius:50%;animation:spin 0.7s linear infinite;margin-bottom:4px}
.csv-toast{position:fixed;top:24px;right:24px;z-index:9999;display:flex;align-items:center;gap:10px;padding:14px 18px;border-radius:10px;font-size:13.5px;font-weight:600;box-shadow:0 8px 32px rgba(0,0,0,.12);animation:slideInRight 0.35s cubic-bezier(.16,1,.3,1);max-width:420px}
.csv-toast.success{background:#f0fdf4;border:1px solid #bbf7d0;color:#166534}
.csv-toast.error{background:#fef2f2;border:1px solid #fecaca;color:#991b1b}
.csv-toast span{flex:1}
.csv-toast button{background:none;border:none;cursor:pointer;color:inherit;opacity:0.6;padding:2px;display:flex;align-items:center}
.csv-toast button:hover{opacity:1}
@keyframes slideInRight{from{transform:translateX(60px);opacity:0}to{transform:translateX(0);opacity:1}}
.csv-error-banner{display:flex;align-items:center;gap:8px;padding:12px 16px;border-radius:8px;background:#fef2f2;border:1px solid #fecaca;color:#991b1b;font-size:13px;font-weight:500;margin-top:12px}
.csv-status-grid{display:grid;grid-template-columns:repeat(4,1fr);gap:12px;padding:16px 24px 20px}
@media(max-width:768px){.csv-status-grid{grid-template-columns:repeat(2,1fr)}}
.csv-status-card{display:flex;flex-direction:column;align-items:center;gap:6px;padding:16px 12px;border-radius:10px;text-align:center;border:1px solid}
.csv-status-count{font-size:28px;font-weight:800;line-height:1}
.csv-status-label{font-size:11px;font-weight:600;text-transform:uppercase;letter-spacing:.05em;color:#64748b}
.csv-error-list{margin:0 24px 20px;border:1px solid #fecaca;border-radius:8px;overflow:hidden}
.csv-error-list-title{padding:8px 14px;background:#fef2f2;font-size:12px;font-weight:600;color:#991b1b;border-bottom:1px solid #fecaca}
.csv-error-row{display:flex;gap:12px;justify-content:space-between;padding:6px 14px;font-size:11.5px;border-bottom:1px solid #fee2e2;color:#dc2626}
.csv-error-row:last-child{border-bottom:none}
.csv-schema-grid{padding:12px 24px 20px;display:flex;flex-direction:column;gap:6px}
.csv-schema-row{display:grid;grid-template-columns:180px 76px 1fr;gap:12px;align-items:center;padding:7px 10px;border-radius:6px;background:#f8fafc;border:1px solid #f1f5f9;font-size:12px}
.csv-col-name{font-family:'JetBrains Mono',monospace;font-size:11.5px;color:#2563eb;background:#eff6ff;padding:2px 8px;border-radius:4px;white-space:nowrap}
.csv-col-req{font-size:10.5px;font-weight:700;padding:2px 8px;border-radius:10px;text-align:center;white-space:nowrap}
.csv-col-req.required{background:#fef2f2;color:#dc2626;border:1px solid #fecaca}
.csv-col-req.optional{background:#f1f5f9;color:#64748b;border:1px solid #e2e8f0}
.csv-col-desc{color:#64748b;font-size:11.5px}
.btn-secondary{display:inline-flex;align-items:center;gap:6px;padding:8px 16px;background:#fff;border:1px solid #e2e8f0;border-radius:8px;font-size:12.5px;font-weight:600;color:#475569;cursor:pointer;transition:all .15s;font-family:inherit}
.btn-secondary:hover{background:#f8fafc;border-color:#cbd5e1;color:#1e293b}
.form-hint{font-size:11px;margin-top:4px}
.form-hint.error{color:#dc2626}
.auth-card-wide{max-width:560px}
.auth-row{display:grid;grid-template-columns:1fr 1fr;gap:16px}
@media(max-width:580px){.auth-row{grid-template-columns:1fr}.auth-card-wide{padding:32px 24px}}
.sidebar-badge.ai-badge{background:linear-gradient(135deg,rgba(124,58,237,.13),rgba(99,102,241,.13));color:#7c3aed;border:1px solid rgba(124,58,237,.18)}
"""

p = pathlib.Path("frontend/src/index.css")
p.write_text(p.read_text(encoding="utf-8") + extra, encoding="utf-8")
print("Done — CSS appended.")
