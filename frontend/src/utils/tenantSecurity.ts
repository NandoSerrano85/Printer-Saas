import { SecurityConfig } from '@/types';
import { apiService } from '@/services/apiService';

interface TenantValidationOptions {
  allowDemo?: boolean;
  requireSignature?: boolean;
}

interface TenantSignature {
  tenantId: string;
  timestamp: number;
  signature: string;
}

interface SecureRequestOptions extends RequestInit {
  headers?: Record<string, string>;
  validateTenant?: boolean;
}

class TenantSecurityError extends Error {
  constructor(message: string, public code: string) {
    super(message);
    this.name = 'TenantSecurityError';
  }
}

// Tenant validation functions
export const validateTenantAccess = (
  requestedTenant: string | null, 
  userTenant: string | null, 
  options: TenantValidationOptions = {}
): boolean => {
  const { allowDemo = true, requireSignature = false } = options;

  if (!userTenant || !requestedTenant) {
    throw new TenantSecurityError(
      'Tenant information missing',
      'MISSING_TENANT_INFO'
    );
  }
  
  // Allow demo tenant in development
  if (allowDemo && (requestedTenant === 'demo' || userTenant === 'demo')) {
    return true;
  }
  
  if (userTenant !== requestedTenant) {
    throw new TenantSecurityError(
      'Access denied: Tenant mismatch',
      'TENANT_MISMATCH'
    );
  }
  
  return true;
};

export const getCurrentTenantId = (): string | null => {
  if (typeof window === 'undefined') {
    return null;
  }

  try {
    // First check for tenant in localStorage (for SPA routing)
    const storedTenant = localStorage.getItem('current_tenant');
    if (storedTenant) {
      return storedTenant;
    }

    // Extract from URL subdomain
    const hostname = window.location.hostname;
    const parts = hostname.split('.');
    
    if (parts.length > 2) {
      const subdomain = parts[0];
      
      // Don't treat localhost, IPs, or common domains as subdomains
      if (['localhost', '127', '0', 'www', 'app'].includes(subdomain) || 
          /^\d+$/.test(subdomain)) {
        return 'demo'; // Default tenant for development
      }
      
      return subdomain;
    }

    return 'demo'; // Default fallback
  } catch (error) {
    console.error('Error getting current tenant ID:', error);
    return 'demo';
  }
};

export const setCurrentTenantId = (tenantId: string): void => {
  if (typeof window === 'undefined') {
    return;
  }

  try {
    localStorage.setItem('current_tenant', tenantId);
  } catch (error) {
    console.error('Error setting current tenant ID:', error);
  }
};

export const clearCurrentTenantId = (): void => {
  if (typeof window === 'undefined') {
    return;
  }

  try {
    localStorage.removeItem('current_tenant');
  } catch (error) {
    console.error('Error clearing current tenant ID:', error);
  }
};

export const generateTenantSignature = (
  tenantId: string,
  secretKey?: string
): TenantSignature => {
  const timestamp = Date.now();
  const payload = `${tenantId}:${timestamp}`;
  
  // In production, use proper HMAC with secret key
  let signature: string;
  
  if (secretKey) {
    // This is a simplified signature - in production use crypto.subtle or a proper HMAC library
    signature = btoa(payload + secretKey);
  } else {
    // Development fallback
    signature = btoa(payload);
  }
  
  return {
    tenantId,
    timestamp,
    signature,
  };
};

export const validateTenantSignature = (
  signature: TenantSignature,
  secretKey?: string,
  maxAge: number = 300000 // 5 minutes
): boolean => {
  try {
    const now = Date.now();
    
    // Check if signature is too old
    if (now - signature.timestamp > maxAge) {
      return false;
    }
    
    // Regenerate signature and compare
    const expected = generateTenantSignature(signature.tenantId, secretKey);
    
    // Simple comparison - in production use constant-time comparison
    return expected.signature === signature.signature;
  } catch (error) {
    console.error('Error validating tenant signature:', error);
    return false;
  }
};

// Enhanced API service with security
export class SecureApiService {
  private baseService: typeof apiService;
  private securityConfig: SecurityConfig;

  constructor(
    baseService: typeof apiService,
    securityConfig: Partial<SecurityConfig> = {}
  ) {
    this.baseService = baseService;
    this.securityConfig = {
      encryptionKey: securityConfig.encryptionKey || process.env.REACT_APP_ENCRYPTION_KEY || '',
      tokenExpiry: securityConfig.tokenExpiry || 3600000, // 1 hour
      maxAttempts: securityConfig.maxAttempts || 3,
    };
  }

  async makeSecureRequest<T>(
    endpoint: string, 
    options: SecureRequestOptions = {}
  ): Promise<T> {
    const { validateTenant = true, ...requestOptions } = options;
    
    // Get current tenant
    const tenantId = getCurrentTenantId();
    
    // Validate tenant access if required
    if (validateTenant) {
      if (!tenantId) {
        throw new TenantSecurityError(
          'No tenant context available',
          'NO_TENANT_CONTEXT'
        );
      }
    }
    
    // Generate tenant signature
    const signature = generateTenantSignature(
      tenantId || 'demo',
      this.securityConfig.encryptionKey
    );
    
    // Add security headers
    const secureHeaders = {
      ...requestOptions.headers,
      'X-Tenant-ID': tenantId || 'demo',
      'X-Tenant-Signature': JSON.stringify(signature),
      'X-Request-Time': Date.now().toString(),
    };
    
    // Make request with security headers
    const response = await fetch(endpoint, {
      ...requestOptions,
      headers: secureHeaders,
    });
    
    if (!response.ok) {
      if (response.status === 403) {
        throw new TenantSecurityError(
          'Access denied by server',
          'SERVER_ACCESS_DENIED'
        );
      }
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }
    
    return response.json();
  }

  // Convenience methods that mirror the base API service
  async get<T>(endpoint: string, options?: SecureRequestOptions): Promise<T> {
    return this.makeSecureRequest<T>(endpoint, {
      ...options,
      method: 'GET',
    });
  }

  async post<T>(
    endpoint: string, 
    data?: any, 
    options?: SecureRequestOptions
  ): Promise<T> {
    return this.makeSecureRequest<T>(endpoint, {
      ...options,
      method: 'POST',
      body: JSON.stringify(data),
      headers: {
        'Content-Type': 'application/json',
        ...options?.headers,
      },
    });
  }

  async put<T>(
    endpoint: string, 
    data?: any, 
    options?: SecureRequestOptions
  ): Promise<T> {
    return this.makeSecureRequest<T>(endpoint, {
      ...options,
      method: 'PUT',
      body: JSON.stringify(data),
      headers: {
        'Content-Type': 'application/json',
        ...options?.headers,
      },
    });
  }

  async delete<T>(endpoint: string, options?: SecureRequestOptions): Promise<T> {
    return this.makeSecureRequest<T>(endpoint, {
      ...options,
      method: 'DELETE',
    });
  }
}

// Create default secure API service instance
export const secureApiService = new SecureApiService(apiService);

// Utility function for tenant-safe URL generation
export const generateTenantUrl = (path: string, tenantId?: string): string => {
  const currentTenant = tenantId || getCurrentTenantId();
  
  if (!currentTenant || currentTenant === 'demo') {
    return path;
  }
  
  // In production, you might want to use subdomains
  // For now, we'll use path-based tenant routing
  return `/tenant/${currentTenant}${path}`;
};

export { TenantSecurityError };