// config/environment.js
const environments = {
  development: {
    API_BASE_URL: 'http://localhost:3003',
    TENANT_MODE: 'single',
    DEBUG: true,
    CACHE_TTL: 60000, // 1 minute
  },
  production: {
    API_BASE_URL: process.env.REACT_APP_API_BASE_URL || 'http://your-qnap-ip:3003',
    TENANT_MODE: 'multi',
    DEBUG: false,
    CACHE_TTL: 300000, // 5 minutes
  },
  qnap: {
    API_BASE_URL: 'http://192.168.1.100:3003', // Your QNAP IP
    TENANT_MODE: 'multi',
    DEBUG: false,
    CACHE_TTL: 600000, // 10 minutes
    ENABLE_ANALYTICS: true,
  }
};

export const config = environments[process.env.NODE_ENV] || environments.development;