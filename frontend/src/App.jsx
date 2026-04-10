import { useState, useEffect, useCallback, useRef } from 'react';
import { ChevronLeft, ChevronRight, Sparkles } from 'lucide-react';
import { AuthProvider, useAuth } from './context/AuthContext';
import api, { setupApiInterceptors } from './api';
import Sidebar from './components/Sidebar';
import DashboardHome from './components/DashboardHome';
import Dashboard from './components/Dashboard';
import ApiDetail from './components/ApiDetail';
import Monitoring from './components/Monitoring';
import Reports from './components/Reports';
import AiChat from './components/AiChat';
import AiInsights from './components/AiInsights';
import ExternalScanner from './components/ExternalScanner';
import CsvUpload from './components/CsvUpload';
import Login from './components/Login';
import Signup from './components/Signup';
import './App.css';

// ── Path normalization (mirrors backend) ──
function normalizePath(path) {
  if (!path || typeof path !== 'string') return path;
  // 1. Lowercase
  let normalized = path.toLowerCase();
  // 2. Remove query parameters
  normalized = normalized.split('?')[0];
  // 3. Collapse consecutive slashes
  normalized = normalized.replace(/\/+/g, '/');
  // 4. Strip trailing slash (except for root '/')
  if (normalized !== '/') {
    normalized = normalized.replace(/\/$/, '');
  }
  return normalized;
}

const PAGE_LABELS = {
  dashboard: 'Dashboard',
  inventory:  'API Inventory',
  catalog:    'API Catalog',
  monitoring: 'Monitoring',
  reports:    'Reports',
  detail:     'API Detail',
  scanner:    'External Scanner',
  ai:         'AI Assistant',
};

// ── Inner App (has access to AuthContext) ──
function AppInner() {
  const { isAuthenticated, token, logout } = useAuth();
  const [authView, setAuthView] = useState('login'); // 'login' | 'signup'

  // Use a ref to always provide the freshest token to the axios interceptor
  // bypassing the race condition where MainShell fetches before useEffect fires
  const tokenRef = useRef(token);
  tokenRef.current = token;

  // Wire up axios interceptors once we have auth context
  useEffect(() => {
    setupApiInterceptors({ getToken: () => tokenRef.current, logout });
  }, [logout]);

  // Listen for 401 events from the interceptor
  useEffect(() => {
    const handler = () => logout();
    window.addEventListener('lazarus:unauthorized', handler);
    return () => window.removeEventListener('lazarus:unauthorized', handler);
  }, [logout]);

  if (!isAuthenticated) {
    return authView === 'login'
      ? <Login onSwitchToSignup={() => setAuthView('signup')} />
      : <Signup onSwitchToLogin={() => setAuthView('login')} />;
  }

  return <MainShell />;
}

