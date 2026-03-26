import {
  ShieldAlert,
  LayoutDashboard,
  Server,
  Activity,
  FileText,
  Search,
  Bell,
  ChevronRight,
  Sparkles,
} from 'lucide-react';

const navItems = [
  { id: 'dashboard', label: 'Dashboard', icon: LayoutDashboard },
  { id: 'inventory', label: 'API Inventory', icon: Server },
  { id: 'monitoring', label: 'Monitoring', icon: Activity },
  { id: 'reports', label: 'Reports', icon: FileText },
  { id: 'scanner', label: 'External Scanner', icon: Search },
  { id: 'ai', label: 'AI Assistant', icon: Sparkles },
];

export default function Sidebar({ currentPage, onNavigate, apiCounts }) {
  return (
    <aside className="sidebar">
      {/* Logo */}
      <div className="sidebar-logo">
        <div className="sidebar-logo-icon">
          <ShieldAlert className="w-5 h-5" />
        </div>
        <div>
          <h1 className="sidebar-logo-title">Lazarus</h1>
          <p className="sidebar-logo-subtitle">API Ghost Defence</p>
        </div>
      </div>

      {/* Navigation */}
      <nav className="sidebar-nav">
        <p className="sidebar-section-label">MAIN MENU</p>
        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive = currentPage === item.id;
          return (
            <button
              key={item.id}
              onClick={() => onNavigate(item.id)}
              className={`sidebar-nav-item ${isActive ? 'active' : ''}`}
              id={`nav-${item.id}`}
            >
              <Icon className="w-[18px] h-[18px]" />
              <span>{item.label}</span>
              {item.id === 'inventory' && apiCounts?.total > 0 && (
                <span className="sidebar-badge">{apiCounts.total}</span>
              )}
              {item.id === 'monitoring' && (
                <span className="sidebar-badge green">Live</span>
              )}
              {item.id === 'ai' && (
                <span className="sidebar-badge ai-badge">AI</span>
              )}
            </button>
          );
        })}

        <div className="sidebar-divider" />

        <p className="sidebar-section-label">THREAT SUMMARY</p>
        <div className="sidebar-stat-group">
          <div className="sidebar-stat">
            <span className="sidebar-stat-dot red" />
            <span className="sidebar-stat-label">Shadow</span>
            <span className="sidebar-stat-value">{apiCounts?.shadow ?? 0}</span>
          </div>
          <div className="sidebar-stat">
            <span className="sidebar-stat-dot amber" />
            <span className="sidebar-stat-label">Zombie</span>
            <span className="sidebar-stat-value">{apiCounts?.zombie ?? 0}</span>
          </div>
          <div className="sidebar-stat">
            <span className="sidebar-stat-dot slate" />
            <span className="sidebar-stat-label">Stale</span>
            <span className="sidebar-stat-value">{apiCounts?.stale ?? 0}</span>
          </div>
          <div className="sidebar-stat">
            <span className="sidebar-stat-dot green" />
            <span className="sidebar-stat-label">Active</span>
            <span className="sidebar-stat-value">{apiCounts?.active ?? 0}</span>
          </div>
        </div>
      </nav>

      {/* Footer */}
      <div className="sidebar-footer">
        <div className="sidebar-scan-status">
          <span className="sidebar-scan-dot" />
          <span>Scanner Active</span>
        </div>
        <p className="sidebar-version">Lazarus v2.0</p>
      </div>
    </aside>
  );
}
