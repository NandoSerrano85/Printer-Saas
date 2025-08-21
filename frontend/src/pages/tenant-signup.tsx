import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/router';
import Link from 'next/link';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { useAuthStore } from '@/store/useStore';
import apiService from '@/services/api';
import toast from 'react-hot-toast';
import { 
  EyeIcon, 
  EyeSlashIcon, 
  CheckCircleIcon, 
  ChevronRightIcon,
  ShoppingBagIcon,
  GlobeAltIcon
} from '@heroicons/react/24/outline';

// Step 1: Company and Admin Details + Integration Selection
const step1Schema = z.object({
  company_name: z.string().min(2, 'Company name must be at least 2 characters'),
  subdomain: z.string()
    .min(3, 'Subdomain must be at least 3 characters')
    .max(20, 'Subdomain must be less than 20 characters')
    .regex(/^[a-z0-9-]+$/, 'Subdomain can only contain lowercase letters, numbers, and hyphens')
    .refine(val => !val.startsWith('-') && !val.endsWith('-'), 'Subdomain cannot start or end with hyphens'),
  admin_first_name: z.string().min(1, 'First name is required'),
  admin_last_name: z.string().min(1, 'Last name is required'),
  admin_email: z.string().email('Invalid email address'),
  admin_password: z.string()
    .min(8, 'Password must be at least 8 characters')
    .regex(/^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)/, 'Password must contain at least one uppercase letter, one lowercase letter, and one number'),
  confirm_password: z.string(),
  subscription_plan: z.string().default('basic'),
  selected_integrations: z.array(z.enum(['etsy', 'shopify'])).min(1, 'Please select at least one integration'),
  terms_accepted: z.boolean().refine(val => val === true, 'You must accept the terms and conditions'),
}).refine(data => data.admin_password === data.confirm_password, {
  message: "Passwords don't match",
  path: ['confirm_password'],
});

type Step1FormData = z.infer<typeof step1Schema>;

enum RegistrationStep {
  DETAILS = 1,
  INTEGRATIONS = 2,
  COMPLETE = 3
}

interface IntegrationOption {
  id: 'etsy' | 'shopify';
  name: string;
  description: string;
  icon: React.ReactNode;
  color: string;
}

const integrationOptions: IntegrationOption[] = [
  {
    id: 'etsy',
    name: 'Etsy',
    description: 'Connect your Etsy shop to sync products and orders',
    icon: <ShoppingBagIcon className="h-8 w-8" />,
    color: 'bg-orange-500'
  },
  {
    id: 'shopify',
    name: 'Shopify',
    description: 'Connect your Shopify store to manage products and orders',
    icon: <GlobeAltIcon className="h-8 w-8" />,
    color: 'bg-green-500'
  }
];

