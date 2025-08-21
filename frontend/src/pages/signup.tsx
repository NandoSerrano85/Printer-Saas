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

const userSignupSchema = z.object({
  // User Information
  first_name: z.string().min(1, 'First name is required'),
  last_name: z.string().min(1, 'Last name is required'),
  email: z.string().email('Invalid email address'),
  password: z.string()
    .min(8, 'Password must be at least 8 characters')
    .regex(/^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)/, 'Password must contain at least one uppercase letter, one lowercase letter, and one number'),
  confirm_password: z.string(),
  
  // Shop Information
  shop_name: z.string().min(2, 'Shop name must be at least 2 characters'),
  
  // Preferences
  timezone: z.string().default('UTC'),
  language: z.string().default('en'),
  marketing_consent: z.boolean().default(false),
  
  // Legal
  terms_accepted: z.boolean().refine(val => val === true, 'You must accept the terms and conditions'),
  
  // Tenant Information (optional - can be from URL or header)
  tenant_id: z.string().optional(),
  invitation_code: z.string().optional(),
}).refine(data => data.password === data.confirm_password, {
  message: "Passwords don't match",
  path: ['confirm_password'],
});

type UserSignupFormData = z.infer<typeof userSignupSchema>;

const timezones = [
  { value: 'UTC', label: 'UTC' },
  { value: 'America/New_York', label: 'Eastern Time (ET)' },
  { value: 'America/Chicago', label: 'Central Time (CT)' },
  { value: 'America/Denver', label: 'Mountain Time (MT)' },
  { value: 'America/Los_Angeles', label: 'Pacific Time (PT)' },
  { value: 'Europe/London', label: 'London (GMT)' },
  { value: 'Europe/Paris', label: 'Paris (CET)' },
  { value: 'Asia/Tokyo', label: 'Tokyo (JST)' },
  { value: 'Australia/Sydney', label: 'Sydney (AEST)' },
];

const languages = [
  { value: 'en', label: 'English' },
  { value: 'es', label: 'Spanish' },
  { value: 'fr', label: 'French' },
  { value: 'de', label: 'German' },
  { value: 'it', label: 'Italian' },
  { value: 'pt', label: 'Portuguese' },
];

