import api from './api';

export const sharesService = {
  async getMemberShares(memberId) { return (await api.get(`/api/v1/members/${memberId}/shares`)).data; },
  async purchaseShares(memberId, shares, faceValue = 10) {
    return (await api.post(`/api/v1/members/${memberId}/shares/purchase`, null, { params: { shares, face_value: faceValue } })).data;
  },
  async refundShares(memberId, shares) {
    return (await api.post(`/api/v1/members/${memberId}/shares/refund`, null, { params: { shares } })).data;
  },
  async listAll() { return (await api.get('/api/v1/shares/')).data; },

  // RD
  async generateRDInstallments(depositId) { return (await api.post(`/api/v1/deposits/${depositId}/rd/generate`)).data; },
  async payRDInstallment(depositId, amount) { return (await api.post(`/api/v1/deposits/${depositId}/rd/pay`, null, { params: { amount } })).data; },
  async getRDSchedule(depositId) { return (await api.get(`/api/v1/deposits/${depositId}/rd/schedule`)).data; },
};
