import React from 'react';
import { render, screen } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { MemoryRouter } from 'react-router-dom';
import App from './App';
import { createTestQueryClient } from './setupTests';

// Mock the auth store
jest.mock('@/store/useStore', () => ({
  useAuthStore: () => ({
    isAuthenticated: false,
    user: null,
    login: jest.fn(),
    logout: jest.fn(),
  }),
}));

// Mock the health monitor
jest.mock('@/utils/healthMonitor', () => ({
  HealthStatus: () => <div data-testid="health-status">Health Status</div>,
  healthMonitor: {
    startMonitoring: jest.fn(),
    getHealthStatus: jest.fn(() => ({
      api: true,
      tenant: true,
      storage: true,
      timestamp: new Date().toISOString(),
    })),
  },
}));

// Mock pages
jest.mock('@/pages/login', () => {
  return function MockLoginPage() {
    return <div data-testid="login-page">Login Page</div>;
  };
});

jest.mock('@/pages/dashboard', () => {
  return function MockDashboardPage() {
    return <div data-testid="dashboard-page">Dashboard Page</div>;
  };
});

jest.mock('@/pages/templates', () => {
  return function MockTemplatesPage() {
    return <div data-testid="templates-page">Templates Page</div>;
  };
});

jest.mock('@/pages/orders', () => {
  return function MockOrdersPage() {
    return <div data-testid="orders-page">Orders Page</div>;
  };
});

jest.mock('@/pages/integrations', () => {
  return function MockIntegrationsPage() {
    return <div data-testid="integrations-page">Integrations Page</div>;
  };
});

jest.mock('@/pages/tenants', () => {
  return function MockTenantsPage() {
    return <div data-testid="tenants-page">Tenants Page</div>;
  };
});

// Test wrapper component
const TestWrapper: React.FC<{ children: React.ReactNode; initialEntries?: string[] }> = ({ 
  children, 
  initialEntries = ['/'] 
}) => {
  const queryClient = createTestQueryClient();
  
  return (
    <QueryClientProvider client={queryClient}>
      <MemoryRouter initialEntries={initialEntries}>
        {children}
      </MemoryRouter>
    </QueryClientProvider>
  );
};

describe('App Component', () => {
  beforeEach(() => {
    // Clear all mocks before each test
    jest.clearAllMocks();
  });

  test('renders login page when not authenticated', () => {
    render(
      <TestWrapper initialEntries={['/login']}>
        <App />
      </TestWrapper>
    );

    expect(screen.getByTestId('login-page')).toBeInTheDocument();
  });

  test('redirects to login when accessing protected route while not authenticated', () => {
    render(
      <TestWrapper initialEntries={['/dashboard']}>
        <App />
      </TestWrapper>
    );

    // Should redirect to login page
    expect(screen.getByTestId('login-page')).toBeInTheDocument();
  });

  test('renders 404 page for unknown routes', () => {
    render(
      <TestWrapper initialEntries={['/unknown-route']}>
        <App />
      </TestWrapper>
    );

    expect(screen.getByText('404')).toBeInTheDocument();
    expect(screen.getByText('Page not found')).toBeInTheDocument();
  });

  test('renders health status component', () => {
    render(
      <TestWrapper>
        <App />
      </TestWrapper>
    );

    expect(screen.getByTestId('health-status')).toBeInTheDocument();
  });
});

describe('App Component - Authenticated', () => {
  beforeEach(() => {
    // Mock authenticated state
    jest.resetModules();
    jest.doMock('@/store/useStore', () => ({
      useAuthStore: () => ({
        isAuthenticated: true,
        user: { id: '1', email: 'test@example.com', full_name: 'Test User' },
        login: jest.fn(),
        logout: jest.fn(),
      }),
    }));
  });

  afterEach(() => {
    jest.resetModules();
  });

  test('renders dashboard when authenticated and accessing root', async () => {
    // Re-import App with mocked authenticated state
    const { default: AuthenticatedApp } = await import('./App');
    
    render(
      <TestWrapper initialEntries={['/']}>
        <AuthenticatedApp />
      </TestWrapper>
    );

    expect(screen.getByTestId('dashboard-page')).toBeInTheDocument();
  });

  test('redirects to dashboard when authenticated and accessing login', async () => {
    // Re-import App with mocked authenticated state
    const { default: AuthenticatedApp } = await import('./App');
    
    render(
      <TestWrapper initialEntries={['/login']}>
        <AuthenticatedApp />
      </TestWrapper>
    );

    expect(screen.getByTestId('dashboard-page')).toBeInTheDocument();
  });

  test('renders protected routes when authenticated', async () => {
    // Re-import App with mocked authenticated state
    const { default: AuthenticatedApp } = await import('./App');
    
    const routes = [
      { path: '/dashboard', testId: 'dashboard-page' },
      { path: '/templates', testId: 'templates-page' },
      { path: '/orders', testId: 'orders-page' },
      { path: '/integrations', testId: 'integrations-page' },
      { path: '/tenants', testId: 'tenants-page' },
    ];

    for (const route of routes) {
      const { container } = render(
        <TestWrapper initialEntries={[route.path]}>
          <AuthenticatedApp />
        </TestWrapper>
      );

      expect(screen.getByTestId(route.testId)).toBeInTheDocument();
      
      // Clean up for next iteration
      container.remove();
    }
  });
});