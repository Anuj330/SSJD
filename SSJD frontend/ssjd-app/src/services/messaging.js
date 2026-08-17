import api from './api';

export const messagingService = {
  async status() { return (await api.get('/api/v1/messaging/status')).data; },
  async contacts() { return (await api.get('/api/v1/messaging/contacts')).data; },
  async send(memberId, channel, message) {
    return (await api.post('/api/v1/messaging/send', null, { params: { member_id: memberId, channel, message } })).data;
  },
  async sendBulk(channel, message) {
    return (await api.post('/api/v1/messaging/send-bulk', null, { params: { channel, message } })).data;
  },
};
