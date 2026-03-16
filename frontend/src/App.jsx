import { useState, useEffect, useCallback, useRef } from 'react';
import axios from 'axios';
import { ChevronLeft, ChevronRight, Sparkles } from 'lucide-react';
import Sidebar from './components/Sidebar';
import DashboardHome from './components/DashboardHome';
import Dashboard from './components/Dashboard';
import ApiDetail from './components/ApiDetail';
import Monitoring from './components/Monitoring';
import Reports from './components/Reports';
import AiChat from './components/AiChat';
import AiInsights from './components/AiInsights';
import './App.css';

const API_BASE = 'http://localhost:8000';

const PAGE_LABELS = {
  dashboard: 'Dashboard',
  inventory: 'Dashboard',
  monitoring: 'Monitoring',
  reports: 'Reports',
  detail: 'API Detail',
  ai: 'AI Assistant',
};

export default function App() {
  const [currentPage, setCurrentPage] = useState('dashboard');
  const [catalog, setCatalog] = useState([]);
  const [traffic, setTraffic] = useState([]);
  const [analysis, setAnalysis] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [deployedPaths, setDeployedPaths] = useState(new Set());
  const [selectedApi, setSelectedApi] = useState(null);
  const [chatOpen, setChatOpen] = useState(false);

  /* ── Navigation History ── */
  const [history, setHistory] = useState([{ page: 'dashboard', api: null }]);
  const [historyIndex, setHistoryIndex] = useState(0);
  const isNavRef = useRef(false); // flag to skip pushing on back/forward

  const navigateTo = useCallback((page, api = null) => {
    setCurrentPage(page);
    setSelectedApi(api);

    if (!isNavRef.current) {
      setHistory(prev => {
        const trimmed = prev.slice(0, historyIndex + 1);
        return [...trimmed, { page, api }];
      });
      setHistoryIndex(prev => prev + 1);
    }
    isNavRef.current = false;
  }, [historyIndex]);

  const canGoBack = historyIndex > 0;
  const canGoForward = historyIndex < history.length - 1;

  const goBack = useCallback(() => {
    if (!canGoBack) return;
    const newIdx = historyIndex - 1;
    const entry = history[newIdx];
    isNavRef.current = true;
    setHistoryIndex(newIdx);
    setCurrentPage(entry.page);
    setSelectedApi(entry.api);
  }, [canGoBack, historyIndex, history]);

  const goForward = useCallback(() => {
    if (!canGoForward) return;
    const newIdx = historyIndex + 1;
    const entry = history[newIdx];
    isNavRef.current = true;
    setHistoryIndex(newIdx);
    setCurrentPage(entry.page);
    setSelectedApi(entry.api);
  }, [canGoForward, historyIndex, history]);

  /* ── Data Fetching ── */
  const fetchData = useCallback(async (isInitial = false) => {
    try {
      const [catRes, trafRes, analyzeRes, honeypotRes] = await Promise.all([
        axios.get(`${API_BASE}/api/catalog`),
        axios.get(`${API_BASE}/api/traffic`),
        axios.get(`${API_BASE}/api/analyze`),
        axios.get(`${API_BASE}/api/honeypots`).catch(() => ({ data: [] })),
      ]);
      setCatalog(catRes.data);
      setTraffic(trafRes.data);
      setAnalysis(analyzeRes.data);
      // Load persisted honeypots from MongoDB
      if (honeypotRes.data && honeypotRes.data.length > 0) {
        setDeployedPaths(new Set(honeypotRes.data));
      }
    } catch (err) {
      if (isInitial) setError('Unable to reach the Lazarus backend. Ensure FastAPI is running on port 8000.');
      console.error(err);
    } finally {
      if (isInitial) setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchData(true);
  }, [fetchData]);

  const handleDeploy = useCallback(async (path) => {
    try {
      await axios.post(`${API_BASE}/api/defend`, { path });
      await new Promise(r => setTimeout(r, 600));
      setDeployedPaths(p => new Set(p).add(path));
    } catch (err) {
      console.error('Deploy failed:', err);
    }
  }, []);

  const handleViewApi = useCallback((id, path) => {
    navigateTo('detail', { id, path });
  }, [navigateTo]);

  const handleBackToDashboard = useCallback(() => {
    navigateTo('dashboard', null);
  }, [navigateTo]);

  const handleNavigate = useCallback((page) => {
    navigateTo(page, null);
  }, [navigateTo]);

  /* ── Compute counts for sidebar ── */
  const catalogPaths = new Set(catalog.map(a => a.path));
  let shadowCount = 0, zombieCount = 0, staleCount = 0, activeCount = 0;
  catalog.forEach(api => {
    const flow = traffic.find(t => t.path === api.path);
    if (api.is_deprecated && flow && flow.hit_count > 0) zombieCount++;
    else if (!flow || flow.hit_count === 0) staleCount++;
    else activeCount++;
  });
  traffic.forEach(flow => {
    if (!catalogPaths.has(flow.path)) shadowCount++;
  });

  const apiCounts = {
    total: catalog.length + shadowCount,
    shadow: shadowCount,
    zombie: zombieCount,
    stale: staleCount,
    active: activeCount,
  };

  /* Loading */
  if (loading) {
    return (
      <div className="app-loading">
        <div className="loading-spinner" />
        <p className="loading-title">Lazarus</p>
        <p className="loading-subtitle">Initializing API scanner...</p>
      </div>
    );
  }

  /* Error */
  if (error) {
    return (
      <div className="app-error">
        <div className="error-icon">⚠</div>
        <h2>Connection Failed</h2>
        <p>{error}</p>
      </div>
    );
  }

  /* Render current page */
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
      case 'monitoring':
        return <Monitoring />;
      case 'reports':
        return <Reports />;
      case 'ai':
        return <AiInsights onOpenChat={() => setChatOpen(true)} />;
      case 'inventory':
        return (
          <Dashboard
            catalog={catalog}
            traffic={traffic}
            analysis={analysis}
            onViewApi={handleViewApi}
            onDeploy={handleDeploy}
            deployedPaths={deployedPaths}
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
            deployedPaths={deployedPaths}
            onOpenChat={() => setChatOpen(true)}
          />
        );
    }
  };

  /* Breadcrumb label */
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

      {/* Floating AI Chat Toggle Button */}
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
