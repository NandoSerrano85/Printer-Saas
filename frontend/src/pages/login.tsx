import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/router';
import Link from 'next/link';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { useAuthStore } from '@/store/useStore';
import apiService from '@/services/api';
import toast from 'react-hot-toast';
import { EyeIcon, EyeSlashIcon } from '@heroicons/react/24/outline';

const loginSchema = z.object({
  email: z.string().email('Invalid email address'),
  password: z.string().min(6, 'Password must be at least 6 characters'),
});

type LoginFormData = z.infer<typeof loginSchema>;

export default function Login() {
  const router = useRouter();
  const { login, isAuthenticated, isLoading } = useAuthStore();
  const [loading, setLoading] = useState(false);
  const [showPassword, setShowPassword] = useState(false);

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<LoginFormData>({
    resolver: zodResolver(loginSchema),
  });

  useEffect(() => {
    // Only redirect if not loading and authenticated
    if (!isLoading && isAuthenticated) {
      router.push('/dashboard');
    }
  }, [isAuthenticated, isLoading, router]);

  const onSubmit = async (data: LoginFormData) => {
    setLoading(true);
    
    try {
      // Extract tenant info from URL or query params for user login
      const { tenant_id } = router.query;
      const tenantId = typeof tenant_id === 'string' ? tenant_id : undefined;
      
      const response = await apiService.login(data.email, data.password, tenantId);
      
      if (response.success && response.tokens && response.user) {
        const user = {
          id: response.user.id,
          email: response.user.email,
          full_name: response.user.full_name || response.user.display_name,
          first_name: response.user.first_name,
          last_name: response.user.last_name,
          is_active: response.user.is_active,
          created_at: response.user.created_at,
          updated_at: response.user.created_at,
        };

        login(user, response.tokens.access_token);
        toast.success('Login successful!');
        router.push('/dashboard');
      } else if (response.requires_email_verification) {
        toast.error('Please verify your email address before logging in.');
        router.push(`/verify-email?email=${encodeURIComponent(data.email)}`);
      } else {
        toast.error('Invalid response from server');
      }
    } catch (error: any) {
      console.error('Login error:', error);
      if (error.response?.status === 401) {
        toast.error('Invalid email or password');
      } else {
        toast.error(error.response?.data?.detail || 'Login failed');
      }
    } finally {
      setLoading(false);
    }
  };

  // Demo login for development
  const handleDemoLogin = async () => {
    setLoading(true);
    try {
      // Create a demo user session without actual API call for development
      const demoUser = {
        id: 'demo-user-id',
        email: 'demo@printersaas.dev',
        full_name: 'Demo User',
        is_active: true,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      };
      
      const demoToken = 'demo-jwt-token';
      login(demoUser, demoToken);
      toast.success('Demo login successful!');
      router.push('/dashboard');
    } catch (error) {
      toast.error('Demo login failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full space-y-8">
        <div>
          <div className="mx-auto h-12 w-12 flex items-center justify-center rounded-full bg-primary-100">
            <svg
              className="h-8 w-8 text-primary-600"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
              xmlns="http://www.w3.org/2000/svg"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M17 17h2a2 2 0 002-2v-4a2 2 0 00-2-2H5a2 2 0 00-2 2v4a2 2 0 002 2h2m2 4h6a2 2 0 002-2v-4a2 2 0 00-2-2H9a2 2 0 00-2 2v4a2 2 0 002 2z"
              />
            </svg>
          </div>
          <h2 className="mt-6 text-center text-3xl font-extrabold text-gray-900">
            Sign in to your workspace
          </h2>
          <p className="mt-2 text-center text-sm text-gray-600">
            Access your print-on-demand tools and templates
          </p>
        </div>
        
        <form className="mt-8 space-y-6" onSubmit={handleSubmit(onSubmit)}>
          <div className="space-y-4">
            <div>
              <label htmlFor="email" className="block text-sm font-medium text-gray-700">
                Email address
              </label>
              <input
                {...register('email')}
                type="email"
                autoComplete="email"
                className="mt-1 appearance-none relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 rounded-md focus:outline-none focus:ring-primary-500 focus:border-primary-500 focus:z-10 sm:text-sm"
                placeholder="Enter your email"
              />
              {errors.email && (
                <p className="mt-1 text-sm text-red-600">{errors.email.message}</p>
              )}
            </div>
            
            <div>
              <label htmlFor="password" className="block text-sm font-medium text-gray-700">
                Password
              </label>
              <div className="mt-1 relative">
                <input
                  {...register('password')}
                  type={showPassword ? 'text' : 'password'}
                  autoComplete="current-password"
                  className="appearance-none relative block w-full px-3 py-2 pr-10 border border-gray-300 placeholder-gray-500 text-gray-900 rounded-md focus:outline-none focus:ring-primary-500 focus:border-primary-500 focus:z-10 sm:text-sm"
                  placeholder="Enter your password"
                />
                <button
                  type="button"
                  className="absolute inset-y-0 right-0 pr-3 flex items-center"
                  onClick={() => setShowPassword(!showPassword)}
                >
                  {showPassword ? (
                    <EyeSlashIcon className="h-5 w-5 text-gray-400" />
                  ) : (
                    <EyeIcon className="h-5 w-5 text-gray-400" />
                  )}
                </button>
              </div>
              {errors.password && (
                <p className="mt-1 text-sm text-red-600">{errors.password.message}</p>
              )}
            </div>
          </div>

          <div>
            <button
              type="submit"
              disabled={loading}
              className="group relative w-full flex justify-center py-2 px-4 border border-transparent text-sm font-medium rounded-md text-white bg-primary-600 hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading ? (
                <div className="flex items-center">
                  <div className="animate-spin -ml-1 mr-3 h-5 w-5 border-2 border-white border-t-transparent rounded-full"></div>
                  Signing in...
                </div>
              ) : (
                'Sign in'
              )}
            </button>
          </div>

          {/* Demo Login Button */}
          <div className="mt-4">
            <button
              type="button"
              onClick={handleDemoLogin}
              disabled={loading}
              className="w-full flex justify-center py-2 px-4 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading ? 'Loading...' : 'Demo Login (Development)'}
            </button>
          </div>

          {/* Development Notice */}
          <div className="mt-6 p-4 bg-blue-50 border border-blue-200 rounded-md">
            <div className="flex">
              <div className="flex-shrink-0">
                <svg className="h-5 w-5 text-blue-400" viewBox="0 0 20 20" fill="currentColor">
                  <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
                </svg>
              </div>
              <div className="ml-3">
                <h3 className="text-sm font-medium text-blue-800">User Workspace Login</h3>
                <div className="mt-2 text-sm text-blue-700">
                  <p>This is for team members to access their workspace. Use the "Demo Login" for development.</p>
                  <p className="mt-1">For company admin access, use the <strong>Admin sign in</strong> link below.</p>
                  <p className="mt-1">Backend API: <code className="text-xs bg-blue-100 px-1 rounded">http://localhost:8000</code></p>
                </div>
              </div>
            </div>
          </div>
        </form>

        {/* Signup Links */}
        <div className="text-center">
          <p className="text-sm text-gray-600">
            Don't have an account?{' '}
            <Link href="/signup" className="font-medium text-primary-600 hover:text-primary-500">
              Join a team
            </Link>
          </p>
          <p className="mt-2 text-sm text-gray-600">
            Need to create a company?{' '}
            <Link href="/tenant-signup" className="font-medium text-primary-600 hover:text-primary-500">
              Create company account
            </Link>
          </p>
          <p className="mt-2 text-sm text-gray-600">
            Company admin?{' '}
            <Link href="/tenant-login" className="font-medium text-primary-600 hover:text-primary-500">
              Admin sign in
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
}