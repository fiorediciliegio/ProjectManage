import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000';

const normalizeUrl = (url) => {
  if (!url) {
    return url;
  }

  return url.replace(/^https?:\/\/(127\.0\.0\.1|localhost):8000/i, API_BASE_URL);
};

export const getCsrfToken = () => {
  const match = document.cookie.match(/(?:^|; )csrftoken=([^;]+)/);
  return match ? decodeURIComponent(match[1]) : '';
};

const api = axios.create({
  baseURL: API_BASE_URL,
  withCredentials: true,
});

api.interceptors.request.use((config) => {
  config.url = normalizeUrl(config.url);
  config.withCredentials = true;

  const method = (config.method || 'get').toLowerCase();
  if (method !== 'get' && method !== 'head' && method !== 'options') {
    const csrfToken = getCsrfToken();
    if (csrfToken) {
      config.headers = config.headers || {};
      config.headers['X-CSRFToken'] = csrfToken;
    }
  }

  return config;
});

export { API_BASE_URL };
export default api;
