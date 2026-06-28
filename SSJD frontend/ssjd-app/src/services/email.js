import api from './api';

export const emailService = {
  listMembersWithEmail: () => api.get('/api/v1/email/members').then(r => r.data),

  send: (memberId, subject, message) =>
    api.post('/api/v1/email/send', null, {
      params: { member_id: memberId, subject, message },
    }).then(r => r.data),

  sendBulk: (subject, message) =>
    api.post('/api/v1/email/send-bulk', null, {
      params: { subject, message },
    }).then(r => r.data),
};
