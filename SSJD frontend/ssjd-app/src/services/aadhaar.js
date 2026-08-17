import api from './api';

export const aadhaarService = {
  async upload({ name, aadhaarNumber, dob, file }) {
    const fd = new FormData();
    fd.append('name', name);
    fd.append('aadhaar_number', aadhaarNumber);
    if (dob) fd.append('dob', dob);
    fd.append('file', file);
    const { data } = await api.post('/api/v1/aadhaar/upload', fd, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return data;
  },
  async list(status) {
    const params = status ? { status } : {};
    return (await api.get('/api/v1/aadhaar/', { params })).data;
  },
  async get(id) { return (await api.get(`/api/v1/aadhaar/${id}`)).data; },
  async imageObjectUrl(id) {
    const res = await api.get(`/api/v1/aadhaar/${id}/image`, { responseType: 'blob' });
    return URL.createObjectURL(res.data);
  },
  async link(id, memberId, basis) {
    return (await api.post(`/api/v1/aadhaar/${id}/link`, null, { params: { member_id: memberId, basis } })).data;
  },
  async approve(id) { return (await api.post(`/api/v1/aadhaar/${id}/approve`)).data; },
  async reject(id, remarks) { return (await api.post(`/api/v1/aadhaar/${id}/reject`, null, { params: { remarks } })).data; },
  async defer(id, remarks) { return (await api.post(`/api/v1/aadhaar/${id}/defer`, null, { params: { remarks } })).data; },
  async unlink(id) { return (await api.post(`/api/v1/aadhaar/${id}/unlink`)).data; },
};