// ── Main App Shell (authenticated) ──
function MainShell() {
  const [currentPage, setCurrentPage] = useState('dashboard');
  const [catalog, setCatalog] = useState([]);
  const [traffic, setTraffic] = useState([]);
  const [analysis, setAnalysis] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedApi, setSelectedApi] = useState(null);
  const [chatOpen, setChatOpen] = useState(false);

  /* ── Navigation History ── */
  const [history, setHistory] = useState([{ page: 'dashboard', api: null }]);
  const [historyIndex, setHistoryIndex] = useState(0);
  const isNavRef = useRef(false);

  const navigateTo = useCallback((page, apiObj = null) => {
    setCurrentPage(page);
    setSelectedApi(apiObj);
    if (!isNavRef.current) {
      setHistory(prev => {
        const trimmed = prev.slice(0, historyIndex + 1);
        return [...trimmed, { page, api: apiObj }];
      });
      setHistoryIndex(prev => prev + 1);
    }
    isNavRef.current = false;
  }, [historyIndex]);

  const canGoBack    = historyIndex > 0;
  const canGoForward = historyIndex < history.length - 1;

  const goBack = useCallback(() => {
    if (!canGoBack) return;
    const newIdx = historyIndex - 1;
    const entry  = history[newIdx];
    isNavRef.current = true;
    setHistoryIndex(newIdx);
    setCurrentPage(entry.page);
    setSelectedApi(entry.api);
  }, [canGoBack, historyIndex, history]);

  const goForward = useCallback(() => {
    if (!canGoForward) return;
    const newIdx = historyIndex + 1;
    const entry  = history[newIdx];
    isNavRef.current = true;
    setHistoryIndex(newIdx);
    setCurrentPage(entry.page);
    setSelectedApi(entry.api);
  }, [canGoForward, historyIndex, history]);

  /* ── Data Fetching (uses shared api instance with auth header) ── */
  const fetchData = useCallback(async (isInitial = false) => {
    try {
      const [catRes, trafRes, analyzeRes] = await Promise.all([
        api.get('/api/catalog'),
        api.get('/api/traffic'),
        api.get('/api/analyze'),
      ]);
      setCatalog(catRes.data);
      setTraffic(trafRes.data);
      setAnalysis(analyzeRes.data);
    } catch (err) {
      if (isInitial) setError('Unable to reach the Lazarus backend. Ensure FastAPI is running on port 8000.');
      console.error(err);
    } finally {
      if (isInitial) setLoading(false);
    }
  }, []);

  useEffect(() => { fetchData(true); }, [fetchData]);



  const handleViewApi = useCallback((id, path) => {
    navigateTo('detail', { id, path });
  }, [navigateTo]);

  const handleBackToDashboard = useCallback(() => navigateTo('dashboard', null), [navigateTo]);
  const handleNavigate = useCallback((page) => navigateTo(page, null), [navigateTo]);

  /* ── Compute counts for sidebar ── */
  const catalogPaths = new Set(catalog.map(a => normalizePath(a.path)));
  let shadowCount = 0, zombieCount = 0, staleCount = 0, activeCount = 0;
  catalog.forEach(api => {
    // Support both mock_data format (is_deprecated) and csv format (lazarus_status)
    const lazStatus = api.lazarus_status;
    if (lazStatus) {
      if (lazStatus === 'zombie')  zombieCount++;
      else if (lazStatus === 'shadow') shadowCount++;
      else if (lazStatus === 'stale')  staleCount++;
      else activeCount++;
    } else {
      const flow = traffic.find(t => normalizePath(t.path) === normalizePath(api.path));
      if (api.is_deprecated && flow && flow.hit_count > 0) zombieCount++;
      else if (!flow || flow.hit_count === 0) staleCount++;
      else activeCount++;
    }
  });
  traffic.forEach(flow => {
    if (!catalogPaths.has(normalizePath(flow.path))) shadowCount++;
  });

  const apiCounts = {
    total:  catalog.length + shadowCount,
    shadow: shadowCount,
    zombie: zombieCount,
    stale:  staleCount,
    active: activeCount,
  };

  if (loading) {
    return (
      <div className="app-loading">
        <div className="loading-spinner" />
        <p className="loading-title">Lazarus</p>
        <p className="loading-subtitle">Initializing API scanner…</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="app-error">
        <div className="error-icon">⚠</div>
        <h2>Connection Failed</h2>
        <p>{error}</p>
      </div>
    );
  }

  const renderPage = () => {
    switch (currentPage) {
      case 'detail':
        return (
          <ApiDetail
            apiId={selectedApi?.id}
            apiPath={selectedApi?.path}
            onBack={handleBackToDashboard}
          />
        );
      case 'monitoring': return <Monitoring />;
      case 'reports':    return <Reports />;
      case 'scanner':    return <ExternalScanner />;
      case 'ai':         return <AiInsights onOpenChat={() => setChatOpen(true)} />;
      case 'catalog':    return <CsvUpload />;
      case 'inventory':
        return (
          <Dashboard
            catalog={catalog}
            traffic={traffic}
            analysis={analysis}
            onViewApi={handleViewApi}
          />
        );
      case 'dashboard':
      default:
        return (
          <DashboardHome
            catalog={catalog}
            traffic={traffic}
            analysis={analysis}
            onViewApi={handleViewApi}
            onNavigate={navigateTo}
            onOpenChat={() => setChatOpen(true)}
          />
        );
    }
  };

  const currentLabel = PAGE_LABELS[currentPage] || 'Dashboard';

  return (
    <div className="app-shell">
      <Sidebar
        currentPage={currentPage === 'detail' ? 'dashboard' : currentPage}
        onNavigate={handleNavigate}
        apiCounts={apiCounts}
      />
      <main className="main-content">
        {/* Navigation Bar */}
        <div className="topnav-bar">
          <div className="topnav-buttons">
            <button
              className={`topnav-btn ${canGoBack ? '' : 'disabled'}`}
              onClick={goBack}
              disabled={!canGoBack}
              title="Go back"
              id="nav-back"
            >
              <ChevronLeft className="w-4 h-4" />
            </button>
            <button
              className={`topnav-btn ${canGoForward ? '' : 'disabled'}`}
              onClick={goForward}
              disabled={!canGoForward}
              title="Go forward"
              id="nav-forward"
            >
              <ChevronRight className="w-4 h-4" />
            </button>
          </div>
          <div className="topnav-breadcrumb">
            <span className="breadcrumb-root" onClick={() => handleNavigate('dashboard')}>Home</span>
            <ChevronRight className="w-3 h-3 breadcrumb-sep" />
            <span className="breadcrumb-current">{currentLabel}</span>
            {currentPage === 'detail' && selectedApi?.path && (
              <>
                <ChevronRight className="w-3 h-3 breadcrumb-sep" />
                <span className="breadcrumb-current">{selectedApi.path}</span>
              </>
            )}
          </div>
        </div>

        {renderPage()}
      </main>

      {/* Floating AI Chat Toggle */}
      <button
        className="ai-chat-fab"
        onClick={() => setChatOpen(true)}
        title="Open AI Assistant"
        id="ai-chat-fab"
      >
        <Sparkles className="w-5 h-5" />
      </button>

      {/* Floating AI Chat Panel */}
      <AiChat
        isOpen={chatOpen}
        onClose={() => setChatOpen(false)}
        apiContext={selectedApi}
      />
    </div>
  );
}

// ── Root export — wrap everything in AuthProvider ──
export default function App() {
  return (
    <AuthProvider>
      <AppInner />
    </AuthProvider>
  );
}
