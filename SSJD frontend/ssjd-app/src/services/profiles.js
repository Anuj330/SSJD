import api from './api';

export const profilesService = {
  async list() {
    const { data } = await api.get('/api/v1/member-profiles/');
    return data;
  },

  async get(profileId) {
    const { data } = await api.get(`/api/v1/member-profiles/${profileId}`);
    return data;
  },

  async create(profileData) {
    const { data } = await api.post('/api/v1/member-profiles/', profileData);
    return data;
  },

  async update(profileId, profileData) {
    const { data } = await api.put(`/api/v1/member-profiles/${profileId}`, profileData);
    return data;
  },
};
