import React, { 
  createContext,
  useContext,
  useState,
  useEffect,
  ReactNode
} from 'react';
import { TenantContextValue, Tenant, ThemeConfig } from '@/types';

interface TenantProviderProps {
  children: ReactNode;
}

interface TenantConfig {
  features: {
    analytics: boolean;
    automation: boolean;
    whiteLabel?: boolean;
  };
  limits: {
    users: number;
    storage: number;
    apiCalls: number;
  };
  customDomain?: string;
  branding?: {
    logo?: string;
    colors?: Record<string, string>;
  };
}

const TenantContext = createContext<TenantContextValue | undefined>(undefined);

// Helper function to get tenant theme
const getTenantTheme = (tenantId: string): ThemeConfig => {
  // Default theme configuration
  const defaultTheme: ThemeConfig = {
    name: 'Default',
    colors: {
      primary: '#3b82f6',
      secondary: '#64748b', 
      background: '#ffffff',
      text: '#1f2937',
    },
    fonts: {
      primary: 'Inter, system-ui, sans-serif',
      secondary: 'ui-monospace, monospace',
    },
  };

  // Tenant-specific themes could be loaded from API or configuration
  const tenantThemes: Record<string, ThemeConfig> = {
    demo: defaultTheme,
    'acme-crafts': {
      name: 'Acme Crafts',
      colors: {
        primary: '#059669',
        secondary: '#6b7280',
        background: '#f9fafb',
        text: '#111827',
      },
      fonts: {
        primary: 'Inter, system-ui, sans-serif',
        secondary: 'ui-monospace, monospace',
      },
    },
    'creative-designs': {
      name: 'Creative Designs',
      colors: {
        primary: '#7c3aed',
        secondary: '#6b7280',
        background: '#faf5ff',
        text: '#581c87',
      },
      fonts: {
        primary: 'Poppins, system-ui, sans-serif',
        secondary: 'ui-monospace, monospace',
      },
    },
  };

  return tenantThemes[tenantId] || defaultTheme;
};

// Helper function to get tenant configuration
const getTenantConfig = (tenantId: string): TenantConfig => {
  // Default configuration
  const defaultConfig: TenantConfig = {
    features: {
      analytics: true,
      automation: true,
    },
    limits: {
      users: 5,
      storage: 10000, // 10GB in MB
      apiCalls: 10000,
    },
  };

  // Tenant-specific configurations
  const tenantConfigs: Record<string, TenantConfig> = {
    demo: {
      ...defaultConfig,
      features: {
        analytics: true,
        automation: true,
      },
      limits: {
        users: 1,
        storage: 1000, // 1GB
        apiCalls: 1000,
      },
    },
    'acme-crafts': {
      ...defaultConfig,
      features: {
        analytics: true,
        automation: true,
      },
      limits: {
        users: 10,
        storage: 50000, // 50GB
        apiCalls: 50000,
      },
    },
    'creative-designs': {
      ...defaultConfig,
      features: {
        analytics: false,
        automation: true,
      },
      limits: {
        users: 3,
        storage: 5000, // 5GB
        apiCalls: 5000,
      },
    },
  };

  return tenantConfigs[tenantId] || defaultConfig;
};

export const TenantProvider: React.FC<TenantProviderProps> = ({ children }) => {
  const [tenantData, setTenantData] = useState<Tenant | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const detectTenant = (): string => {
    try {
      const hostname = window.location.hostname;
      const subdomain = hostname.split('.')[0];
      
      // For development: tenant1.localhost, tenant2.localhost
      // For production: tenant1.yourdomain.com
      if (subdomain && subdomain !== 'localhost' && subdomain !== 'www' && subdomain !== '127' && !subdomain.match(/^\d+$/)) {
        return subdomain;
      }
      
      // Fallback to path-based routing: /tenant1/dashboard
      const pathSegments = window.location.pathname.split('/').filter(Boolean);
      if (pathSegments.length > 0 && pathSegments[0] !== 'login') {
        return pathSegments[0];
      }
      
      return 'demo'; // Default tenant
    } catch (error) {
      console.error('Error detecting tenant:', error);
      return 'demo';
    }
  };

  const refreshTenant = async (): Promise<void> => {
    setIsLoading(true);
    setError(null);

    try {
      const tenantId = detectTenant();
      
      // In a real app, you'd fetch tenant data from API
      const tenant: Tenant = {
        id: crypto.randomUUID(),
        subdomain: tenantId,
        company_name: tenantId.replace(/-/g, ' ').replace(/\b\w/g, l => l.toUpperCase()),
        subscription_tier: tenantId === 'demo' ? 'free' : 'professional',
        database_schema: `tenant_${tenantId}`,
        settings: {
          theme: getTenantTheme(tenantId),
          config: getTenantConfig(tenantId),
        },
        is_active: true,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      };

      setTenantData(tenant);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to load tenant data';
      setError(errorMessage);
      console.error('Error loading tenant:', err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    refreshTenant();
  }, []);

  const contextValue: TenantContextValue = {
    tenantId: tenantData?.subdomain || null,
    tenantData,
    isLoading,
    error,
    refreshTenant,
  };

  return (
    <TenantContext.Provider value={contextValue}>
      {children}
    </TenantContext.Provider>
  );
};

export const useTenant = (): TenantContextValue => {
  const context = useContext(TenantContext);
  if (context === undefined) {
    throw new Error('useTenant must be used within TenantProvider');
  }
  return context;
};

export default TenantContext;