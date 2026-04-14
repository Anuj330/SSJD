import api from './api';

export const depositsService = {
  async list(params = {}) {
    const { data } = await api.get('/api/v1/deposits/', { params });
    return data;
  },

  async get(depositId) {
    const { data } = await api.get(`/api/v1/deposits/${depositId}`);
    return data;
  },

  async open(depositData) {
    const { data } = await api.post('/api/v1/deposits/open', depositData);
    return data;
  },

  async deposit(depositId, txnData) {
    const { data } = await api.post(`/api/v1/deposits/${depositId}/deposit`, txnData);
    return data;
  },

  async withdraw(depositId, txnData) {
    const { data } = await api.post(`/api/v1/deposits/${depositId}/withdraw`, txnData);
    return data;
  },

  async close(depositId) {
    const { data } = await api.post(`/api/v1/deposits/${depositId}/close`);
    return data;
  },

  async calculateInterest(depositId, asOf) {
    const params = {};
    if (asOf) params.as_of = asOf;
    const { data } = await api.post(`/api/v1/deposits/${depositId}/calculate-interest`, null, { params });
    return data;
  },

  async getStatement(depositId, fromDate, toDate) {
    const params = {};
    if (fromDate) params.from_date = fromDate;
    if (toDate) params.to_date = toDate;
    const { data } = await api.get(`/api/v1/deposits/${depositId}/statement`, { params });
    return data;
  },
};
