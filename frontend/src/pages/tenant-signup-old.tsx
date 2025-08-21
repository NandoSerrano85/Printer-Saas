import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/router';
import Link from 'next/link';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { useAuthStore } from '@/store/useStore';
import apiService from '@/services/api';
import toast from 'react-hot-toast';
import { EyeIcon, EyeSlashIcon, CheckCircleIcon } from '@heroicons/react/24/outline';

const tenantSignupSchema = z.object({
  // Company Information
  company_name: z.string().min(2, 'Company name must be at least 2 characters'),
  subdomain: z.string()
    .min(3, 'Subdomain must be at least 3 characters')
    .max(20, 'Subdomain must be less than 20 characters')
    .regex(/^[a-z0-9-]+$/, 'Subdomain can only contain lowercase letters, numbers, and hyphens')
    .refine(val => !val.startsWith('-') && !val.endsWith('-'), 'Subdomain cannot start or end with hyphens'),
  
  // Admin User Information
  admin_first_name: z.string().min(1, 'First name is required'),
  admin_last_name: z.string().min(1, 'Last name is required'),
  admin_email: z.string().email('Invalid email address'),
  admin_password: z.string()
    .min(8, 'Password must be at least 8 characters')
    .regex(/^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)/, 'Password must contain at least one uppercase letter, one lowercase letter, and one number'),
  confirm_password: z.string(),
  
  // Subscription
  subscription_plan: z.string().default('basic'),
  
  // Legal
  terms_accepted: z.boolean().refine(val => val === true, 'You must accept the terms and conditions'),
}).refine(data => data.admin_password === data.confirm_password, {
  message: "Passwords don't match",
  path: ['confirm_password'],
});

type TenantSignupFormData = z.infer<typeof tenantSignupSchema>;

