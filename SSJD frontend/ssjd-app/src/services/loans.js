import api from './api';

export const loansService = {
  // Products
  async listProducts() { return (await api.get('/api/v1/loan-products/')).data; },
  async getProduct(id) { return (await api.get(`/api/v1/loan-products/${id}`)).data; },
  async createProduct(data) { return (await api.post('/api/v1/loan-products/', data)).data; },
  async updateProduct(id, data) { return (await api.put(`/api/v1/loan-products/${id}`, data)).data; },

  // Loan operations
  async apply(data) { return (await api.post('/api/v1/loans/apply', data)).data; },
  async list(params = {}) { return (await api.get('/api/v1/loans/', { params })).data; },
  async get(id) { return (await api.get(`/api/v1/loans/${id}`)).data; },
  async approve(id, data) { return (await api.post(`/api/v1/loans/${id}/approve`, data)).data; },
  async reject(id, remarks) { return (await api.post(`/api/v1/loans/${id}/reject`, null, { params: { remarks } })).data; },
  async disburse(id) { return (await api.post(`/api/v1/loans/${id}/disburse`)).data; },
  async repay(id, data) { return (await api.post(`/api/v1/loans/${id}/repay`, data)).data; },
  async getSchedule(id) { return (await api.get(`/api/v1/loans/${id}/schedule`)).data; },
};
