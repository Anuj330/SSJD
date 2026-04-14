import api from './api';

export const schemesService = {
  async list() {
    const { data } = await api.get('/api/v1/schemes/');
    return data;
  },

  async get(schemeId) {
    const { data } = await api.get(`/api/v1/schemes/${schemeId}`);
    return data;
  },

  async create(schemeData) {
    const { data } = await api.post('/api/v1/schemes/', schemeData);
    return data;
  },

  async update(schemeId, schemeData) {
    const { data } = await api.put(`/api/v1/schemes/${schemeId}`, schemeData);
    return data;
  },
};
