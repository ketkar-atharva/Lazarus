import { useState } from 'react';
import { ShieldAlert, Eye, EyeOff, ArrowRight, AlertCircle } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import api from '../api';
import '../styles/Auth.css';

export default function Login({ onSwitchToSignup }) {
  const { login } = useAuth();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleLogin = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      // OAuth2PasswordRequestForm requires application/x-www-form-urlencoded
      const params = new URLSearchParams();
      params.append('username', email);
      params.append('password', password);

      const res = await api.post('/auth/login', params, {
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      });

      login(res.data.access_token, res.data.user);
    } catch (err) {
      const detail = err.response?.data?.detail;
      if (err.response?.status === 401) {
        setError('Invalid credentials. Please check your email and password.');
      } else {
        setError(
          typeof detail === 'object'
            ? detail.detail || 'Login failed.'
            : detail || 'Login failed.'
        );
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="auth-container">
      <div className="auth-card">
        {/* Logo */}
        <div className="auth-logo">
          <div className="auth-logo-icon">
            <ShieldAlert className="w-8 h-8" />
          </div>
          <div>
            <h1 className="auth-logo-title">Lazarus</h1>
            <p className="auth-logo-subtitle">API Ghost Defence</p>
          </div>
        </div>

        <div className="auth-form-wrapper">
          <h2 className="auth-heading">Welcome Back</h2>
          <p className="auth-subheading">Sign in with your bank credentials to continue</p>

          <form onSubmit={handleLogin} className="auth-form">
            <div className="form-group">
              <label htmlFor="login-email" className="form-label">Email Address</label>
              <input
                id="login-email"
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="you@lazarusbank.com"
                className="form-input"
                required
                autoComplete="email"
              />
            </div>

            <div className="form-group">
              <label htmlFor="login-password" className="form-label">Password</label>
              <div className="password-input-wrapper">
                <input
                  id="login-password"
                  type={showPassword ? 'text' : 'password'}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••"
                  className="form-input"
                  required
                  autoComplete="current-password"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="password-toggle"
                  tabIndex={-1}
                >
                  {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              </div>
            </div>

            {error && (
              <div className="error-message">
                <AlertCircle className="w-4 h-4" />
                {error}
              </div>
            )}

            <button
              id="login-submit"
              type="submit"
              disabled={loading}
              className="auth-button"
            >
              {loading ? 'Signing in…' : 'Sign In'}
              <ArrowRight className="w-4 h-4" />
            </button>
          </form>

          <p className="auth-footer">
            Don't have an account?{' '}
            <button onClick={onSwitchToSignup} className="auth-link" id="switch-to-signup">
              Create one
            </button>
          </p>
        </div>
      </div>
      <div className="auth-background-shape" />
    </div>
  );
}
