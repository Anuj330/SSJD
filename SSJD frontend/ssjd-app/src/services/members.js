import api from './api';

export const membersService = {
  async list() {
    const { data } = await api.get('/api/v1/members/');
    return data;
  },

  async get(memberId) {
    const { data } = await api.get(`/api/v1/members/${memberId}`);
    return data;
  },

  async create(memberData) {
    const { data } = await api.post('/api/v1/members/', memberData);
    return data;
  },

  async update(memberId, memberData) {
    const { data } = await api.put(`/api/v1/members/${memberId}`, memberData);
    return data;
  },

  async deactivate(memberId) {
    const { data } = await api.delete(`/api/v1/members/${memberId}`);
    return data;
  },

  async getMoneyFlow(memberId, fromDate, toDate) {
    const params = {};
    if (fromDate) params.from_date = fromDate;
    if (toDate) params.to_date = toDate;
    const { data } = await api.get(`/api/v1/members/${memberId}/money-flow`, { params });
    return data;
  },

  async getPassbook(memberId, fromDate, toDate) {
    const params = {};
    if (fromDate) params.from_date = fromDate;
    if (toDate) params.to_date = toDate;
    const { data } = await api.get(`/api/v1/members/${memberId}/passbook`, { params });
    return data;
  },
};
