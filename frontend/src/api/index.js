import axios from 'axios';

import {TOKEN} from '@src/config';
import {HOST} from '@api/path';

const api = axios.create({
  baseURL: HOST,
  timeout: 30000,
});

api.interceptors.request.use(config => {
  const token = localStorage.getItem(TOKEN);
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
}, error => {
  return Promise.reject(error);
});

api.interceptors.response.use(response => response, error => {
  if ([401, 403].includes(error.response?.status)) {
    localStorage.removeItem(TOKEN);
  }
  return Promise.reject(error);
});

export default api;