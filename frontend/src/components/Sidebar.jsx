import {
  ShieldAlert,
  LayoutDashboard,
  Server,
  Activity,
  FileText,
  Search,
  Sparkles,
  Crosshair,
  Upload,
  LogOut,
  User,
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';

const navItems = [
  { id: 'dashboard', label: 'Dashboard',        icon: LayoutDashboard },
  { id: 'inventory', label: 'API Inventory',    icon: Server           },
  { id: 'catalog',   label: 'API Catalog',      icon: Upload           },
  { id: 'monitoring',label: 'Monitoring',        icon: Activity         },
  { id: 'reports',   label: 'Reports',           icon: FileText         },
  { id: 'scanner',   label: 'External Scanner',  icon: Search           },
  { id: 'ai',        label: 'AI Assistant',      icon: Sparkles         },
];

export default function Sidebar({ currentPage, onNavigate, apiCounts, isOpen, setIsOpen }) {
  const { user, logout } = useAuth();

  return (
    <aside className={`sidebar ${isOpen ? 'open' : ''}`}>
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
              onClick={() => {
                onNavigate(item.id);
                if (setIsOpen) setIsOpen(false);
              }}
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
              {item.id === 'catalog' && (
                <span className="sidebar-badge" style={{ background: 'rgba(167,139,250,0.15)', color: '#a78bfa' }}>CSV</span>
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

        {/* User info + logout */}
        {user && (
          <div className="sidebar-user">
            <div className="sidebar-user-info">
              <div className="sidebar-user-avatar">
                <User className="w-3.5 h-3.5" />
              </div>
              <div className="sidebar-user-text">
                <span className="sidebar-user-name">{user.full_name || user.email}</span>
                <span className="sidebar-user-dept">{user.department || user.employee_id || ''}</span>
              </div>
            </div>
            <button
              className="sidebar-logout-btn"
              onClick={logout}
              title="Sign out"
              id="sidebar-logout"
            >
              <LogOut className="w-3.5 h-3.5" />
            </button>
          </div>
        )}

        <p className="sidebar-version">Lazarus v2.1</p>
      </div>
    </aside>
  );
}
