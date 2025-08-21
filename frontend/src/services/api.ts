import axios, { AxiosInstance, AxiosRequestConfig, AxiosResponse } from 'axios';

// Handle different API URLs for server-side (Docker) vs client-side (browser)
const getApiBaseUrl = () => {
  // Check if backend URL is configured
  const backendURL = process.env.NEXT_PUBLIC_BACKEND_URL || process.env.NEXT_PUBLIC_API_URL;
  
  // Server-side rendering (Docker container to Docker container)
  if (typeof window === 'undefined') {
    return backendURL || 'http://localhost:8000';
  }
  
  // Client-side (browser) - prefer backend if configured, otherwise use Next.js API routes
  if (backendURL) {
    return backendURL;
  }
  
  // Try backend on localhost:8000 first, fallback to Next.js API routes
  return 'http://localhost:8000';
};

const API_BASE_URL = getApiBaseUrl();

class ApiService {
  private client: AxiosInstance;

  constructor() {
    this.client = axios.create({
      baseURL: API_BASE_URL, // Use backend URL when available
      timeout: 30000,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // Request interceptor
    this.client.interceptors.request.use(
      (config) => {
        const token = this.getToken();
        if (token) {
          config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
      },
      (error) => Promise.reject(error)
    );

    // Response interceptor
    this.client.interceptors.response.use(
      (response) => response,
      (error) => {
        if (error.response?.status === 401) {
          this.clearToken();
          // Let React components handle the redirect based on auth state
          // Don't force redirect here to avoid conflicts with React Router
        }
        
        // Log CORS and network errors but don't show them to users during development
        if (error.code === 'ERR_NETWORK' || error.message?.includes('CORS')) {
          console.warn('Backend API unavailable, using fallback data:', error.message);
        }
        
        return Promise.reject(error);
      }
    );
  }

  private getToken(): string | null {
    if (typeof window !== 'undefined') {
      return localStorage.getItem('auth_token');
    }
    return null;
  }

  private clearToken(): void {
    if (typeof window !== 'undefined') {
      localStorage.removeItem('auth_token');
      localStorage.removeItem('user_data');
      
      // Update auth store to reflect the logout
      // Import auth store dynamically to avoid SSR issues
      import('@/store/useStore').then((store) => {
        store.useAuthStore.getState().logout();
      }).catch(console.error);
    }
  }

  public setToken(token: string): void {
    if (typeof window !== 'undefined') {
      localStorage.setItem('auth_token', token);
    }
  }

  // Generic request methods
  async get<T>(url: string, config?: AxiosRequestConfig): Promise<T> {
    const response = await this.client.get<T>(url, config);
    return response.data;
  }

  async post<T>(url: string, data?: any, config?: AxiosRequestConfig): Promise<T> {
    const response = await this.client.post<T>(url, data, config);
    return response.data;
  }

  async put<T>(url: string, data?: any, config?: AxiosRequestConfig): Promise<T> {
    const response = await this.client.put<T>(url, data, config);
    return response.data;
  }

  async patch<T>(url: string, data?: any, config?: AxiosRequestConfig): Promise<T> {
    const response = await this.client.patch<T>(url, data, config);
    return response.data;
  }

  async delete<T>(url: string, config?: AxiosRequestConfig): Promise<T> {
    const response = await this.client.delete<T>(url, config);
    return response.data;
  }

  // Health check
  async healthCheck() {
    return this.get('/health/');
  }

  // API status
  async getApiStatus() {
    return this.get('/api/v1/status');
  }

  // User Authentication (within tenant)
  async login(email: string, password: string, tenantId?: string) {
    const headers: any = {};
    if (tenantId) {
      headers['X-Tenant-ID'] = tenantId;
    }
    return this.post('/api/v1/auth/login', { email, password }, { headers });
  }

  async register(userData: {
    email: string;
    password: string;
    shop_name: string;
    first_name: string;
    last_name: string;
    timezone?: string;
    language?: string;
    marketing_consent?: boolean;
    terms_accepted: boolean;
  }, tenantId?: string) {
    const headers: any = {};
    if (tenantId) {
      headers['X-Tenant-ID'] = tenantId;
    }
    return this.post('/api/v1/auth/register', userData, { headers });
  }

  async logout() {
    return this.post('/api/v1/auth/logout');
  }

  async refreshToken() {
    return this.post('/api/v1/auth/refresh');
  }

  // Tenant Authentication
  async tenantRegister(tenantData: {
    company_name: string;
    subdomain: string;
    admin_email: string;
    admin_password: string;
    admin_first_name: string;
    admin_last_name: string;
    subscription_plan?: string;
  }) {
    return this.post('/api/v1/tenants/register', tenantData);
  }

  async tenantLogin(email: string, password: string, subdomain?: string) {
    return this.post('/api/v1/tenants/login', { email, password, subdomain });
  }

  async checkSubdomainAvailability(subdomain: string) {
    return this.get(`/api/v1/tenants/check-subdomain/${subdomain}`);
  }

  // Multi-step tenant registration methods
  async startTenantRegistration(data: {
    company_name: string;
    subdomain: string;
    admin_email: string;
    admin_password: string;
    admin_first_name: string;
    admin_last_name: string;
    selected_integrations: string[];
  }) {
    return this.post('/api/v1/tenants/register/start', data);
  }

  async connectIntegration(data: {
    registration_token: string;
    platform: string;
    oauth_code: string;
    oauth_state: string;
  }) {
    return this.post('/api/v1/tenants/register/connect', data);
  }

  async completeRegistration(data: {
    registration_token: string;
  }) {
    return this.post('/api/v1/tenants/register/complete', data);
  }

  // Dashboard
  async getDashboardData() {
    return this.get('/api/v1/dashboard/');
  }

  async getDashboardAnalytics() {
    return this.get('/api/v1/dashboard/analytics');
  }

  // Shopify Integration
  async getShopifyHealth() {
    return this.get('/api/v1/shopify/health');
  }

  async initShopifyOAuth(shopDomain: string) {
    try {
      // Try backend first (real OAuth)
      const response = await this.post('/api/v1/shopify/oauth/init', { 
        shop_domain: shopDomain,
        redirect_uri: `http://localhost:8000/api/v1/shopify/oauth/callback`
      });
      return response;
    } catch (error: any) {
      // If backend is not available, fallback to Next.js API route (demo)
      if (error.code === 'ECONNREFUSED' || error.response?.status >= 500) {
        console.log('Backend not available, using demo OAuth flow');
        const fallbackClient = axios.create({ baseURL: '' });
        return fallbackClient.post('/api/v1/shopify/oauth/init', { shop_domain: shopDomain });
      }
      throw error;
    }
  }

  async getShopifyIntegrationStatus() {
    try {
      return await this.get('/api/v1/shopify/integration/status');
    } catch (error: any) {
      if (error.code === 'ECONNREFUSED' || error.response?.status >= 500) {
        console.log('Backend not available, using demo integration status');
        const fallbackClient = axios.create({ baseURL: '' });
        return fallbackClient.get('/api/v1/shopify/integration/status');
      }
      throw error;
    }
  }

  async getShopifyProducts() {
    return this.get('/api/v1/shopify/products');
  }

  async getShopifyOrders() {
    return this.get('/api/v1/shopify/orders');
  }

  async getShopifyCollections() {
    return this.get('/api/v1/shopify/collections');
  }

  async createShopifyProduct(productData: any) {
    return this.post('/api/v1/shopify/products', productData);
  }

  async batchUpdateShopifyProducts(updates: any[]) {
    return this.post('/api/v1/shopify/products/batch-update', { updates });
  }

  // Etsy Integration
  async getEtsyHealth() {
    return this.get('/api/v1/etsy/health');
  }

  async initEtsyOAuth() {
    try {
      // Try backend first (real OAuth)
      const response = await this.post('/api/v1/etsy/oauth/init', {
        redirect_uri: `http://localhost:8000/api/v1/etsy/oauth/callback`
      });
      return response;
    } catch (error: any) {
      // If backend is not available, fallback to Next.js API route (demo)
      if (error.code === 'ECONNREFUSED' || error.response?.status >= 500) {
        console.log('Backend not available, using demo OAuth flow');
        const fallbackClient = axios.create({ baseURL: '' });
        return fallbackClient.post('/api/v1/etsy/oauth/init', {});
      }
      throw error;
    }
  }

  async getEtsyIntegrationStatus() {
    try {
      return await this.get('/api/v1/etsy/verify-connection');
    } catch (error: any) {
      if (error.code === 'ECONNREFUSED' || error.response?.status >= 500) {
        console.log('Backend not available, using demo integration status');
        const fallbackClient = axios.create({ baseURL: '' });
        return fallbackClient.get('/api/v1/etsy/integration/status');
      }
      throw error;
    }
  }

  async getEtsyOAuthData() {
    try {
      return await this.get('/api/v1/etsy/oauth-data');
    } catch (error: any) {
      if (error.code === 'ECONNREFUSED' || error.response?.status >= 500) {
        console.log('Backend not available, using demo OAuth data');
        // Return demo OAuth data
        return {
          clientId: 'demo-client-id',
          redirectUri: `${window.location.origin}/oauth/redirect`,
          codeChallenge: 'demo-challenge',
          state: 'demo-state',
          scopes: 'listings_w listings_r shops_r shops_w transactions_r',
          codeChallengeMethod: 'S256',
          responseType: 'code',
          oauthConnectUrl: 'https://www.etsy.com/oauth/connect'
        };
      }
      throw error;
    }
  }

  async handleEtsyOAuthCallback(code: string) {
    try {
      return await this.get(`/api/v1/etsy/oauth-redirect?code=${encodeURIComponent(code)}`);
    } catch (error: any) {
      if (error.code === 'ECONNREFUSED' || error.response?.status >= 500) {
        console.log('Backend not available, using demo OAuth callback');
        const fallbackClient = axios.create({ baseURL: '' });
        return fallbackClient.get(`/api/v1/etsy/oauth/callback?code=${encodeURIComponent(code)}`);
      }
      throw error;
    }
  }

  async disconnectEtsy() {
    try {
      return await this.post('/api/v1/etsy/revoke-token', {});
    } catch (error: any) {
      if (error.code === 'ECONNREFUSED' || error.response?.status >= 500) {
        console.log('Backend not available, using demo disconnect');
        return { success: true, message: 'Disconnected (demo mode)' };
      }
      throw error;
    }
  }

  async getEtsyListings() {
    return this.get('/api/v1/etsy/listings');
  }

  async getEtsyOrders() {
    return this.get('/api/v1/etsy/orders');
  }

  // Templates
  async getTemplates() {
    return this.get('/api/v1/templates');
  }

  async createTemplate(templateData: any) {
    return this.post('/api/v1/templates', templateData);
  }

  async updateTemplate(id: string, templateData: any) {
    return this.put(`/api/v1/templates/${id}`, templateData);
  }

  async deleteTemplate(id: string) {
    return this.delete(`/api/v1/templates/${id}`);
  }

  async getTemplate(id: string) {
    return this.get(`/api/v1/templates/${id}`);
  }

  // Orders
  async getOrders() {
    return this.get('/api/v1/orders');
  }

  async getOrder(id: string) {
    return this.get(`/api/v1/orders/${id}`);
  }

  async updateOrder(id: string, orderData: any) {
    return this.put(`/api/v1/orders/${id}`, orderData);
  }

  async getOrderPreview(orderId: string) {
    return this.get(`/api/v1/orders/${orderId}/preview`);
  }

  // Tenant Management
  async getTenants() {
    return this.get('/api/v1/tenants');
  }

  async createTenant(tenantData: any) {
    return this.post('/api/v1/tenants', tenantData);
  }

  async updateTenant(id: string, tenantData: any) {
    return this.put(`/api/v1/tenants/${id}`, tenantData);
  }

  async deleteTenant(id: string) {
    return this.delete(`/api/v1/tenants/${id}`);
  }

  async getTenantUsers(tenantId: string) {
    return this.get(`/api/v1/tenants/${tenantId}/users`);
  }

  async getTenantUsage(tenantId: string) {
    return this.get(`/api/v1/tenants/${tenantId}/usage`);
  }
}

export const apiService = new ApiService();
export default apiService;