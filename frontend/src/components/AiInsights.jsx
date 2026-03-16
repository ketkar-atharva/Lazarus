import { useState, useEffect } from 'react';
import axios from 'axios';
import ReactMarkdown from 'react-markdown';
import {
  Sparkles,
  Brain,
  Shield,
  AlertTriangle,
  FileText,
  Swords,
  Loader2,
  RefreshCw,
  Zap,
  Target,
  Search,
  Eye,
  MessageSquare,
} from 'lucide-react';

const API_BASE = 'http://localhost:8000';

const PRESET_QUERIES = [
  { label: 'Which APIs have no authentication?', icon: Shield },
  { label: 'Show me all critical risk APIs', icon: AlertTriangle },
  { label: 'Which APIs expose sensitive customer data?', icon: Eye },
  { label: 'What is the biggest security concern right now?', icon: Zap },
  { label: 'Which payment APIs are at risk?', icon: Target },
  { label: 'Are there any shadow or undocumented APIs?', icon: Search },
];

export default function AiInsights({ onOpenChat }) {
  const [summary, setSummary] = useState(null);
  const [summaryLoading, setSummaryLoading] = useState(true);
  const [queryResult, setQueryResult] = useState(null);
  const [queryLoading, setQueryLoading] = useState(false);
  const [activeQuery, setActiveQuery] = useState(null);
  const [customQuery, setCustomQuery] = useState('');

  useEffect(() => {
    (async () => {
      try {
        const res = await axios.get(`${API_BASE}/api/ai/security-summary`);
        setSummary(res.data.summary);
      } catch (err) {
        setSummary('⚠ Could not generate AI summary. Ensure the backend is running and GEMINI_API_KEY is set.');
      } finally {
        setSummaryLoading(false);
      }
    })();
  }, []);

  const handlePresetQuery = async (question) => {
    setActiveQuery(question);
    setQueryLoading(true);
    setQueryResult(null);
    try {
      const res = await axios.post(`${API_BASE}/api/ai/query`, { question });
      setQueryResult(res.data.answer);
    } catch (err) {
      const detail = err.response?.data?.detail || 'AI query failed.';
      setQueryResult(`⚠ **Error:** ${detail}`);
    } finally {
      setQueryLoading(false);
    }
  };

  const handleCustomQuery = (e) => {
    e.preventDefault();
    if (customQuery.trim()) {
      handlePresetQuery(customQuery.trim());
      setCustomQuery('');
    }
  };

  return (
    <div className="dashboard-content">
      {/* Page Header */}
      <div className="page-header">
        <div>
          <h2 className="page-title">AI Security Insights</h2>
          <p className="page-subtitle">AI-powered analysis and intelligence for your API landscape</p>
        </div>
        <div className="header-live-badge" style={{ background: '#f5f3ff', borderColor: '#ddd6fe', color: '#7c3aed' }}>
          <Sparkles className="w-4 h-4" />
          <span>Powered by Gemini AI</span>
        </div>
      </div>

      {/* AI Executive Summary */}
      <div className="ai-summary-card">
        <div className="card-header">
          <div className="card-header-left">
            <Brain className="w-5 h-5 text-purple-500" />
            <h3 className="card-title">AI Executive Summary</h3>
          </div>
          <button
            className="ai-refresh-btn"
            onClick={() => {
              setSummaryLoading(true);
              axios.get(`${API_BASE}/api/ai/security-summary`)
                .then(res => setSummary(res.data.summary))
                .catch(() => setSummary('⚠ Failed to refresh.'))
                .finally(() => setSummaryLoading(false));
            }}
          >
            <RefreshCw className={`w-3.5 h-3.5 ${summaryLoading ? 'animate-spin' : ''}`} />
          </button>
        </div>
        <div className="ai-summary-body">
          {summaryLoading ? (
            <div className="ai-skeleton-block">
              <div className="ai-skeleton-line wide" />
              <div className="ai-skeleton-line medium" />
              <div className="ai-skeleton-line wide" />
              <div className="ai-skeleton-line short" />
            </div>
          ) : (
            <div className="ai-rendered-content">
              <ReactMarkdown>{summary}</ReactMarkdown>
            </div>
          )}
        </div>
      </div>

      {/* Two Column Layout */}
      <div className="dashboard-grid-2col">
        {/* Left: Quick Query Panel */}
        <div className="detail-card">
          <div className="card-header">
            <div className="card-header-left">
              <MessageSquare className="w-5 h-5 text-blue-500" />
              <h3 className="card-title">Ask AI About Your Security</h3>
            </div>
          </div>

          {/* Custom Query Input */}
          <div className="ai-custom-query-wrap">
            <form onSubmit={handleCustomQuery} className="ai-custom-query-form">
              <input
                type="text"
                className="ai-custom-query-input"
                placeholder="Type your own security question..."
                value={customQuery}
                onChange={(e) => setCustomQuery(e.target.value)}
                disabled={queryLoading}
                id="ai-insights-query-input"
              />
              <button
                type="submit"
                className="ai-custom-query-btn"
                disabled={queryLoading || !customQuery.trim()}
              >
                {queryLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Search className="w-4 h-4" />}
              </button>
            </form>
          </div>

          {/* Preset Queries */}
          <div className="ai-preset-queries">
            <p className="ai-preset-label">Or try one of these:</p>
            {PRESET_QUERIES.map((pq, i) => {
              const Icon = pq.icon;
              return (
                <button
                  key={i}
                  className={`ai-preset-btn ${activeQuery === pq.label ? 'active' : ''}`}
                  onClick={() => handlePresetQuery(pq.label)}
                  disabled={queryLoading}
                >
                  <Icon className="w-3.5 h-3.5" />
                  <span>{pq.label}</span>
                </button>
              );
            })}
          </div>
        </div>

        {/* Right: Query Result */}
        <div className="detail-card">
          <div className="card-header">
            <div className="card-header-left">
              <Sparkles className="w-5 h-5 text-purple-500" />
              <h3 className="card-title">AI Response</h3>
            </div>
          </div>
          <div className="ai-response-body">
            {queryLoading ? (
              <div className="ai-loading-state">
                <Loader2 className="w-6 h-6 animate-spin text-purple-500" />
                <p>Analyzing your security data...</p>
                {activeQuery && (
                  <p className="ai-loading-query">"{activeQuery}"</p>
                )}
              </div>
            ) : queryResult ? (
              <div className="ai-rendered-content">
                <ReactMarkdown>{queryResult}</ReactMarkdown>
              </div>
            ) : (
              <div className="ai-empty-state">
                <Brain className="w-10 h-10" />
                <p>Select a question or type your own to get AI-powered security insights.</p>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* AI Capabilities Info */}
      <div className="ai-capabilities-bar">
        {[
          { icon: Brain, title: 'Risk Explanation', desc: 'Plain-English security analysis' },
          { icon: MessageSquare, title: 'NL Queries', desc: 'Ask questions in plain English' },
          { icon: FileText, title: 'Report Generator', desc: 'AI-enriched compliance reports' },
          { icon: Swords, title: 'Attack Simulator', desc: 'Hypothetical attack scenarios' },
        ].map((cap, i) => {
          const Icon = cap.icon;
          return (
            <div key={i} className="ai-cap-item">
              <div className="ai-cap-icon">
                <Icon className="w-4 h-4" />
              </div>
              <div>
                <span className="ai-cap-title">{cap.title}</span>
                <span className="ai-cap-desc">{cap.desc}</span>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
