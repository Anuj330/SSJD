import api from './api';

export const collectionsService = {
  // Record one collection split across loan EMI / share money / advance wallet.
  async collect(memberId, data) {
    return (await api.post(`/api/v1/members/${memberId}/collect`, data)).data;
  },
  // Member's advance (adjust-balance) wallet + history.
  async getAdvance(memberId) {
    return (await api.get(`/api/v1/members/${memberId}/advance`)).data;
  },
};
