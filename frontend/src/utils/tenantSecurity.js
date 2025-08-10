// utils/tenantSecurity.js
export const validateTenantAccess = (requestedTenant, userTenant) => {
  if (!userTenant || !requestedTenant) {
    throw new Error('Tenant information missing');
  }
  
  if (userTenant !== requestedTenant) {
    throw new Error('Access denied: Tenant mismatch');
  }
  
  return true;
};

// Enhanced API service with security
export class SecureApiService extends ApiService {
  async makeRequest(endpoint, options = {}) {
    const tenant = this.getCurrentTenant();
    
    // Validate tenant access before making request
    if (!tenant?.id) {
      throw new Error('No tenant context available');
    }
    
    return super.makeRequest(endpoint, {
      ...options,
      headers: {
        ...options.headers,
        'X-Tenant-ID': tenant.id,
        'X-Tenant-Signature': this.generateTenantSignature(tenant.id),
      }
    });
  }
  
  generateTenantSignature(tenantId) {
    // Generate HMAC signature for tenant validation
    const timestamp = Date.now();
    const payload = `${tenantId}:${timestamp}`;
    // In production, use proper HMAC with secret key
    return btoa(payload);
  }
}