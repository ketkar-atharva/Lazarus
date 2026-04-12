import { useState } from 'react';
import { ShieldAlert, Eye, EyeOff, ArrowRight, AlertCircle } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import api from '../api';
import '../styles/Auth.css';

const BANK_DOMAIN = '@lazarusbank.com';

export default function Signup({ onSwitchToLogin }) {
  const { login } = useAuth();
  const [formData, setFormData] = useState({
    full_name: '',
    employee_id: '',
    department: '',
    email: '',
    password: '',
    confirmPassword: '',
    invite_code: '',
  });
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirm, setShowConfirm] = useState(false);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [passwordStrength, setPasswordStrength] = useState(0);

  const calcStrength = (pwd) => {
    let s = 0;
    if (pwd.length >= 8)  s++;
    if (pwd.length >= 12) s++;
    if (/[a-z]/.test(pwd) && /[A-Z]/.test(pwd)) s++;
    if (/\d/.test(pwd)) s++;
    if (/[^a-zA-Z\d]/.test(pwd)) s++;
    return s;
  };

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
    if (name === 'password') setPasswordStrength(calcStrength(value));
  };

  const handleSignup = async (e) => {
    e.preventDefault();
    setError('');

    // Client-side validations
    if (!formData.email.toLowerCase().endsWith(BANK_DOMAIN)) {
      setError(`Email must end with ${BANK_DOMAIN}`);
      return;
    }
    if (formData.password.length < 8) {
      setError('Password must be at least 8 characters.');
      return;
    }
    if (formData.password !== formData.confirmPassword) {
      setError('Passwords do not match.');
      return;
    }

    setLoading(true);
    try {
      // 1. Create account
      await api.post('/auth/signup', {
        email: formData.email,
        password: formData.password,
        full_name: formData.full_name,
        employee_id: formData.employee_id,
        department: formData.department,
        invite_code: formData.invite_code,
      });

      // 2. Auto-login
      const params = new URLSearchParams();
      params.append('username', formData.email);
      params.append('password', formData.password);
      const loginRes = await api.post('/auth/login', params, {
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      });
      login(loginRes.data.access_token, loginRes.data.user);
    } catch (err) {
      const detail = err.response?.data?.detail;
      setError(
        typeof detail === 'object'
          ? detail.detail || 'Signup failed.'
          : detail || 'Signup failed. Please try again.'
      );
    } finally {
      setLoading(false);
    }
  };

  const strengthColors = ['', '#dc2626', '#f97316', '#eab308', '#22c55e', '#16a34a'];
  const strengthLabels = ['', 'Weak', 'Fair', 'Good', 'Strong', 'Very Strong'];

  return (
    <div className="auth-container">
      <div className="auth-card auth-card-wide">
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
          <h2 className="auth-heading">Create Your Account</h2>
          <p className="auth-subheading">Register with your bank email to protect your API ecosystem</p>

          <form onSubmit={handleSignup} className="auth-form">
            {/* Two-col row */}
            <div className="auth-row">
              <div className="form-group">
                <label htmlFor="signup-fullname" className="form-label">Full Name</label>
                <input
                  id="signup-fullname"
                  name="full_name"
                  type="text"
                  value={formData.full_name}
                  onChange={handleChange}
                  placeholder="Jane Smith"
                  className="form-input"
                  required
                />
              </div>
              <div className="form-group">
                <label htmlFor="signup-empid" className="form-label">Employee ID</label>
                <input
                  id="signup-empid"
                  name="employee_id"
                  type="text"
                  value={formData.employee_id}
                  onChange={handleChange}
                  placeholder="EMP-12345"
                  className="form-input"
                  required
                />
              </div>
            </div>

            <div className="auth-row">
              <div className="form-group">
                <label htmlFor="signup-department" className="form-label">Department</label>
                <input
                  id="signup-department"
                  name="department"
                  type="text"
                  value={formData.department}
                  onChange={handleChange}
                  placeholder="e.g. Core Banking, Security, R&D"
                  className="form-input"
                  required
                />
              </div>
              <div className="form-group">
                <label htmlFor="signup-invite-code" className="form-label">Invite Code</label>
                <input
                  id="signup-invite-code"
                  name="invite_code"
                  type="text"
                  value={formData.invite_code}
                  onChange={handleChange}
                  placeholder="Paste your unique code"
                  className="form-input"
                  required
                />
              </div>
            </div>

            <div className="form-group">
              <label htmlFor="signup-email" className="form-label">Email Address</label>
              <input
                id="signup-email"
                name="email"
                type="email"
                value={formData.email}
                onChange={handleChange}
                placeholder={`you${BANK_DOMAIN}`}
                className="form-input"
                required
                autoComplete="email"
              />
              {formData.email && !formData.email.toLowerCase().endsWith(BANK_DOMAIN) && (
                <p className="form-hint error">Must end with {BANK_DOMAIN}</p>
              )}
            </div>

            <div className="auth-row">
              <div className="form-group">
                <label htmlFor="signup-password" className="form-label">Password</label>
                <div className="password-input-wrapper">
                  <input
                    id="signup-password"
                    name="password"
                    type={showPassword ? 'text' : 'password'}
                    value={formData.password}
                    onChange={handleChange}
                    placeholder="••••••••"
                    className="form-input"
                    required
                    autoComplete="new-password"
                  />
                  <button type="button" onClick={() => setShowPassword(!showPassword)} className="password-toggle" tabIndex={-1}>
                    {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                  </button>
                </div>
                {formData.password && (
                  <div className="password-strength">
                    <div className="strength-bar">
                      <div
                        className="strength-fill"
                        style={{ width: `${(passwordStrength / 5) * 100}%`, backgroundColor: strengthColors[passwordStrength] }}
                      />
                    </div>
                    <span className="strength-label" style={{ color: strengthColors[passwordStrength] }}>
                      {strengthLabels[passwordStrength]}
                    </span>
                  </div>
                )}
              </div>

              <div className="form-group">
                <label htmlFor="signup-confirm" className="form-label">Confirm Password</label>
                <div className="password-input-wrapper">
                  <input
                    id="signup-confirm"
                    name="confirmPassword"
                    type={showConfirm ? 'text' : 'password'}
                    value={formData.confirmPassword}
                    onChange={handleChange}
                    placeholder="••••••••"
                    className="form-input"
                    required
                    autoComplete="new-password"
                  />
                  <button type="button" onClick={() => setShowConfirm(!showConfirm)} className="password-toggle" tabIndex={-1}>
                    {showConfirm ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                  </button>
                </div>
              </div>
            </div>

            {error && (
              <div className="error-message">
                <AlertCircle className="w-4 h-4" />
                {error}
              </div>
            )}

            <button
              id="signup-submit"
              type="submit"
              disabled={loading}
              className="auth-button"
            >
              {loading ? 'Creating account…' : 'Create Account'}
              <ArrowRight className="w-4 h-4" />
            </button>
          </form>

          <p className="auth-footer">
            Already have an account?{' '}
            <button onClick={onSwitchToLogin} className="auth-link" id="switch-to-login">
              Sign in
            </button>
          </p>
        </div>
      </div>
      <div className="auth-background-shape" />
    </div>
  );
}
