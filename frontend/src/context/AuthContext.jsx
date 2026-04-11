import { createContext, useContext, useState, useCallback } from 'react';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [token, setToken] = useState(() => localStorage.getItem('lazarus_token') || null);
  const [user, setUser] = useState(() => {
    const saved = localStorage.getItem('lazarus_user');
    return saved ? JSON.parse(saved) : null;
  });

  const login = useCallback((accessToken, userData) => {
    localStorage.setItem('lazarus_token', accessToken);
    localStorage.setItem('lazarus_user', JSON.stringify(userData));
    setToken(accessToken);
    setUser(userData);
  }, []);

  const logout = useCallback(() => {
    localStorage.removeItem('lazarus_token');
    localStorage.removeItem('lazarus_user');
    setToken(null);
    setUser(null);
  }, []);

  const isAuthenticated = !!token;

  return (
    <AuthContext.Provider value={{ token, user, login, logout, isAuthenticated }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used within AuthProvider');
  return ctx;
}
