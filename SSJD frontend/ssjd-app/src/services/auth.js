import api from './api';

export const authService = {
  async adminLogin(email, password) {
    const { data } = await api.post(`/auth/login?email=${encodeURIComponent(email)}&password=${encodeURIComponent(password)}`);
    return data;
  },

  async memberLogin(username, password) {
    const { data } = await api.post('/api/v1/member/login', { username, password });
    return data;
  },

  async createUser(userData) {
    const { data } = await api.post('/users/', userData);
    return data;
  },
};
