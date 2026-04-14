import api from './api';

export const reportsService = {
  async profitLoss(fromDate, toDate) {
    const params = {};
    if (fromDate) params.from_date = fromDate;
    if (toDate) params.to_date = toDate;
    return (await api.get('/api/v1/reports/profit-loss', { params })).data;
  },
  async balanceSheet(asOf) {
    const params = {};
    if (asOf) params.as_of = asOf;
    return (await api.get('/api/v1/reports/balance-sheet', { params })).data;
  },
  async cashFlow(fromDate, toDate) {
    const params = {};
    if (fromDate) params.from_date = fromDate;
    if (toDate) params.to_date = toDate;
    return (await api.get('/api/v1/reports/cash-flow', { params })).data;
  },
  async memberOutstanding() { return (await api.get('/api/v1/reports/member-outstanding')).data; },
  async batchInterest(asOf) {
    const params = {};
    if (asOf) params.as_of = asOf;
    return (await api.post('/api/v1/reports/batch-interest', null, { params })).data;
  },

  // Activity & Receipts
  async activityLogs(params = {}) { return (await api.get('/api/v1/activity-logs/', { params })).data; },
  async getReceipt(entryId) { return (await api.get(`/api/v1/receipts/${entryId}`)).data; },

  // Analytics
  async dashboardKPIs() { return (await api.get('/api/v1/analytics/dashboard')).data; },
  async calculateDividend(rate, year, post = false) {
    return (await api.post('/api/v1/analytics/dividend', null, {
      params: { dividend_rate: rate, financial_year: year, post_entries: post }
    })).data;
  },
};
