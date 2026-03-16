import { useState, useRef, useEffect } from 'react';
import axios from 'axios';
import ReactMarkdown from 'react-markdown';
import {
  X,
  Send,
  Bot,
  User,
  Sparkles,
  Brain,
  FileText,
  Swords,
  AlertTriangle,
  Loader2,
  MessageSquare,
  ChevronDown,
  Zap,
  Shield,
} from 'lucide-react';

const API_BASE = 'http://localhost:8000';

const QUICK_ACTIONS = [
  { label: 'Which APIs have no authentication?', icon: Shield },
  { label: 'Show me all critical risk APIs', icon: AlertTriangle },
  { label: 'What is our biggest security concern right now?', icon: Zap },
  { label: 'Which APIs expose sensitive customer data?', icon: Brain },
];

export default function AiChat({ isOpen, onClose, apiContext }) {
  const [messages, setMessages] = useState([
    {
      role: 'ai',
      content: "👋 Hi! I'm **Lazarus AI**, your API security assistant. I can help you understand security risks in plain English, answer questions about your APIs, generate compliance reports, and simulate attack scenarios.\n\nTry asking me something or use the quick actions below!",
    },
  ]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [activeFeature, setActiveFeature] = useState(null);
  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  useEffect(() => {
    if (isOpen && inputRef.current) {
      setTimeout(() => inputRef.current?.focus(), 300);
    }
  }, [isOpen]);

  const addAiMessage = (content) => {
    setMessages((prev) => [...prev, { role: 'ai', content }]);
  };

  const addUserMessage = (content) => {
    setMessages((prev) => [...prev, { role: 'user', content }]);
  };

  /* ── NL Query ── */
  const handleQuery = async (question) => {
    if (!question.trim()) return;
    addUserMessage(question);
    setInput('');
    setLoading(true);
    setActiveFeature('query');
    try {
      const res = await axios.post(`${API_BASE}/api/ai/query`, { question });
      addAiMessage(res.data.answer);
    } catch (err) {
      const detail = err.response?.data?.detail || 'Failed to get AI response. Make sure GEMINI_API_KEY is set.';
      addAiMessage(`⚠ **Error:** ${detail}`);
    } finally {
      setLoading(false);
      setActiveFeature(null);
    }
  };

  /* ── Explain Risk ── */
  const handleExplainRisk = async () => {
    if (!apiContext?.path) {
      addAiMessage("⚠ Please open an API detail page first, then I can explain its risks.");
      return;
    }
    addUserMessage(`Explain the risks for **${apiContext.path}**`);
    setLoading(true);
    setActiveFeature('explain');
    try {
      const res = await axios.post(`${API_BASE}/api/ai/explain-risk`, {
        api_id: apiContext.id,
        path: apiContext.path,
      });
      addAiMessage(res.data.explanation);
    } catch (err) {
      const detail = err.response?.data?.detail || 'AI analysis failed.';
      addAiMessage(`⚠ **Error:** ${detail}`);
    } finally {
      setLoading(false);
      setActiveFeature(null);
    }
  };

  /* ── Generate Report ── */
  const handleGenerateReport = async () => {
    if (!apiContext?.path) {
      addAiMessage("⚠ Please open an API detail page first, then I can generate a report.");
      return;
    }
    addUserMessage(`Generate a security report for **${apiContext.path}**`);
    setLoading(true);
    setActiveFeature('report');
    try {
      const res = await axios.post(`${API_BASE}/api/ai/generate-report`, {
        api_id: apiContext.id,
        path: apiContext.path,
      });
      addAiMessage(res.data.report);
    } catch (err) {
      const detail = err.response?.data?.detail || 'Report generation failed.';
      addAiMessage(`⚠ **Error:** ${detail}`);
    } finally {
      setLoading(false);
      setActiveFeature(null);
    }
  };

  /* ── Attack Simulation ── */
  const handleAttackSim = async () => {
    if (!apiContext?.path) {
      addAiMessage("⚠ Please open an API detail page first, then I can simulate attack scenarios.");
      return;
    }
    addUserMessage(`Simulate attack scenarios for **${apiContext.path}**`);
    setLoading(true);
    setActiveFeature('attack');
    try {
      const res = await axios.post(`${API_BASE}/api/ai/attack-simulation`, {
        api_id: apiContext.id,
        path: apiContext.path,
      });
      addAiMessage(res.data.simulation);
    } catch (err) {
      const detail = err.response?.data?.detail || 'Attack simulation failed.';
      addAiMessage(`⚠ **Error:** ${detail}`);
    } finally {
      setLoading(false);
      setActiveFeature(null);
    }
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    handleQuery(input);
  };

  if (!isOpen) return null;

  return (
    <div className="ai-chat-overlay" onClick={onClose}>
      <div className="ai-chat-panel" onClick={(e) => e.stopPropagation()}>
        {/* Header */}
        <div className="ai-chat-header">
          <div className="ai-chat-header-left">
            <div className="ai-chat-avatar">
              <Sparkles className="w-5 h-5" />
            </div>
            <div>
              <h3 className="ai-chat-title">Lazarus AI</h3>
              <p className="ai-chat-subtitle">Security Intelligence Assistant</p>
            </div>
          </div>
          <button className="ai-chat-close" onClick={onClose} id="ai-chat-close">
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Context Bar */}
        {apiContext?.path && (
          <div className="ai-chat-context">
            <Shield className="w-3.5 h-3.5" />
            <span>Context: <strong>{apiContext.path}</strong></span>
          </div>
        )}

        {/* Action Buttons */}
        <div className="ai-chat-actions">
          <button
            className={`ai-action-btn ${activeFeature === 'explain' ? 'active' : ''}`}
            onClick={handleExplainRisk}
            disabled={loading}
          >
            <Brain className="w-3.5 h-3.5" />
            <span>Explain Risk</span>
          </button>
          <button
            className={`ai-action-btn ${activeFeature === 'report' ? 'active' : ''}`}
            onClick={handleGenerateReport}
            disabled={loading}
          >
            <FileText className="w-3.5 h-3.5" />
            <span>AI Report</span>
          </button>
          <button
            className={`ai-action-btn ${activeFeature === 'attack' ? 'active' : ''}`}
            onClick={handleAttackSim}
            disabled={loading}
          >
            <Swords className="w-3.5 h-3.5" />
            <span>Attack Sim</span>
          </button>
        </div>

        {/* Messages */}
        <div className="ai-chat-messages">
          {messages.map((msg, i) => (
            <div key={i} className={`ai-msg ${msg.role}`}>
              <div className="ai-msg-avatar">
                {msg.role === 'ai' ? (
                  <Bot className="w-4 h-4" />
                ) : (
                  <User className="w-4 h-4" />
                )}
              </div>
              <div className="ai-msg-content">
                <ReactMarkdown>{msg.content}</ReactMarkdown>
              </div>
            </div>
          ))}
          {loading && (
            <div className="ai-msg ai">
              <div className="ai-msg-avatar">
                <Bot className="w-4 h-4" />
              </div>
              <div className="ai-msg-content">
                <div className="ai-typing">
                  <div className="ai-typing-dot" />
                  <div className="ai-typing-dot" />
                  <div className="ai-typing-dot" />
                </div>
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        {/* Quick Actions */}
        {messages.length <= 2 && !loading && (
          <div className="ai-quick-actions">
            {QUICK_ACTIONS.map((qa, i) => {
              const Icon = qa.icon;
              return (
                <button
                  key={i}
                  className="ai-quick-btn"
                  onClick={() => handleQuery(qa.label)}
                >
                  <Icon className="w-3.5 h-3.5" />
                  <span>{qa.label}</span>
                </button>
              );
            })}
          </div>
        )}

        {/* Input */}
        <form className="ai-chat-input-bar" onSubmit={handleSubmit}>
          <input
            ref={inputRef}
            type="text"
            className="ai-chat-input"
            placeholder="Ask about your API security..."
            value={input}
            onChange={(e) => setInput(e.target.value)}
            disabled={loading}
            id="ai-chat-input"
          />
          <button
            type="submit"
            className="ai-send-btn"
            disabled={loading || !input.trim()}
            id="ai-send-btn"
          >
            {loading ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : (
              <Send className="w-4 h-4" />
            )}
          </button>
        </form>
      </div>
    </div>
  );
}
