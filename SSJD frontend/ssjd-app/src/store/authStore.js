import { create } from 'zustand';
import { authService } from '../services/auth';

function parseJwt(token) {
  try {
    const base64 = token.split('.')[1].replace(/-/g, '+').replace(/_/g, '/');
    return JSON.parse(atob(base64));
  } catch {
    return null;
  }
}

function getInitialState() {
  const token = localStorage.getItem('access_token');
  if (!token) return { token: null, role: null, memberId: null, sub: null, isAuthenticated: false };
  const payload = parseJwt(token);
  if (!payload || (payload.exp && payload.exp * 1000 < Date.now())) {
    localStorage.removeItem('access_token');
    return { token: null, role: null, memberId: null, sub: null, isAuthenticated: false };
  }
  return {
    token,
    role: payload.role || null,
    memberId: payload.member_id || null,
    sub: payload.sub || null,
    isAuthenticated: true,
  };
}

const initial = getInitialState();

export const useAuthStore = create((set) => ({
  ...initial,
  loading: false,
  error: null,

  adminLogin: async (email, password) => {
    set({ loading: true, error: null });
    try {
      const data = await authService.adminLogin(email, password);
      const payload = parseJwt(data.access_token);
      localStorage.setItem('access_token', data.access_token);
      set({
        token: data.access_token,
        role: payload?.role || 'admin',
        memberId: null,
        sub: payload?.sub || null,
        isAuthenticated: true,
        loading: false,
      });
      return data;
    } catch (err) {
      const message = err.response?.data?.detail || 'Login failed';
      set({ error: message, loading: false });
      throw err;
    }
  },

  memberLogin: async (username, password) => {
    set({ loading: true, error: null });
    try {
      const data = await authService.memberLogin(username, password);
      const payload = parseJwt(data.access_token);
      localStorage.setItem('access_token', data.access_token);
      set({
        token: data.access_token,
        role: payload?.role || 'member',
        memberId: payload?.member_id || null,
        sub: payload?.sub || null,
        isAuthenticated: true,
        loading: false,
      });
      return data;
    } catch (err) {
      const message = err.response?.data?.detail || 'Login failed';
      set({ error: message, loading: false });
      throw err;
    }
  },

  logout: () => {
    localStorage.removeItem('access_token');
    set({ token: null, role: null, memberId: null, sub: null, isAuthenticated: false, error: null });
  },

  clearError: () => set({ error: null }),
}));
