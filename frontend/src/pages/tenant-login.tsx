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

const tenantLoginSchema = z.object({
  email: z.string().email('Invalid email address'),
  password: z.string().min(1, 'Password is required'),
  subdomain: z.string().optional(),
});

type TenantLoginFormData = z.infer<typeof tenantLoginSchema>;

export default function TenantLogin() {
  const router = useRouter();
  const { login, isAuthenticated, isLoading } = useAuthStore();
  const [loading, setLoading] = useState(false);
  const [showPassword, setShowPassword] = useState(false);

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<TenantLoginFormData>({
    resolver: zodResolver(tenantLoginSchema),
  });

  useEffect(() => {
    // Only redirect if not loading and authenticated
    if (!isLoading && isAuthenticated) {
      router.push('/dashboard');
    }
  }, [isAuthenticated, isLoading, router]);

  const onSubmit = async (data: TenantLoginFormData) => {
    setLoading(true);
    
    try {
      const response = await apiService.tenantLogin(
        data.email, 
        data.password, 
        data.subdomain || undefined
      );

      if (response.success && response.tokens) {
        // Store the admin user and token
        const adminUser = {
          id: response.user.id,
          email: response.user.email,
          full_name: `${response.user.first_name} ${response.user.last_name}`,
          first_name: response.user.first_name,
          last_name: response.user.last_name,
          is_active: response.user.is_active,
          role: response.user.role,
          tenant_id: response.tenant.id,
          created_at: response.user.created_at,
          updated_at: response.user.created_at,
        };

        login(adminUser, response.tokens.access_token);
        toast.success(`Welcome back to ${response.tenant.company_name}!`);
        router.push('/dashboard');
      } else {
        toast.error('Login failed: Invalid response from server');
      }
    } catch (error: any) {
      console.error('Tenant login error:', error);
      if (error.response?.status === 401) {
        toast.error('Invalid email or password');
      } else {
        toast.error(error.response?.data?.detail || 'Login failed');
      }
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
                d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4"
              />
            </svg>
          </div>
          <h2 className="mt-6 text-center text-3xl font-extrabold text-gray-900">
            Company Admin Sign In
          </h2>
          <p className="mt-2 text-center text-sm text-gray-600">
            Access your company's Printer SaaS dashboard
          </p>
        </div>
        
        <form className="mt-8 space-y-6" onSubmit={handleSubmit(onSubmit)}>
          <div className="space-y-4">
            <div>
              <label htmlFor="email" className="block text-sm font-medium text-gray-700">
                Admin Email Address
              </label>
              <input
                {...register('email')}
                type="email"
                autoComplete="email"
                className="mt-1 appearance-none relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 rounded-md focus:outline-none focus:ring-primary-500 focus:border-primary-500 focus:z-10 sm:text-sm"
                placeholder="admin@yourcompany.com"
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

            <div>
              <label htmlFor="subdomain" className="block text-sm font-medium text-gray-700">
                Company Subdomain (Optional)
              </label>
              <div className="mt-1 flex rounded-md shadow-sm">
                <input
                  {...register('subdomain')}
                  type="text"
                  className="flex-1 block w-full border-gray-300 rounded-l-md focus:ring-primary-500 focus:border-primary-500 sm:text-sm"
                  placeholder="yourcompany"
                />
                <span className="inline-flex items-center px-3 rounded-r-md border border-l-0 border-gray-300 bg-gray-50 text-gray-500 sm:text-sm">
                  .printersaas.com
                </span>
              </div>
              <p className="mt-1 text-xs text-gray-500">
                Leave blank if you're unsure - we'll find your account by email
              </p>
              {errors.subdomain && (
                <p className="mt-1 text-sm text-red-600">{errors.subdomain.message}</p>
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
                'Sign In as Admin'
              )}
            </button>
          </div>

          <div className="flex items-center justify-between">
            <div className="text-sm">
              <a href="#" className="font-medium text-primary-600 hover:text-primary-500">
                Forgot your password?
              </a>
            </div>
          </div>
        </form>

        <div className="text-center">
          <p className="text-sm text-gray-600">
            Don't have a company account?{' '}
            <Link href="/tenant-signup" className="font-medium text-primary-600 hover:text-primary-500">
              Create company account
            </Link>
          </p>
          <p className="mt-2 text-sm text-gray-600">
            Are you a team member?{' '}
            <Link href="/login" className="font-medium text-primary-600 hover:text-primary-500">
              Sign in to your workspace
            </Link>
          </p>
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
              <h3 className="text-sm font-medium text-blue-800">Company Admin Access</h3>
              <div className="mt-2 text-sm text-blue-700">
                <p>This login is for company administrators who manage tenant settings, billing, and user accounts.</p>
                <p className="mt-1">Team members should use the regular workspace login instead.</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}