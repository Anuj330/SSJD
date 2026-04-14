import api from './api';

export const ledgerService = {
  async createAccount(accountData) {
    const { data } = await api.post('/api/v1/ledger/accounts/', accountData);
    return data;
  },

  async postJournalEntry(entryData) {
    const { data } = await api.post('/api/v1/ledger/journal/post', entryData);
    return data;
  },

  async reverseEntry(entryId) {
    const { data } = await api.post(`/api/v1/ledger/journal/${entryId}/reverse`);
    return data;
  },

  async getAccountStatement(accountId, fromDate, toDate) {
    const params = {};
    if (fromDate) params.from_date = fromDate;
    if (toDate) params.to_date = toDate;
    const { data } = await api.get(`/api/v1/ledger/accounts/${accountId}/statement`, { params });
    return data;
  },

  async getTrialBalance(asOf) {
    const params = {};
    if (asOf) params.as_of = asOf;
    const { data } = await api.get('/api/v1/ledger/trial-balance', { params });
    return data;
  },
};
