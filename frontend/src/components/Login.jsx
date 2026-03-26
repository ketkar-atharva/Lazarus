import { useState } from 'react';
import { ShieldAlert, Eye, EyeOff, ArrowRight } from 'lucide-react';
import '../styles/Auth.css';

export default function Login({ onLoginSuccess, onSwitchToSignup }) {
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
      const response = await fetch('http://localhost:8000/api/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || data.message || 'Invalid email or password');
      }

      localStorage.setItem('token', data.token);
      localStorage.setItem('user', JSON.stringify(data.user));
      onLoginSuccess(data.user);
    } catch (err) {
      console.error('Login error:', err);
      setError(err.message || 'Login failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="auth-container">
      <div className="auth-card">
        {/* Logo Section */}
        <div className="auth-logo">
          <div className="auth-logo-icon">
            <ShieldAlert className="w-8 h-8" />
          </div>
          <div>
            <h1 className="auth-logo-title">Lazarus</h1>
            <p className="auth-logo-subtitle">API Ghost Defence</p>
          </div>
        </div>

        {/* Form Section */}
        <div className="auth-form-wrapper">
          <h2 className="auth-heading">Welcome Back</h2>
          <p className="auth-subheading">
            Sign in to your account to continue
          </p>

          <form onSubmit={handleLogin} className="auth-form">
            {/* Email Field */}
            <div className="form-group">
              <label htmlFor="email" className="form-label">
                Email Address
              </label>
              <input
                id="email"
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="you@example.com"
                className="form-input"
                required
              />
            </div>

            {/* Password Field */}
            <div className="form-group">
              <label htmlFor="password" className="form-label">
                Password
              </label>
              <div className="password-input-wrapper">
                <input
                  id="password"
                  type={showPassword ? 'text' : 'password'}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••"
                  className="form-input"
                  required
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="password-toggle"
                >
                  {showPassword ? (
                    <EyeOff className="w-4 h-4" />
                  ) : (
                    <Eye className="w-4 h-4" />
                  )}
                </button>
              </div>
            </div>

            {/* Error Message */}
            {error && <div className="error-message">{error}</div>}

            {/* Submit Button */}
            <button
              type="submit"
              disabled={loading}
              className="auth-button"
            >
              {loading ? 'Signing in...' : 'Sign In'}
              <ArrowRight className="w-4 h-4" />
            </button>
          </form>

          {/* Signup Link */}
          <p className="auth-footer">
            Don't have an account?{' '}
            <button
              onClick={onSwitchToSignup}
              className="auth-link"
            >
              Create one
            </button>
          </p>
        </div>
      </div>

      {/* Background decoration */}
      <div className="auth-background-shape" />
    </div>
  );
}