export default function TenantSignup() {
  const router = useRouter();
  const { login, isAuthenticated, isLoading } = useAuthStore();
  const [currentStep, setCurrentStep] = useState(RegistrationStep.DETAILS);
  const [loading, setLoading] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [subdomainAvailable, setSubdomainAvailable] = useState<boolean | null>(null);
  const [checkingSubdomain, setCheckingSubdomain] = useState(false);
  
  // Registration state
  const [registrationToken, setRegistrationToken] = useState<string>('');
  const [oauthUrls, setOauthUrls] = useState<Record<string, string>>({});
  const [connectedIntegrations, setConnectedIntegrations] = useState<string[]>([]);
  const [selectedIntegrations, setSelectedIntegrations] = useState<string[]>([]);
  const [shopifyStoreDomain, setShopifyStoreDomain] = useState<string>('');

  const {
    register,
    handleSubmit,
    formState: { errors },
    watch,
    setValue,
    trigger,
  } = useForm<Step1FormData>({
    resolver: zodResolver(step1Schema),
    defaultValues: {
      subscription_plan: 'basic',
      selected_integrations: [],
    },
  });

  const watchedSubdomain = watch('subdomain');
  const watchedIntegrations = watch('selected_integrations');

  useEffect(() => {
    if (!isLoading && isAuthenticated) {
      router.push('/dashboard');
    }
  }, [isAuthenticated, isLoading, router]);

  // Handle OAuth callback
  useEffect(() => {
    const handleOAuthCallback = async () => {
      const urlParams = new URLSearchParams(window.location.search);
      const code = urlParams.get('code');
      const state = urlParams.get('state');
      const platform = urlParams.get('platform');
      const error = urlParams.get('error');

      if (error) {
        toast.error(`OAuth error: ${error}`);
        return;
      }

      if (code && state && platform && registrationToken) {
        try {
          const response = await apiService.connectIntegration({
            registration_token: registrationToken,
            platform,
            oauth_code: code,
            oauth_state: state,
          });

          if (response.success) {
            setConnectedIntegrations(prev => [...prev, platform]);
            toast.success(`${response.platform} connected successfully!`);
            
            // Clean URL
            window.history.replaceState({}, document.title, window.location.pathname);
          }
        } catch (error: any) {
          console.error('OAuth connection error:', error);
          toast.error(error.response?.data?.detail || 'Integration connection failed');
        }
      }
    };

    if (currentStep === RegistrationStep.INTEGRATIONS && registrationToken) {
      handleOAuthCallback();
    }
  }, [currentStep, registrationToken]);

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

  const onStep1Submit = async (data: Step1FormData) => {
    if (subdomainAvailable === false) {
      toast.error('Please choose an available subdomain');
      return;
    }

    setLoading(true);
    
    try {
      const response = await apiService.startTenantRegistration({
        company_name: data.company_name,
        subdomain: data.subdomain,
        admin_email: data.admin_email,
        admin_password: data.admin_password,
        admin_first_name: data.admin_first_name,
        admin_last_name: data.admin_last_name,
        selected_integrations: data.selected_integrations,
      });

      if (response.success) {
        setRegistrationToken(response.registration_token);
        setOauthUrls(response.oauth_urls);
        setSelectedIntegrations(data.selected_integrations);
        setCurrentStep(RegistrationStep.INTEGRATIONS);
        toast.success('Company registered! Now connect your integrations.');
      } else {
        toast.error('Registration failed');
      }
    } catch (error: any) {
      console.error('Registration error:', error);
      toast.error(error.response?.data?.detail || 'Registration failed');
    } finally {
      setLoading(false);
    }
  };

  const handleIntegrationConnect = (platform: string) => {
    if (platform === 'shopify') {
      // For Shopify, we need to collect the store domain first
      handleShopifyConnect();
    } else {
      const url = oauthUrls[platform];
      if (url) {
        // Open OAuth URL in a popup or redirect
        window.location.href = url;
      }
    }
  };

  const handleShopifyConnect = () => {
    if (!shopifyStoreDomain.trim()) {
      toast.error('Please enter your Shopify store domain');
      return;
    }

    // Generate the actual Shopify OAuth URL with the provided store domain
    const placeholderUrl = oauthUrls['shopify'];
    if (!placeholderUrl) {
      toast.error('Shopify OAuth not available');
      return;
    }

    // Extract parameters from placeholder URL
    const urlParams = new URLSearchParams(placeholderUrl.split('?')[1]);
    const clientId = urlParams.get('client_id');
    const scope = urlParams.get('scope');
    const redirectUri = urlParams.get('redirect_uri');
    const state = urlParams.get('state');

    // Clean the store domain (remove .myshopify.com if present)
    const cleanDomain = shopifyStoreDomain.replace('.myshopify.com', '').trim();
    
    // Build the actual OAuth URL
    const shopifyOAuthUrl = 
      `https://${cleanDomain}.myshopify.com/admin/oauth/authorize?` +
      `client_id=${clientId}&` +
      `scope=${scope}&` +
      `redirect_uri=${encodeURIComponent(redirectUri)}&` +
      `state=${state}`;

    // Redirect to Shopify OAuth
    window.location.href = shopifyOAuthUrl;
  };

  const completeRegistration = async () => {
    if (connectedIntegrations.length !== selectedIntegrations.length) {
      toast.error('Please connect all selected integrations first');
      return;
    }

    setLoading(true);
    
    try {
      const response = await apiService.completeRegistration({
        registration_token: registrationToken,
      });

      if (response.success && response.tokens) {
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
        toast.success(`Welcome to ${response.tenant.company_name}!`);
        router.push('/dashboard?welcome=true');
      } else {
        toast.error('Registration completion failed');
      }
    } catch (error: any) {
      console.error('Registration completion error:', error);
      toast.error(error.response?.data?.detail || 'Registration completion failed');
    } finally {
      setLoading(false);
    }
  };

  const renderProgressSteps = () => (
    <div className="mb-8">
      <div className="flex items-center justify-center">
        <div className="flex items-center space-x-4">
          {/* Step 1 */}
          <div className="flex items-center">
            <div className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium ${
              currentStep >= RegistrationStep.DETAILS 
                ? 'bg-primary-600 text-white' 
                : 'bg-gray-200 text-gray-500'
            }`}>
              1
            </div>
            <span className="ml-2 text-sm font-medium text-gray-900">Company Details</span>
          </div>
          
          <ChevronRightIcon className="h-5 w-5 text-gray-400" />
          
          {/* Step 2 */}
          <div className="flex items-center">
            <div className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium ${
              currentStep >= RegistrationStep.INTEGRATIONS 
                ? 'bg-primary-600 text-white' 
                : 'bg-gray-200 text-gray-500'
            }`}>
              2
            </div>
            <span className="ml-2 text-sm font-medium text-gray-900">Connect Integrations</span>
          </div>
          
          <ChevronRightIcon className="h-5 w-5 text-gray-400" />
          
          {/* Step 3 */}
          <div className="flex items-center">
            <div className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium ${
              currentStep >= RegistrationStep.COMPLETE 
                ? 'bg-primary-600 text-white' 
                : 'bg-gray-200 text-gray-500'
            }`}>
              3
            </div>
            <span className="ml-2 text-sm font-medium text-gray-900">Complete Setup</span>
          </div>
        </div>
      </div>
    </div>
  );

  const renderStep1 = () => (
    <form onSubmit={handleSubmit(onStep1Submit)} className="space-y-6">
      {/* Company Information */}
      <div className="bg-gray-50 p-6 rounded-lg">
        <h3 className="text-lg font-medium text-gray-900 mb-4">Company Information</h3>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label htmlFor="company_name" className="block text-sm font-medium text-gray-700">
              Company Name
            </label>
            <input
              {...register('company_name')}
              type="text"
              className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-primary-500 focus:border-primary-500"
              placeholder="Your Company Name"
            />
            {errors.company_name && (
              <p className="mt-1 text-sm text-red-600">{errors.company_name.message}</p>
            )}
          </div>

          <div>
            <label htmlFor="subdomain" className="block text-sm font-medium text-gray-700">
              Subdomain
            </label>
            <div className="mt-1 flex rounded-md shadow-sm">
              <input
                {...register('subdomain')}
                type="text"
                className="flex-1 block w-full border-gray-300 rounded-l-md focus:ring-primary-500 focus:border-primary-500"
                placeholder="yourcompany"
              />
              <span className="inline-flex items-center px-3 rounded-r-md border border-l-0 border-gray-300 bg-gray-50 text-gray-500 text-sm">
                .printersaas.com
              </span>
            </div>
            {/* Subdomain availability indicator */}
            {watchedSubdomain && watchedSubdomain.length >= 3 && (
              <div className="mt-1 flex items-center">
                {checkingSubdomain ? (
                  <span className="text-sm text-gray-500">Checking availability...</span>
                ) : subdomainAvailable === true ? (
                  <span className="text-sm text-green-600 flex items-center">
                    <CheckCircleIcon className="h-4 w-4 mr-1" />
                    Available
                  </span>
                ) : subdomainAvailable === false ? (
                  <span className="text-sm text-red-600">Already taken</span>
                ) : null}
              </div>
            )}
            {errors.subdomain && (
              <p className="mt-1 text-sm text-red-600">{errors.subdomain.message}</p>
            )}
          </div>
        </div>
      </div>

      {/* Admin User Information */}
      <div className="bg-gray-50 p-6 rounded-lg">
        <h3 className="text-lg font-medium text-gray-900 mb-4">Admin Account</h3>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label htmlFor="admin_first_name" className="block text-sm font-medium text-gray-700">
              First Name
            </label>
            <input
              {...register('admin_first_name')}
              type="text"
              className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-primary-500 focus:border-primary-500"
            />
            {errors.admin_first_name && (
              <p className="mt-1 text-sm text-red-600">{errors.admin_first_name.message}</p>
            )}
          </div>

          <div>
            <label htmlFor="admin_last_name" className="block text-sm font-medium text-gray-700">
              Last Name
            </label>
            <input
              {...register('admin_last_name')}
              type="text"
              className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-primary-500 focus:border-primary-500"
            />
            {errors.admin_last_name && (
              <p className="mt-1 text-sm text-red-600">{errors.admin_last_name.message}</p>
            )}
          </div>

          <div>
            <label htmlFor="admin_email" className="block text-sm font-medium text-gray-700">
              Email Address
            </label>
            <input
              {...register('admin_email')}
              type="email"
              className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-primary-500 focus:border-primary-500"
            />
            {errors.admin_email && (
              <p className="mt-1 text-sm text-red-600">{errors.admin_email.message}</p>
            )}
          </div>

          <div>
            <label htmlFor="admin_password" className="block text-sm font-medium text-gray-700">
              Password
            </label>
            <div className="mt-1 relative">
              <input
                {...register('admin_password')}
                type={showPassword ? 'text' : 'password'}
                className="block w-full pr-10 border-gray-300 rounded-md shadow-sm focus:ring-primary-500 focus:border-primary-500"
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
            {errors.admin_password && (
              <p className="mt-1 text-sm text-red-600">{errors.admin_password.message}</p>
            )}
          </div>

          <div className="md:col-span-2">
            <label htmlFor="confirm_password" className="block text-sm font-medium text-gray-700">
              Confirm Password
            </label>
            <div className="mt-1 relative">
              <input
                {...register('confirm_password')}
                type={showConfirmPassword ? 'text' : 'password'}
                className="block w-full pr-10 border-gray-300 rounded-md shadow-sm focus:ring-primary-500 focus:border-primary-500"
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
      </div>

      {/* Integration Selection */}
      <div className="bg-gray-50 p-6 rounded-lg">
        <h3 className="text-lg font-medium text-gray-900 mb-4">Choose Your Integrations</h3>
        <p className="text-sm text-gray-600 mb-4">
          Select at least one platform to connect. You can add more integrations later.
        </p>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {integrationOptions.map((integration) => (
            <label
              key={integration.id}
              className={`relative flex items-center p-4 border-2 rounded-lg cursor-pointer hover:bg-gray-50 ${
                watchedIntegrations?.includes(integration.id)
                  ? 'border-primary-500 bg-primary-50'
                  : 'border-gray-200'
              }`}
            >
              <input
                {...register('selected_integrations')}
                type="checkbox"
                value={integration.id}
                className="sr-only"
              />
              
              <div className={`flex-shrink-0 w-10 h-10 rounded-full ${integration.color} flex items-center justify-center text-white mr-4`}>
                {integration.icon}
              </div>
              
              <div className="flex-1">
                <h4 className="text-sm font-medium text-gray-900">{integration.name}</h4>
                <p className="text-sm text-gray-500">{integration.description}</p>
              </div>
              
              {watchedIntegrations?.includes(integration.id) && (
                <CheckCircleIcon className="h-5 w-5 text-primary-500" />
              )}
            </label>
          ))}
        </div>
        
        {errors.selected_integrations && (
          <p className="mt-2 text-sm text-red-600">{errors.selected_integrations.message}</p>
        )}
      </div>

      {/* Terms */}
      <div className="flex items-center">
        <input
          {...register('terms_accepted')}
          type="checkbox"
          className="h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300 rounded"
        />
        <label htmlFor="terms_accepted" className="ml-2 block text-sm text-gray-900">
          I agree to the{' '}
          <Link href="/terms" className="text-primary-600 hover:text-primary-500">
            Terms of Service
          </Link>{' '}
          and{' '}
          <Link href="/privacy" className="text-primary-600 hover:text-primary-500">
            Privacy Policy
          </Link>
        </label>
      </div>
      {errors.terms_accepted && (
        <p className="text-sm text-red-600">{errors.terms_accepted.message}</p>
      )}

      <button
        type="submit"
        disabled={loading || subdomainAvailable === false}
        className="w-full flex justify-center py-3 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-primary-600 hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 disabled:opacity-50 disabled:cursor-not-allowed"
      >
        {loading ? (
          <div className="flex items-center">
            <div className="animate-spin -ml-1 mr-3 h-5 w-5 border-2 border-white border-t-transparent rounded-full"></div>
            Creating Account...
          </div>
        ) : (
          'Continue to Integrations'
        )}
      </button>
    </form>
  );

  const renderStep2 = () => (
    <div className="space-y-6">
      <div className="text-center">
        <h3 className="text-lg font-medium text-gray-900 mb-2">Connect Your Integrations</h3>
        <p className="text-sm text-gray-600">
          Connect your selected platforms to start importing your products and orders.
        </p>
      </div>

      <div className="space-y-4">
        {selectedIntegrations.map((platformId) => {
          const integration = integrationOptions.find(opt => opt.id === platformId);
          const isConnected = connectedIntegrations.includes(platformId);
          
          if (!integration) return null;

          return (
            <div
              key={platformId}
              className={`border-2 rounded-lg p-6 ${
                isConnected ? 'border-green-500 bg-green-50' : 'border-gray-200'
              }`}
            >
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center">
                    <div className={`w-12 h-12 rounded-full ${integration.color} flex items-center justify-center text-white mr-4`}>
                      {integration.icon}
                    </div>
                    <div>
                      <h4 className="text-lg font-medium text-gray-900">{integration.name}</h4>
                      <p className="text-sm text-gray-500">{integration.description}</p>
                    </div>
                  </div>
                  
                  <div className="flex items-center">
                    {isConnected ? (
                      <div className="flex items-center text-green-600">
                        <CheckCircleIcon className="h-5 w-5 mr-2" />
                        Connected
                      </div>
                    ) : (
                      <button
                        onClick={() => handleIntegrationConnect(platformId)}
                        disabled={platformId === 'shopify' && !shopifyStoreDomain.trim()}
                        className="px-4 py-2 bg-primary-600 text-white rounded-md hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 disabled:opacity-50 disabled:cursor-not-allowed"
                      >
                        Connect {integration.name}
                      </button>
                    )}
                  </div>
                </div>
                
                {/* Shopify store domain input */}
                {platformId === 'shopify' && !isConnected && (
                  <div>
                    <label htmlFor="shopify-domain" className="block text-sm font-medium text-gray-700 mb-2">
                      Shopify Store Domain
                    </label>
                    <div className="flex rounded-md shadow-sm">
                      <input
                        type="text"
                        id="shopify-domain"
                        value={shopifyStoreDomain}
                        onChange={(e) => setShopifyStoreDomain(e.target.value)}
                        className="flex-1 block w-full border-gray-300 rounded-l-md focus:ring-primary-500 focus:border-primary-500 sm:text-sm"
                        placeholder="your-store"
                      />
                      <span className="inline-flex items-center px-3 rounded-r-md border border-l-0 border-gray-300 bg-gray-50 text-gray-500 sm:text-sm">
                        .myshopify.com
                      </span>
                    </div>
                    <p className="mt-1 text-xs text-gray-500">
                      Enter your Shopify store domain (without .myshopify.com)
                    </p>
                  </div>
                )}
              </div>
            </div>
          );
        })}
      </div>

      {connectedIntegrations.length === selectedIntegrations.length && (
        <button
          onClick={completeRegistration}
          disabled={loading}
          className="w-full flex justify-center py-3 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-green-600 hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-green-500 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {loading ? (
            <div className="flex items-center">
              <div className="animate-spin -ml-1 mr-3 h-5 w-5 border-2 border-white border-t-transparent rounded-full"></div>
              Completing Setup...
            </div>
          ) : (
            'Complete Registration'
          )}
        </button>
      )}
    </div>
  );

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-2xl w-full space-y-8">
        <div className="text-center">
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
            Create Your Company Account
          </h2>
          <p className="mt-2 text-center text-sm text-gray-600">
            Get started with your print-on-demand business in minutes
          </p>
        </div>

        {renderProgressSteps()}

        <div className="bg-white shadow rounded-lg p-8">
          {currentStep === RegistrationStep.DETAILS && renderStep1()}
          {currentStep === RegistrationStep.INTEGRATIONS && renderStep2()}
        </div>

        <div className="text-center">
          <p className="text-sm text-gray-600">
            Already have an account?{' '}
            <Link href="/tenant-login" className="font-medium text-primary-600 hover:text-primary-500">
              Sign in
            </Link>
          </p>
          <p className="mt-2 text-sm text-gray-600">
            Prefer simple registration?{' '}
            <Link href="/tenant-signup-old" className="font-medium text-primary-600 hover:text-primary-500">
              Skip integrations setup
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
}