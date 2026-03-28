import axios from 'axios';

const api = axios.create({
  baseURL: '/api',
  headers: { 'Content-Type': 'application/json' },
});

// Calls
export const getCalls = (params = {}) => api.get('/calls', { params });
export const getCallStats = () => api.get('/calls/stats');
export const getCall = (id) => api.get(`/calls/${id}`);

// Profiles
export const getProfiles = () => api.get('/profiles');
export const getProfile = (id) => api.get(`/profiles/${id}`);
export const createProfile = (data) => api.post('/profiles', data);
export const updateProfile = (id, data) => api.put(`/profiles/${id}`, data);
export const addProject = (profileId, data) => api.post(`/profiles/${profileId}/projects`, data);

// Matches
export const getMatches = (params) => api.get('/matches', { params });
export const getMatchStats = (profileId) => api.get('/matches/stats', { params: { profile_id: profileId } });
export const bookmarkMatch = (id) => api.post(`/matches/${id}/bookmark`);
export const dismissMatch = (id) => api.post(`/matches/${id}/dismiss`);

// Filters
export const getFilters = (profileId) => api.get('/filters', { params: { profile_id: profileId } });
export const createFilter = (profileId, data) => api.post('/filters', data, { params: { profile_id: profileId } });

// Pipeline
export const runPipeline = (daysBack = 1) => api.post('/pipeline/run', null, { params: { days_back: daysBack } });
export const getPipelineStatus = () => api.get('/pipeline/status');

// Feedback
export const submitFeedback = (data) => api.post('/feedback', data);
export const getFeedback = () => api.get('/feedback');
export const markReviewed = (id) => api.post(`/feedback/${id}/review`);

export default api;
