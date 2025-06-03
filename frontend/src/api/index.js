import axios from 'axios';
import {SERVER_URL} from "@src/config";

const api = axios.create({
    baseURL: SERVER_URL,
    timeout: 10000
});

api.interceptors.request.use(config => {
    const token = localStorage.getItem('token');
    if (token) {
        config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
}, error => {
    return Promise.reject(error);
});

api.interceptors.response.use(response => response, error => {
    if (error.response?.status === 401) {
        localStorage.removeItem('token');
        window.location.reload();
    }
    return Promise.reject(error);
});

export default api;