export default function UserSignup() {
  const router = useRouter();
  const { login, isAuthenticated, isLoading } = useAuthStore();
  const [loading, setLoading] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);

  // Extract tenant info from URL or query params
  const { tenant_id, invitation_code } = router.query;

  const {
    register,
    handleSubmit,
    formState: { errors },
    setValue,
  } = useForm<UserSignupFormData>({
    resolver: zodResolver(userSignupSchema),
    defaultValues: {
      timezone: 'UTC',
      language: 'en',
      marketing_consent: false,
      tenant_id: typeof tenant_id === 'string' ? tenant_id : undefined,
      invitation_code: typeof invitation_code === 'string' ? invitation_code : undefined,
    },
  });

  useEffect(() => {
    // Only redirect if not loading and authenticated
    if (!isLoading && isAuthenticated) {
      router.push('/dashboard');
    }
  }, [isAuthenticated, isLoading, router]);

  // Set tenant_id from URL params
  useEffect(() => {
    if (tenant_id && typeof tenant_id === 'string') {
      setValue('tenant_id', tenant_id);
    }
    if (invitation_code && typeof invitation_code === 'string') {
      setValue('invitation_code', invitation_code);
    }
  }, [tenant_id, invitation_code, setValue]);

  const onSubmit = async (data: UserSignupFormData) => {
    setLoading(true);
    
    try {
      const response = await apiService.register({
        email: data.email,
        password: data.password,
        shop_name: data.shop_name,
        first_name: data.first_name,
        last_name: data.last_name,
        timezone: data.timezone,
        language: data.language,
        marketing_consent: data.marketing_consent,
        terms_accepted: data.terms_accepted,
      }, data.tenant_id);

      if (response.success && response.user) {
        // Note: User registration may not provide immediate login tokens
        // depending on email verification requirements
        toast.success('Account created successfully! Please check your email to verify your account.');
        
        // If we get tokens immediately, log them in
        if (response.tokens) {
          const user = {
            id: response.user.id,
            email: response.user.email,
            full_name: response.user.full_name || `${response.user.first_name} ${response.user.last_name}`,
            first_name: response.user.first_name,
            last_name: response.user.last_name,
            is_active: response.user.is_active,
            created_at: response.user.created_at,
            updated_at: response.user.created_at,
          };

          login(user, response.tokens.access_token);
          router.push('/dashboard');
        } else {
          // Redirect to login with email verification notice
          router.push(`/login?email=${encodeURIComponent(data.email)}&verification_required=true`);
        }
      } else {
        toast.error('Registration failed: Invalid response from server');
      }
    } catch (error: any) {
      console.error('User registration error:', error);
      if (error.response?.status === 409) {
        toast.error('Email address is already registered');
      } else if (error.response?.status === 400) {
        const detail = error.response?.data?.detail;
        if (detail?.includes('tenant')) {
          toast.error('Invalid tenant. Please check your invitation link.');
        } else {
          toast.error(detail || 'Invalid registration data');
        }
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
                d="M18 9v3m0 0v3m0-3h3m-3 0h-3m-2-5a4 4 0 11-8 0 4 4 0 018 0zM3 20a6 6 0 0112 0v1H3v-1z"
              />
            </svg>
          </div>
          <h2 className="mt-6 text-center text-3xl font-extrabold text-gray-900">
            Join your team
          </h2>
          <p className="mt-2 text-center text-sm text-gray-600">
            Create your user account to access the print-on-demand platform
          </p>
        </div>
        
        <form className="mt-8 space-y-6" onSubmit={handleSubmit(onSubmit)}>
          <div className="space-y-4">
            {/* Personal Information */}
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label htmlFor="first_name" className="block text-sm font-medium text-gray-700">
                  First Name *
                </label>
                <input
                  {...register('first_name')}
                  type="text"
                  className="mt-1 appearance-none relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 rounded-md focus:outline-none focus:ring-primary-500 focus:border-primary-500 focus:z-10 sm:text-sm"
                  placeholder="John"
                />
                {errors.first_name && (
                  <p className="mt-1 text-sm text-red-600">{errors.first_name.message}</p>
                )}
              </div>

              <div>
                <label htmlFor="last_name" className="block text-sm font-medium text-gray-700">
                  Last Name *
                </label>
                <input
                  {...register('last_name')}
                  type="text"
                  className="mt-1 appearance-none relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 rounded-md focus:outline-none focus:ring-primary-500 focus:border-primary-500 focus:z-10 sm:text-sm"
                  placeholder="Doe"
                />
                {errors.last_name && (
                  <p className="mt-1 text-sm text-red-600">{errors.last_name.message}</p>
                )}
              </div>
            </div>

            <div>
              <label htmlFor="email" className="block text-sm font-medium text-gray-700">
                Email Address *
              </label>
              <input
                {...register('email')}
                type="email"
                autoComplete="email"
                className="mt-1 appearance-none relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 rounded-md focus:outline-none focus:ring-primary-500 focus:border-primary-500 focus:z-10 sm:text-sm"
                placeholder="john@example.com"
              />
              {errors.email && (
                <p className="mt-1 text-sm text-red-600">{errors.email.message}</p>
              )}
            </div>

            <div>
              <label htmlFor="shop_name" className="block text-sm font-medium text-gray-700">
                Shop Name *
              </label>
              <input
                {...register('shop_name')}
                type="text"
                className="mt-1 appearance-none relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 rounded-md focus:outline-none focus:ring-primary-500 focus:border-primary-500 focus:z-10 sm:text-sm"
                placeholder="My Print Shop"
              />
              <p className="mt-1 text-xs text-gray-500">
                This will be the name of your shop or store within the platform
              </p>
              {errors.shop_name && (
                <p className="mt-1 text-sm text-red-600">{errors.shop_name.message}</p>
              )}
            </div>

            <div>
              <label htmlFor="password" className="block text-sm font-medium text-gray-700">
                Password *
              </label>
              <div className="mt-1 relative">
                <input
                  {...register('password')}
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
              {errors.password && (
                <p className="mt-1 text-sm text-red-600">{errors.password.message}</p>
              )}
            </div>

            <div>
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

            {/* Preferences */}
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label htmlFor="timezone" className="block text-sm font-medium text-gray-700">
                  Timezone
                </label>
                <select
                  {...register('timezone')}
                  className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-primary-500 focus:border-primary-500 sm:text-sm"
                >
                  {timezones.map(tz => (
                    <option key={tz.value} value={tz.value}>
                      {tz.label}
                    </option>
                  ))}
                </select>
                {errors.timezone && (
                  <p className="mt-1 text-sm text-red-600">{errors.timezone.message}</p>
                )}
              </div>

              <div>
                <label htmlFor="language" className="block text-sm font-medium text-gray-700">
                  Language
                </label>
                <select
                  {...register('language')}
                  className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-primary-500 focus:border-primary-500 sm:text-sm"
                >
                  {languages.map(lang => (
                    <option key={lang.value} value={lang.value}>
                      {lang.label}
                    </option>
                  ))}
                </select>
                {errors.language && (
                  <p className="mt-1 text-sm text-red-600">{errors.language.message}</p>
                )}
              </div>
            </div>

            {/* Marketing Consent */}
            <div className="flex items-start">
              <div className="flex items-center h-5">
                <input
                  {...register('marketing_consent')}
                  type="checkbox"
                  className="h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300 rounded"
                />
              </div>
              <div className="ml-3 text-sm">
                <label className="text-gray-700">
                  I would like to receive marketing emails and product updates
                </label>
              </div>
            </div>

            {/* Terms and Conditions */}
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

          <div>
            <button
              type="submit"
              disabled={loading}
              className="group relative w-full flex justify-center py-2 px-4 border border-transparent text-sm font-medium rounded-md text-white bg-primary-600 hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading ? (
                <div className="flex items-center">
                  <div className="animate-spin -ml-1 mr-3 h-5 w-5 border-2 border-white border-t-transparent rounded-full"></div>
                  Creating Account...
                </div>
              ) : (
                'Create Account'
              )}
            </button>
          </div>
        </form>

        <div className="text-center">
          <p className="text-sm text-gray-600">
            Already have an account?{' '}
            <Link href="/login" className="font-medium text-primary-600 hover:text-primary-500">
              Sign in
            </Link>
          </p>
          <p className="mt-2 text-sm text-gray-600">
            Need to create a company account?{' '}
            <Link href="/tenant-signup" className="font-medium text-primary-600 hover:text-primary-500">
              Create company account
            </Link>
          </p>
        </div>

        {/* Invitation Info */}
        {(tenant_id || invitation_code) && (
          <div className="mt-6 p-4 bg-green-50 border border-green-200 rounded-md">
            <div className="flex">
              <div className="flex-shrink-0">
                <svg className="h-5 w-5 text-green-400" viewBox="0 0 20 20" fill="currentColor">
                  <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                </svg>
              </div>
              <div className="ml-3">
                <h3 className="text-sm font-medium text-green-800">Team Invitation</h3>
                <div className="mt-2 text-sm text-green-700">
                  <p>You've been invited to join a team. Complete the registration to access your workspace.</p>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}