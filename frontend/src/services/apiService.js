import axios from 'axios';

class ApiService {
  constructor() {
    this.baseUrl = process.env.REACT_APP_API_BASE_URL || 'http://localhost:3003';
    this.client = axios.create({
      baseURL: this.baseUrl,
      timeout: 10000,
    });

    // Add tenant header to all requests
    this.client.interceptors.request.use((config) => {
      const tenant = this.getCurrentTenant();
      if (tenant) {
        config.headers['X-Tenant-ID'] = tenant.id;
      }
      const token = localStorage.getItem('auth_token');
      if (token) {
        config.headers.Authorization = `Bearer ${token}`;
      }
      return config;
    });

    // Handle tenant-specific errors
    this.client.interceptors.response.use(
      (response) => response,
      (error) => {
        if (error.response?.status === 403) {
          // Tenant access denied
          window.location.href = '/unauthorized';
        }
        return Promise.reject(error);
      }
    );
  }

  getCurrentTenant() {
    // Extract from URL or context
    const hostname = window.location.hostname;
    const subdomain = hostname.split('.')[0];
    return { id: subdomain };
  }

  // Etsy-specific API methods
  async getShopAnalytics(params = {}) {
    const response = await this.client.get('/api/shop-analytics', { params });
    return response.data;
  }

  async getTopSellers(year) {
    const response = await this.client.get(`/api/top-sellers?year=${year}`);
    return response.data;
  }

  async getLocalImages() {
    const response = await this.client.get('/api/local-images');
    return response.data;
  }

  async saveMaskData(maskData) {
    const response = await this.client.post('/api/masks', maskData);
    return response.data;
  }
}

export const apiService = new ApiService();