import api from './api';

export const sharesService = {
  async getMemberShares(memberId) { return (await api.get(`/api/v1/members/${memberId}/shares`)).data; },
  async getShareInterest(memberId, rate) {
    const params = rate ? { rate } : {};
    return (await api.get(`/api/v1/members/${memberId}/share-interest`, { params })).data;
  },
  async addShareMoney(memberId, { amount, cd_amount, od_amount, remarks, txnDate }) {
    return (await api.post(`/api/v1/members/${memberId}/shares/purchase`, null, { params: {
      amount, cd_amount, od_amount, remarks: remarks || undefined, txn_date: txnDate || undefined,
    } })).data;
  },
  async withdrawShareMoney(memberId, amount, remarks) {
    return (await api.post(`/api/v1/members/${memberId}/shares/refund`, null, { params: { amount, remarks: remarks || undefined } })).data;
  },
  async listAll() { return (await api.get('/api/v1/shares/')).data; },

  // RD
  async generateRDInstallments(depositId) { return (await api.post(`/api/v1/deposits/${depositId}/rd/generate`)).data; },
  async payRDInstallment(depositId, amount) { return (await api.post(`/api/v1/deposits/${depositId}/rd/pay`, null, { params: { amount } })).data; },
  async getRDSchedule(depositId) { return (await api.get(`/api/v1/deposits/${depositId}/rd/schedule`)).data; },
};
