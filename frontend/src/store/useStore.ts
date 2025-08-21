import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import { User, Tenant, IntegrationStatus, DashboardStats } from '@/types';

interface AuthState {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (user: User, token: string) => void;
  logout: () => void;
  setLoading: (loading: boolean) => void;
  initializeAuth: () => void;
}

interface AppState {
  currentTenant: Tenant | null;
  integrationStatus: {
    shopify: IntegrationStatus | null;
    etsy: IntegrationStatus | null;
  };
  dashboardStats: DashboardStats | null;
  setCurrentTenant: (tenant: Tenant | null) => void;
  setIntegrationStatus: (platform: 'shopify' | 'etsy', status: IntegrationStatus) => void;
  setDashboardStats: (stats: DashboardStats) => void;
}

interface UIState {
  sidebarOpen: boolean;
  theme: 'light' | 'dark';
  notifications: Array<{
    id: string;
    type: 'success' | 'error' | 'warning' | 'info';
    message: string;
    timestamp: number;
  }>;
  setSidebarOpen: (open: boolean) => void;
  toggleSidebar: () => void;
  setTheme: (theme: 'light' | 'dark') => void;
  addNotification: (notification: Omit<UIState['notifications'][0], 'id' | 'timestamp'>) => void;
  removeNotification: (id: string) => void;
  clearNotifications: () => void;
}

// Auth Store
export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      user: null,
      token: null,
      isAuthenticated: false,
      isLoading: true, // Start with loading true to prevent premature redirects
      login: (user: User, token: string) => {
        if (typeof window !== 'undefined') {
          localStorage.setItem('auth_token', token);
          localStorage.setItem('user_data', JSON.stringify(user));
        }
        set({ user, token, isAuthenticated: true, isLoading: false });
      },
      logout: () => {
        if (typeof window !== 'undefined') {
          localStorage.removeItem('auth_token');
          localStorage.removeItem('user_data');
        }
        set({ user: null, token: null, isAuthenticated: false, isLoading: false });
      },
      setLoading: (loading: boolean) => set({ isLoading: loading }),
      initializeAuth: () => {
        if (typeof window !== 'undefined') {
          const token = localStorage.getItem('auth_token');
          const userData = localStorage.getItem('user_data');
          
          if (token && userData) {
            try {
              const user = JSON.parse(userData);
              set({ user, token, isAuthenticated: true, isLoading: false });
            } catch (error) {
              console.error('Error parsing stored user data:', error);
              // Clear invalid data
              localStorage.removeItem('auth_token');
              localStorage.removeItem('user_data');
              set({ user: null, token: null, isAuthenticated: false, isLoading: false });
            }
          } else {
            set({ user: null, token: null, isAuthenticated: false, isLoading: false });
          }
        } else {
          // Server-side, just set loading to false
          set({ isLoading: false });
        }
      },
    }),
    {
      name: 'auth-store',
      partialize: (state) => ({ 
        user: state.user, 
        token: state.token, 
        isAuthenticated: state.isAuthenticated 
      }),
    }
  )
);

// App State Store
export const useAppStore = create<AppState>()((set) => ({
  currentTenant: null,
  integrationStatus: {
    shopify: null,
    etsy: null,
  },
  dashboardStats: null,
  setCurrentTenant: (tenant) => set({ currentTenant: tenant }),
  setIntegrationStatus: (platform, status) =>
    set((state) => ({
      integrationStatus: {
        ...state.integrationStatus,
        [platform]: status,
      },
    })),
  setDashboardStats: (stats) => set({ dashboardStats: stats }),
}));

// UI State Store
export const useUIStore = create<UIState>()(
  persist(
    (set) => ({
      sidebarOpen: true,
      theme: 'light',
      notifications: [],
      setSidebarOpen: (open) => set({ sidebarOpen: open }),
      toggleSidebar: () => set((state) => ({ sidebarOpen: !state.sidebarOpen })),
      setTheme: (theme) => set({ theme }),
      addNotification: (notification) =>
        set((state) => ({
          notifications: [
            ...state.notifications,
            {
              ...notification,
              id: Math.random().toString(36).substr(2, 9),
              timestamp: Date.now(),
            },
          ],
        })),
      removeNotification: (id) =>
        set((state) => ({
          notifications: state.notifications.filter((n) => n.id !== id),
        })),
      clearNotifications: () => set({ notifications: [] }),
    }),
    {
      name: 'ui-store',
      partialize: (state) => ({ 
        sidebarOpen: state.sidebarOpen, 
        theme: state.theme 
      }),
    }
  )
);

// Computed selectors
export const useAuth = () => {
  const { user, token, isAuthenticated, isLoading } = useAuthStore();
  return { user, token, isAuthenticated, isLoading };
};

export const useCurrentTenant = () => {
  const currentTenant = useAppStore((state) => state.currentTenant);
  return currentTenant;
};

export const useIntegrationStatus = () => {
  const integrationStatus = useAppStore((state) => state.integrationStatus);
  return integrationStatus;
};

export const useDashboardStats = () => {
  const dashboardStats = useAppStore((state) => state.dashboardStats);
  return dashboardStats;
};