export default function TenantSignupOld() {
  const router = useRouter();
  const { login, isAuthenticated, isLoading } = useAuthStore();
  const [loading, setLoading] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [subdomainAvailable, setSubdomainAvailable] = useState<boolean | null>(null);
  const [checkingSubdomain, setCheckingSubdomain] = useState(false);

  const {
    register,
    handleSubmit,
    formState: { errors },
    watch,
    setValue,
  } = useForm<TenantSignupFormData>({
    resolver: zodResolver(tenantSignupSchema),
    defaultValues: {
      subscription_plan: 'basic',
    },
  });

  const watchedSubdomain = watch('subdomain');

  useEffect(() => {
    // Only redirect if not loading and authenticated
    if (!isLoading && isAuthenticated) {
      router.push('/dashboard');
    }
  }, [isAuthenticated, isLoading, router]);

  // Check subdomain availability
  useEffect(() => {
    const checkSubdomain = async () => {
      if (watchedSubdomain && watchedSubdomain.length >= 3) {
        setCheckingSubdomain(true);
        try {
          const response = await apiService.checkSubdomainAvailability(watchedSubdomain);
          setSubdomainAvailable(response.available);
        } catch (error) {
          console.error('Error checking subdomain:', error);
          setSubdomainAvailable(false);
        } finally {
          setCheckingSubdomain(false);
        }
      } else {
        setSubdomainAvailable(null);
      }
    };

    const timeoutId = setTimeout(checkSubdomain, 500);
    return () => clearTimeout(timeoutId);
  }, [watchedSubdomain]);

  const onSubmit = async (data: TenantSignupFormData) => {
    if (subdomainAvailable === false) {
      toast.error('Please choose an available subdomain');
      return;
    }

    setLoading(true);
    
    try {
      const response = await apiService.tenantRegister({
        company_name: data.company_name,
        subdomain: data.subdomain,
        admin_email: data.admin_email,
        admin_password: data.admin_password,
        admin_first_name: data.admin_first_name,
        admin_last_name: data.admin_last_name,
        subscription_plan: data.subscription_plan,
      });

      if (response.success && response.tokens) {
        // Store the admin user and token
        const adminUser = {
          id: response.admin_user.id,
          email: response.admin_user.email,
          full_name: `${response.admin_user.first_name} ${response.admin_user.last_name}`,
          first_name: response.admin_user.first_name,
          last_name: response.admin_user.last_name,
          is_active: response.admin_user.is_active,
          role: response.admin_user.role,
          tenant_id: response.tenant.id,
          created_at: response.admin_user.created_at,
          updated_at: response.admin_user.created_at,
        };

        login(adminUser, response.tokens.access_token);
        toast.success(`Welcome to Printer SaaS! Your tenant "${data.company_name}" has been created.`);
        router.push('/dashboard');
      } else {
        toast.error('Registration failed: Invalid response from server');
      }
    } catch (error: any) {
      console.error('Tenant registration error:', error);
      if (error.response?.status === 409) {
        toast.error('Subdomain or email is already taken');
      } else if (error.response?.status === 400) {
        toast.error(error.response?.data?.detail || 'Invalid registration data');
      } else {
        toast.error('Registration failed. Please try again.');
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
            Create your company account
          </h2>
          <p className="mt-2 text-center text-sm text-gray-600">
            Simple registration - set up integrations later
          </p>
        </div>
        
        <form className="mt-8 space-y-6" onSubmit={handleSubmit(onSubmit)}>
          <div className="space-y-4">
            {/* Company Information */}
            <div className="border-b border-gray-200 pb-4">
              <h3 className="text-lg font-medium text-gray-900 mb-3">Company Information</h3>
              
              <div>
                <label htmlFor="company_name" className="block text-sm font-medium text-gray-700">
                  Company Name *
                </label>
                <input
                  {...register('company_name')}
                  type="text"
                  className="mt-1 appearance-none relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 rounded-md focus:outline-none focus:ring-primary-500 focus:border-primary-500 focus:z-10 sm:text-sm"
                  placeholder="Your Company Name"
                />
                {errors.company_name && (
                  <p className="mt-1 text-sm text-red-600">{errors.company_name.message}</p>
                )}
              </div>

              <div className="mt-3">
                <label htmlFor="subdomain" className="block text-sm font-medium text-gray-700">
                  Subdomain *
                </label>
                <div className="mt-1 flex rounded-md shadow-sm">
                  <input
                    {...register('subdomain')}
                    type="text"
                    className="flex-1 block w-full border-gray-300 rounded-l-md focus:ring-primary-500 focus:border-primary-500 sm:text-sm"
                    placeholder="yourcompany"
                    onChange={(e) => {
                      const value = e.target.value.toLowerCase().replace(/[^a-z0-9-]/g, '');
                      setValue('subdomain', value);
                    }}
                  />
                  <span className="inline-flex items-center px-3 rounded-r-md border border-l-0 border-gray-300 bg-gray-50 text-gray-500 sm:text-sm">
                    .printersaas.com
                  </span>
                </div>
                {checkingSubdomain && (
                  <p className="mt-1 text-sm text-gray-500">Checking availability...</p>
                )}
                {subdomainAvailable === true && (
                  <p className="mt-1 text-sm text-green-600 flex items-center">
                    <CheckCircleIcon className="h-4 w-4 mr-1" />
                    Subdomain is available
                  </p>
                )}
                {subdomainAvailable === false && (
                  <p className="mt-1 text-sm text-red-600">Subdomain is not available</p>
                )}
                {errors.subdomain && (
                  <p className="mt-1 text-sm text-red-600">{errors.subdomain.message}</p>
                )}
              </div>
            </div>

            {/* Admin User Information */}
            <div className="pb-4">
              <h3 className="text-lg font-medium text-gray-900 mb-3">Admin Account</h3>
              
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label htmlFor="admin_first_name" className="block text-sm font-medium text-gray-700">
                    First Name *
                  </label>
                  <input
                    {...register('admin_first_name')}
                    type="text"
                    className="mt-1 appearance-none relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 rounded-md focus:outline-none focus:ring-primary-500 focus:border-primary-500 focus:z-10 sm:text-sm"
                    placeholder="John"
                  />
                  {errors.admin_first_name && (
                    <p className="mt-1 text-sm text-red-600">{errors.admin_first_name.message}</p>
                  )}
                </div>

                <div>
                  <label htmlFor="admin_last_name" className="block text-sm font-medium text-gray-700">
                    Last Name *
                  </label>
                  <input
                    {...register('admin_last_name')}
                    type="text"
                    className="mt-1 appearance-none relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 rounded-md focus:outline-none focus:ring-primary-500 focus:border-primary-500 focus:z-10 sm:text-sm"
                    placeholder="Doe"
                  />
                  {errors.admin_last_name && (
                    <p className="mt-1 text-sm text-red-600">{errors.admin_last_name.message}</p>
                  )}
                </div>
              </div>

              <div className="mt-3">
                <label htmlFor="admin_email" className="block text-sm font-medium text-gray-700">
                  Admin Email *
                </label>
                <input
                  {...register('admin_email')}
                  type="email"
                  autoComplete="email"
                  className="mt-1 appearance-none relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 rounded-md focus:outline-none focus:ring-primary-500 focus:border-primary-500 focus:z-10 sm:text-sm"
                  placeholder="admin@yourcompany.com"
                />
                {errors.admin_email && (
                  <p className="mt-1 text-sm text-red-600">{errors.admin_email.message}</p>
                )}
              </div>

              <div className="mt-3">
                <label htmlFor="admin_password" className="block text-sm font-medium text-gray-700">
                  Password *
                </label>
                <div className="mt-1 relative">
                  <input
                    {...register('admin_password')}
                    type={showPassword ? 'text' : 'password'}
                    autoComplete="new-password"
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
                <p className="mt-1 text-xs text-gray-500">
                  Must contain at least 8 characters with uppercase, lowercase, and number
                </p>
                {errors.admin_password && (
                  <p className="mt-1 text-sm text-red-600">{errors.admin_password.message}</p>
                )}
              </div>

              <div className="mt-3">
                <label htmlFor="confirm_password" className="block text-sm font-medium text-gray-700">
                  Confirm Password *
                </label>
                <div className="mt-1 relative">
                  <input
                    {...register('confirm_password')}
                    type={showConfirmPassword ? 'text' : 'password'}
                    autoComplete="new-password"
                    className="appearance-none relative block w-full px-3 py-2 pr-10 border border-gray-300 placeholder-gray-500 text-gray-900 rounded-md focus:outline-none focus:ring-primary-500 focus:border-primary-500 focus:z-10 sm:text-sm"
                    placeholder="Confirm your password"
                  />
                  <button
                    type="button"
                    className="absolute inset-y-0 right-0 pr-3 flex items-center"
                    onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                  >
                    {showConfirmPassword ? (
                      <EyeSlashIcon className="h-5 w-5 text-gray-400" />
                    ) : (
                      <EyeIcon className="h-5 w-5 text-gray-400" />
                    )}
                  </button>
                </div>
                {errors.confirm_password && (
                  <p className="mt-1 text-sm text-red-600">{errors.confirm_password.message}</p>
                )}
              </div>
            </div>

            {/* Terms and Conditions */}
            <div>
              <div className="flex items-start">
                <div className="flex items-center h-5">
                  <input
                    {...register('terms_accepted')}
                    type="checkbox"
                    className="h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300 rounded"
                  />
                </div>
                <div className="ml-3 text-sm">
                  <label className="text-gray-700">
                    I accept the{' '}
                    <a href="/terms" target="_blank" className="text-primary-600 hover:text-primary-500">
                      Terms and Conditions
                    </a>{' '}
                    and{' '}
                    <a href="/privacy" target="_blank" className="text-primary-600 hover:text-primary-500">
                      Privacy Policy
                    </a>{' '}
                    *
                  </label>
                </div>
              </div>
              {errors.terms_accepted && (
                <p className="mt-1 text-sm text-red-600">{errors.terms_accepted.message}</p>
              )}
            </div>
          </div>

          <div>
            <button
              type="submit"
              disabled={loading || subdomainAvailable === false}
              className="group relative w-full flex justify-center py-2 px-4 border border-transparent text-sm font-medium rounded-md text-white bg-primary-600 hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading ? (
                <div className="flex items-center">
                  <div className="animate-spin -ml-1 mr-3 h-5 w-5 border-2 border-white border-t-transparent rounded-full"></div>
                  Creating Account...
                </div>
              ) : (
                'Create Company Account'
              )}
            </button>
          </div>
        </form>

        <div className="text-center">
          <p className="text-sm text-gray-600">
            Want to connect integrations during setup?{' '}
            <Link href="/tenant-signup" className="font-medium text-primary-600 hover:text-primary-500">
              Use guided registration
            </Link>
          </p>
          <p className="mt-2 text-sm text-gray-600">
            Already have a company account?{' '}
            <Link href="/tenant-login" className="font-medium text-primary-600 hover:text-primary-500">
              Sign in as admin
            </Link>
          </p>
          <p className="mt-2 text-sm text-gray-600">
            Need to join an existing company?{' '}
            <Link href="/signup" className="font-medium text-primary-600 hover:text-primary-500">
              Join a team
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
}