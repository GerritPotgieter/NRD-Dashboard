import axios from 'axios';
import apiCache from '../utils/cache';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API_BASE = `${BACKEND_URL}/api`;

const api = axios.create({
  baseURL: API_BASE,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Domain APIs
export const getDomains = async (params = {}) => {
  // Check cache first
  const cacheKey = apiCache.generateKey('domains', params);
  const cached = apiCache.get(cacheKey);

  if (cached) {
    return cached;
  }

  // Fetch from API
  const response = await api.get('/domains', { params });

  // Cache the result (30 seconds TTL)
  apiCache.set(cacheKey, response.data, 30000);

  return response.data;
};

export const getDomain = async (domain) => {
  // Check cache first
  const cacheKey = apiCache.generateKey('domain', { domain });
  const cached = apiCache.get(cacheKey);

  if (cached) {
    return cached;
  }

  // Fetch from API
  const response = await api.get(`/domains/${domain}`);

  // Cache the result (60 seconds TTL)
  apiCache.set(cacheKey, response.data, 60000);

  return response.data;
};

export const updateDomain = async (domain, data) => {
  const response = await api.put(`/domains/${domain}`, data);

  // Clear cache for this domain and domain list
  apiCache.clearPrefix('domain');
  apiCache.clearPrefix('domains');
  apiCache.clearPrefix('stats');

  return response.data;
};

export const deleteDomain = async (domain) => {
  const response = await api.delete(`/domains/${domain}`);

  // Clear cache for domain list
  apiCache.clearPrefix('domains');
  apiCache.clearPrefix('stats');

  return response.data;
};

export const getDomainHistory = async (domain, limit = 50) => {
  // Check cache first
  const cacheKey = apiCache.generateKey('history', { domain, limit });
  const cached = apiCache.get(cacheKey);

  if (cached) {
    return cached;
  }

  // Fetch from API
  const response = await api.get(`/domains/${domain}/history`, { params: { limit } });

  // Cache the result (60 seconds TTL)
  apiCache.set(cacheKey, response.data, 60000);

  return response.data;
};

export const addToIgnoreList = async (domain) => {
  const response = await api.post(`/domains/${domain}/ignore`);
  return response.data;
};

// Statistics APIs
export const getStats = async () => {
  // Check cache first
  const cacheKey = apiCache.generateKey('stats', {});
  const cached = apiCache.get(cacheKey);

  if (cached) {
    return cached;
  }

  // Fetch from API
  const response = await api.get('/stats');

  // Cache the result (30 seconds TTL)
  apiCache.set(cacheKey, response.data, 30000);

  return response.data;
};

export const getRecentActivity = async (limit = 20) => {
  // Check cache first
  const cacheKey = apiCache.generateKey('recent-activity', { limit });
  const cached = apiCache.get(cacheKey);

  if (cached) {
    return cached;
  }

  // Fetch from API
  const response = await api.get('/analytics/recent-activity', { params: { limit } });

  // Cache the result (30 seconds TTL)
  apiCache.set(cacheKey, response.data, 30000);

  return response.data;
};

export const getRecentChanges = async (limit = 10) => {
  // Check cache first
  const cacheKey = apiCache.generateKey('recent-changes', { limit });
  const cached = apiCache.get(cacheKey);

  if (cached) {
    return cached;
  }

  // Fetch from API
  const response = await api.get('/analytics/recent-changes', { params: { limit } });

  // Cache the result (30 seconds TTL)
  apiCache.set(cacheKey, response.data, 30000);

  return response.data;
};

export const getCategoryStats = async () => {
  // Check cache first
  const cacheKey = apiCache.generateKey('category-stats', {});
  const cached = apiCache.get(cacheKey);

  if (cached) {
    return cached;
  }

  // Fetch from API
  const response = await api.get('/analytics/by-category');

  // Cache the result (30 seconds TTL)
  apiCache.set(cacheKey, response.data, 30000);

  return response.data;
};

export const getTimeline = async (days = 30) => {
  // Check cache first
  const cacheKey = apiCache.generateKey('timeline', { days });
  const cached = apiCache.get(cacheKey);

  if (cached) {
    return cached;
  }

  // Fetch from API
  const response = await api.get('/analytics/timeline', { params: { days } });

  // Cache the result (60 seconds TTL)
  apiCache.set(cacheKey, response.data, 60000);

  return response.data;
};

// Pattern APIs
export const getPatterns = async () => {
  const response = await api.get('/patterns');
  return response.data;
};

export const updatePattern = async (patternName, patterns) => {
  const response = await api.put(`/patterns/${patternName}`, patterns);
  return response.data;
};

// Whitelist APIs
export const getIgnoreDomains = async () => {
  const response = await api.get('/whitelist/ignore');
  return response.data;
};

export const addIgnoreDomain = async (domain) => {
  const response = await api.post('/whitelist/ignore', { domain });
  return response.data;
};

export const removeIgnoreDomain = async (domain) => {
  const response = await api.delete(`/whitelist/ignore/${domain}`);
  return response.data;
};

export const getIncludedDomains = async () => {
  const response = await api.get('/whitelist/included');
  return response.data;
};

// Workflow APIs
export const triggerWorkflow = async () => {
  const response = await api.post('/workflow/run');
  return response.data;
};

export const getWorkflowStatus = async () => {
  const response = await api.get('/workflow/status');
  return response.data;
};

// Export APIs
export const exportToCSV = async (params = {}) => {
  const response = await api.get('/export/csv', {
    params,
    responseType: 'blob'
  });
  return response.data;
};

export const exportToJSON = async (params = {}) => {
  const response = await api.get('/export/json', {
    params,
    responseType: 'blob'
  });
  return response.data;
};

// Screenshot APIs
export const getScreenshots = async (domain) => {
  // Check cache first
  const cacheKey = apiCache.generateKey('screenshots', { domain });
  const cached = apiCache.get(cacheKey);

  if (cached) {
    return cached;
  }

  // Fetch from API
  const response = await api.get(`/screenshots/${domain}`);

  // Cache the result (120 seconds TTL - screenshots don't change often)
  apiCache.set(cacheKey, response.data, 120000);

  return response.data;
};

export const captureScreenshot = async (domain) => {
  const response = await api.post(`/screenshots/${domain}/capture`);

  // Clear screenshot cache for this domain
  const cacheKey = apiCache.generateKey('screenshots', { domain });
  apiCache.clear(cacheKey);

  return response.data;
};

export const getScreenshotUrl = (domain, filename) => {
  return `${API_BASE}/screenshots/${domain}/${filename}`;
};

// Domain Profile APIs
export const getDomainProfile = async (domain) => {
  // Check cache first
  const cacheKey = apiCache.generateKey('profile', { domain });
  const cached = apiCache.get(cacheKey);

  if (cached) {
    return cached;
  }

  // Fetch from API
  const response = await api.get(`/domains/${domain}/profile`);

  // Cache the result (300 seconds TTL - profiles don't change often)
  apiCache.set(cacheKey, response.data, 300000);

  return response.data;
};

export const generateDomainProfile = async (domain) => {
  const response = await api.post(`/domains/${domain}/profile/generate`);

  // Clear profile cache for this domain
  const cacheKey = apiCache.generateKey('profile', { domain });
  apiCache.clear(cacheKey);

  // Clear domain cache (has_profile flag may change)
  apiCache.clearPrefix('domain');
  apiCache.clearPrefix('domains');

  return response.data;
};

export const syncDomainProfiles = async () => {
  const response = await api.post('/domains/profiles/sync');

  // Clear all domain caches since has_profile flags may have changed
  apiCache.clearPrefix('domain');
  apiCache.clearPrefix('domains');

  return response.data;
};

// Export cache utility for manual cache control
export { apiCache };

export default api;