import React, { useEffect } from 'react';
import type { AppProps } from 'next/app';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import ErrorBoundary from '@/components/ErrorBoundary';
import { useAuthStore } from '@/store/useStore';
import '../styles/globals.css';

// Create a query client
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: 1,
      staleTime: 5 * 60 * 1000, // 5 minutes
    },
  },
});

// Auth Initializer Component
function AuthInitializer({ children }: { children: React.ReactNode }) {
  const initializeAuth = useAuthStore(state => state.initializeAuth);
  
  useEffect(() => {
    // Initialize auth state on app load
    initializeAuth();
  }, [initializeAuth]);
  
  return <>{children}</>;
}

export default function App({ Component, pageProps }: AppProps) {
  return (
    <ErrorBoundary>
      <QueryClientProvider client={queryClient}>
        <AuthInitializer>
          <Component {...pageProps} />
        </AuthInitializer>
      </QueryClientProvider>
    </ErrorBoundary>
  );
}