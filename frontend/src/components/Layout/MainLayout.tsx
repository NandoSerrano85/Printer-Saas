import React, { ReactNode, useEffect } from 'react';
import { useRouter } from 'next/router';
import Sidebar from './Sidebar';
import Header from './Header';
import { useAuthStore } from '@/store/useStore';
import { Toaster } from 'react-hot-toast';

interface MainLayoutProps {
  children: ReactNode;
}

export default function MainLayout({ children }: MainLayoutProps) {
  const router = useRouter();
  const { isAuthenticated, user, isLoading } = useAuthStore();

  useEffect(() => {
    // Only redirect if not loading and not authenticated
    if (!isLoading && !isAuthenticated && router.pathname !== '/login' && router.pathname !== '/tenant-login' && router.pathname !== '/signup' && router.pathname !== '/tenant-signup' && router.pathname !== '/tenant-signup-old') {
      router.push('/login');
    }
  }, [isAuthenticated, isLoading, router, router.pathname]);

  // Show loading spinner while auth state is being determined
  if (isLoading) {
    return (
      <div className="h-screen flex items-center justify-center bg-gray-100">
        <div className="flex flex-col items-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-500"></div>
          <p className="mt-4 text-gray-600">Loading...</p>
        </div>
      </div>
    );
  }

  if (!isAuthenticated) {
    return null; // will redirect to login via useEffect
  }

  return (
    <div className="h-screen flex overflow-hidden bg-gray-100">
      <Sidebar />
      
      <div className="flex flex-col w-0 flex-1 overflow-hidden">
        <Header />
        
        <main className="flex-1 relative overflow-y-auto focus:outline-none">
          <div className="py-6">
            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
              {children}
            </div>
          </div>
        </main>
      </div>
      
      <Toaster
        position="top-right"
        toastOptions={{
          duration: 4000,
          style: {
            background: '#363636',
            color: '#fff',
          },
        }}
      />
    </div>
  );
}