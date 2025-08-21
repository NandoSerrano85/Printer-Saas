import axios, { AxiosInstance, AxiosResponse, AxiosRequestConfig } from 'axios';
import { ApiResponse, Tenant, AnalyticsData } from '@/types';

interface TenantInfo {
  id: string;
}

interface ShopAnalyticsParams {
  startDate?: string;
  endDate?: string;
  period?: 'day' | 'week' | 'month' | 'year';
}

interface TopSellersResponse {
  products: Array<{
    id: string;
    title: string;
    sales: number;
    revenue: number;
  }>;
  total: number;
}

interface LocalImagesResponse {
  images: Array<{
    id: string;
    filename: string;
    url: string;
    size: number;
    mimeType: string;
    createdAt: string;
  }>;
}

interface MaskData {
  name: string;
  data: any; // JSON data for mask configuration
  thumbnail?: string;
  category?: string;
}

// Multi-step registration interfaces
interface TenantRegistrationStep1Request {
  subdomain: string;
  company_name: string;
  admin_email: string;
  admin_password: string;
  admin_first_name: string;
  admin_last_name: string;
  selected_integrations: string[];
}

interface TenantRegistrationStep1Response {
  success: boolean;
  message: string;
  tenant_id: string;
  registration_token: string;
  oauth_urls: Record<string, string>;
  expires_in: number;
}

interface IntegrationConnectRequest {
  registration_token: string;
  platform: string;
  oauth_code: string;
  oauth_state: string;
}

interface IntegrationConnectResponse {
  success: boolean;
  message: string;
  platform: string;
  shop_name?: string;
  remaining_integrations: string[];
}

interface CompleteRegistrationRequest {
  registration_token: string;
}

interface CompleteRegistrationResponse {
  success: boolean;
  message: string;
  tenant: any;
  user: any;
  tokens: any;
  connected_integrations: string[];
}

class ApiService {
  private baseUrl: string;
  private client: AxiosInstance;

  constructor() {
    this.baseUrl = process.env.REACT_APP_API_BASE_URL || 'http://localhost:3003';
    this.client = axios.create({
      baseURL: this.baseUrl,
      timeout: 10000,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // Add tenant header to all requests
    this.client.interceptors.request.use((config: AxiosRequestConfig) => {
      const tenant = this.getCurrentTenant();
      if (tenant) {
        config.headers = {
          ...config.headers,
          'X-Tenant-ID': tenant.id,
        };
      }
      
      const token = localStorage.getItem('auth_token');
      if (token) {
        config.headers = {
          ...config.headers,
          Authorization: `Bearer ${token}`,
        };
      }
      
      return config;
    });

    // Handle tenant-specific errors
    this.client.interceptors.response.use(
      (response: AxiosResponse) => response,
      (error) => {
        if (error.response?.status === 403) {
          // Tenant access denied
          window.location.href = '/unauthorized';
        } else if (error.response?.status === 401) {
          // Authentication required
          localStorage.removeItem('auth_token');
          window.location.href = '/login';
        }
        return Promise.reject(error);
      }
    );
  }

  getCurrentTenant(): TenantInfo | null {
    try {
      // Extract from URL or context
      const hostname = window.location.hostname;
      const subdomain = hostname.split('.')[0];
      
      // Don't treat localhost, IPs, or common domains as subdomains
      if (['localhost', '127', '0', 'www'].includes(subdomain) || 
          /^\d+$/.test(subdomain.split('.')[0])) {
        return { id: 'demo' }; // Default tenant for development
      }
      
      return { id: subdomain };
    } catch (error) {
      console.error('Error getting current tenant:', error);
      return { id: 'demo' };
    }
  }

  // Generic API method
  private async request<T>(
    method: 'GET' | 'POST' | 'PUT' | 'DELETE' | 'PATCH',
    url: string,
    data?: any,
    config?: AxiosRequestConfig
  ): Promise<T> {
    try {
      const response: AxiosResponse<T> = await this.client.request({
        method,
        url,
        data,
        ...config,
      });
      return response.data;
    } catch (error) {
      console.error(`API ${method} ${url} failed:`, error);
      throw error;
    }
  }

  // Etsy-specific API methods
  async getShopAnalytics(params: ShopAnalyticsParams = {}): Promise<AnalyticsData> {
    return this.request<AnalyticsData>('GET', '/api/shop-analytics', undefined, { params });
  }

  async getTopSellers(year: number): Promise<TopSellersResponse> {
    return this.request<TopSellersResponse>('GET', `/api/top-sellers?year=${year}`);
  }

  async getLocalImages(): Promise<LocalImagesResponse> {
    return this.request<LocalImagesResponse>('GET', '/api/local-images');
  }

  async saveMaskData(maskData: MaskData): Promise<ApiResponse<{ id: string; name: string }>> {
    return this.request<ApiResponse<{ id: string; name: string }>>(
      'POST', 
      '/api/masks', 
      maskData
    );
  }

  // Additional utility methods
  async uploadFile(file: File, path: string = '/api/upload'): Promise<ApiResponse<{ url: string }>> {
    const formData = new FormData();
    formData.append('file', file);

    return this.request<ApiResponse<{ url: string }>>(
      'POST',
      path,
      formData,
      {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      }
    );
  }

  async downloadFile(url: string): Promise<Blob> {
    const response = await this.client.get(url, {
      responseType: 'blob',
    });
    return response.data;
  }

  // Health check
  async healthCheck(): Promise<{ status: string; timestamp: number }> {
    return this.request<{ status: string; timestamp: number }>('GET', '/health');
  }

  // Multi-step tenant registration methods
  async startTenantRegistration(data: TenantRegistrationStep1Request): Promise<TenantRegistrationStep1Response> {
    return this.request<TenantRegistrationStep1Response>('POST', '/api/v1/tenants/register/start', data);
  }

  async connectIntegration(data: IntegrationConnectRequest): Promise<IntegrationConnectResponse> {
    return this.request<IntegrationConnectResponse>('POST', '/api/v1/tenants/register/connect', data);
  }

  async completeRegistration(data: CompleteRegistrationRequest): Promise<CompleteRegistrationResponse> {
    return this.request<CompleteRegistrationResponse>('POST', '/api/v1/tenants/register/complete', data);
  }

  async checkSubdomainAvailability(subdomain: string): Promise<{ subdomain: string; available: boolean; message: string }> {
    return this.request<{ subdomain: string; available: boolean; message: string }>('GET', `/api/v1/tenants/check-subdomain/${subdomain}`);
  }
}

export const apiService = new ApiService();
export default apiService;