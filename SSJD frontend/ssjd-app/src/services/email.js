import api from './api';

export const emailService = {
  listMembersWithEmail: () => api.get('/email/members').then(r => r.data),

  send: (memberId, subject, message) =>
    api.post('/email/send', null, {
      params: { member_id: memberId, subject, message },
    }).then(r => r.data),

  sendBulk: (subject, message) =>
    api.post('/email/send-bulk', null, {
      params: { subject, message },
    }).then(r => r.data),
};
