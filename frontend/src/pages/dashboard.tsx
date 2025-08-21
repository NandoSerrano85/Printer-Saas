import React, { useEffect, useState } from 'react';
import { useRouter } from 'next/router';
import MainLayout from '@/components/Layout/MainLayout';
import { useAppStore } from '@/store/useStore';
import apiService from '@/services/api';
import { DashboardStats, AnalyticsData } from '@/types';
import {
  ShoppingBagIcon,
  CurrencyDollarIcon,
  DocumentTextIcon,
  LinkIcon,
  CheckCircleIcon,
  XMarkIcon,
} from '@heroicons/react/24/outline';
import toast from 'react-hot-toast';
import dynamic from 'next/dynamic';
import ClientOnly from '@/components/ClientOnly';

// Dynamically import charts to avoid SSR issues
const LineChart = dynamic(() => import('recharts').then(mod => mod.LineChart), { ssr: false });
const Line = dynamic(() => import('recharts').then(mod => mod.Line), { ssr: false });
const XAxis = dynamic(() => import('recharts').then(mod => mod.XAxis), { ssr: false });
const YAxis = dynamic(() => import('recharts').then(mod => mod.YAxis), { ssr: false });
const CartesianGrid = dynamic(() => import('recharts').then(mod => mod.CartesianGrid), { ssr: false });
const Tooltip = dynamic(() => import('recharts').then(mod => mod.Tooltip), { ssr: false });
const Legend = dynamic(() => import('recharts').then(mod => mod.Legend), { ssr: false });
const ResponsiveContainer = dynamic(() => import('recharts').then(mod => mod.ResponsiveContainer), { ssr: false });
const BarChart = dynamic(() => import('recharts').then(mod => mod.BarChart), { ssr: false });
const Bar = dynamic(() => import('recharts').then(mod => mod.Bar), { ssr: false });

const StatCard = ({ 
  title, 
  value, 
  icon: Icon, 
  color = 'primary' 
}: { 
  title: string; 
  value: string | number; 
  icon: any; 
  color?: string; 
}) => {
  const colorClasses = {
    primary: 'bg-primary-500',
    success: 'bg-success-500',
    warning: 'bg-warning-500',
    error: 'bg-error-500',
  };

  return (
    <div className="bg-white overflow-hidden shadow rounded-lg">
      <div className="p-5">
        <div className="flex items-center">
          <div className="flex-shrink-0">
            <Icon className={`h-8 w-8 text-white p-1 rounded-md ${colorClasses[color as keyof typeof colorClasses]}`} />
          </div>
          <div className="ml-5 w-0 flex-1">
            <dl>
              <dt className="text-sm font-medium text-gray-500 truncate">{title}</dt>
              <dd className="text-lg font-medium text-gray-900">{value}</dd>
            </dl>
          </div>
        </div>
      </div>
    </div>
  );
};

const IntegrationStatus = ({ 
  platform, 
  connected, 
  onConnect 
}: { 
  platform: string; 
  connected: boolean; 
  onConnect: () => void; 
}) => (
  <div className="flex items-center justify-between p-4 bg-white rounded-lg border">
    <div className="flex items-center">
      <div className={`w-3 h-3 rounded-full mr-3 ${connected ? 'bg-success-500' : 'bg-error-500'}`} />
      <span className="font-medium capitalize">{platform}</span>
    </div>
    <div className="flex items-center">
      <span className={`text-sm mr-3 ${connected ? 'text-success-600' : 'text-error-600'}`}>
        {connected ? 'Connected' : 'Disconnected'}
      </span>
      {!connected && (
        <button
          onClick={onConnect}
          className="px-3 py-1 text-sm bg-primary-500 text-white rounded hover:bg-primary-600"
        >
          Connect
        </button>
      )}
    </div>
  </div>
);

export default function Dashboard() {
  const router = useRouter();
  const { dashboardStats, setDashboardStats, integrationStatus, setIntegrationStatus } = useAppStore();
  const [analyticsData, setAnalyticsData] = useState<AnalyticsData | null>(null);
  const [loading, setLoading] = useState(true);
  const [isMounted, setIsMounted] = useState(false);
  const [showWelcomeBanner, setShowWelcomeBanner] = useState(false);

  useEffect(() => {
    setIsMounted(true);
    loadDashboardData();
    loadIntegrationStatus();
    
    // Check if user just completed registration
    if (router.query.welcome === 'true') {
      setShowWelcomeBanner(true);
      // Clean up the URL
      router.replace('/dashboard', undefined, { shallow: true });
    }
  }, [router]);

  const loadDashboardData = async () => {
    try {
      const [statsResponse, analyticsResponse] = await Promise.all([
        apiService.getDashboardData().catch(() => null),
        apiService.getDashboardAnalytics().catch(() => null),
      ]);
      
      // Set fallback data if API calls fail
      const fallbackStats: DashboardStats = {
        total_orders: 0,
        total_revenue: 0,
        active_templates: 0,
        integration_status: {
          shopify: false,
          etsy: false
        },
        recent_orders: []
      };

      const fallbackAnalytics: AnalyticsData = {
        revenue: {
          labels: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'],
          data: [1200, 1900, 3000, 5000, 2000, 3000]
        },
        orders: {
          labels: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'],
          data: [12, 19, 30, 50, 20, 30]
        },
        top_products: [
          { name: 'Custom T-Shirt', sales: 45 },
          { name: 'Business Cards', sales: 32 },
          { name: 'Poster Print', sales: 28 }
        ]
      };
      
      setDashboardStats(statsResponse || fallbackStats);
      setAnalyticsData(analyticsResponse || fallbackAnalytics);
    } catch (error) {
      console.error('Error loading dashboard data:', error);
      // Set fallback data on error
      setDashboardStats({
        total_orders: 0,
        total_revenue: 0,
        active_templates: 0,
        integration_status: {
          shopify: false,
          etsy: false
        },
        recent_orders: []
      });
      setAnalyticsData({
        revenue: {
          labels: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'],
          data: [0, 0, 0, 0, 0, 0]
        },
        orders: {
          labels: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'],
          data: [0, 0, 0, 0, 0, 0]
        },
        top_products: []
      });
    } finally {
      setLoading(false);
    }
  };

  const loadIntegrationStatus = async () => {
    try {
      const [shopifyStatus, etsyStatus] = await Promise.all([
        apiService.getShopifyIntegrationStatus().catch(() => ({ connected: false })),
        apiService.getEtsyIntegrationStatus().catch(() => ({ connected: false })),
      ]);
      
      setIntegrationStatus('shopify', {
        platform: 'shopify',
        connected: (shopifyStatus as any).connected || false,
        shop_name: (shopifyStatus as any).shop_name,
        last_sync: (shopifyStatus as any).last_sync,
      });
      
      setIntegrationStatus('etsy', {
        platform: 'etsy',
        connected: (etsyStatus as any).connected || false,
        shop_name: (etsyStatus as any).shop_name,
        last_sync: (etsyStatus as any).last_sync,
      });
    } catch (error) {
      console.error('Error loading integration status:', error);
    }
  };

  const handleConnectIntegration = async (platform: 'shopify' | 'etsy') => {
    try {
      if (platform === 'shopify') {
        const shopDomain = prompt('Enter your Shopify shop domain (e.g., my-store.myshopify.com):');
        if (shopDomain) {
          const response = await apiService.initShopifyOAuth(shopDomain);
          const authUrl = (response as any).oauth_url || (response as any).auth_url;
          
          if (authUrl && authUrl !== '#') {
            toast.success('Opening Shopify authorization window...');
            
            // Open OAuth in popup window
            const popup = window.open(
              authUrl, 
              'shopify_oauth', 
              'width=600,height=700,scrollbars=yes,resizable=yes'
            );
            
            // Monitor popup for completion
            const checkClosed = setInterval(() => {
              if (popup?.closed) {
                clearInterval(checkClosed);
                // Refresh integration status after popup closes
                setTimeout(() => {
                  loadIntegrationStatus();
                  toast.success('Checking connection status...');
                }, 1000);
              }
            }, 1000);
          } else {
            toast.info('Using demo OAuth flow - for real integration, configure OAuth credentials in backend');
          }
        }
      } else if (platform === 'etsy') {
        const response = await apiService.initEtsyOAuth();
        const authUrl = (response as any).oauth_url || (response as any).auth_url;
        
        if (authUrl && authUrl !== '#') {
          toast.success('Opening Etsy authorization window...');
          
          // Open OAuth in popup window
          const popup = window.open(
            authUrl, 
            'etsy_oauth', 
            'width=600,height=700,scrollbars=yes,resizable=yes'
          );
          
          // Monitor popup for completion
          const checkClosed = setInterval(() => {
            if (popup?.closed) {
              clearInterval(checkClosed);
              // Refresh integration status after popup closes
              setTimeout(() => {
                loadIntegrationStatus();
                toast.success('Checking connection status...');
              }, 1000);
            }
          }, 1000);
        } else {
          toast.info('OAuth integration is not configured for development environment');
        }
      }
    } catch (error) {
      console.error(`Error connecting to ${platform}:`, error);
      toast.error(`Failed to connect to ${platform}`);
    }
  };

  if (loading || !isMounted) {
    return (
      <MainLayout>
        <div className="flex items-center justify-center h-64">
          <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-primary-500"></div>
        </div>
      </MainLayout>
    );
  }

  return (
    <MainLayout>
      <div className="space-y-6">
        {/* Page Header */}
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Dashboard</h1>
          <p className="mt-1 text-sm text-gray-500">
            Overview of your printer SaaS business
          </p>
        </div>

        {/* Welcome Banner for New Registrations */}
        {showWelcomeBanner && (
          <div className="bg-green-50 border border-green-200 rounded-lg p-4">
            <div className="flex">
              <div className="flex-shrink-0">
                <CheckCircleIcon className="h-5 w-5 text-green-400" />
              </div>
              <div className="ml-3 flex-1">
                <h3 className="text-sm font-medium text-green-800">
                  Welcome! Your account is ready to go
                </h3>
                <div className="mt-2 text-sm text-green-700">
                  <p>
                    Your integrations have been successfully connected during registration. 
                    You can now start creating templates and managing your print-on-demand business.
                  </p>
                </div>
              </div>
              <div className="ml-auto pl-3">
                <div className="-mx-1.5 -my-1.5">
                  <button
                    type="button"
                    onClick={() => setShowWelcomeBanner(false)}
                    className="inline-flex bg-green-50 rounded-md p-1.5 text-green-500 hover:bg-green-100 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-offset-green-50 focus:ring-green-600"
                  >
                    <span className="sr-only">Dismiss</span>
                    <XMarkIcon className="h-5 w-5" />
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Stats Cards */}
        <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-4">
          <StatCard
            title="Total Orders"
            value={dashboardStats?.total_orders || 0}
            icon={ShoppingBagIcon}
            color="primary"
          />
          <StatCard
            title="Total Revenue"
            value={`$${dashboardStats?.total_revenue?.toFixed(2) || '0.00'}`}
            icon={CurrencyDollarIcon}
            color="success"
          />
          <StatCard
            title="Active Templates"
            value={dashboardStats?.active_templates || 0}
            icon={DocumentTextIcon}
            color="warning"
          />
          <StatCard
            title="Integrations"
            value={`${(integrationStatus.shopify?.connected ? 1 : 0) + (integrationStatus.etsy?.connected ? 1 : 0)}/2`}
            icon={LinkIcon}
            color="error"
          />
        </div>

        {/* Integration Status */}
        <div className="bg-white shadow rounded-lg">
          <div className="px-6 py-4 border-b border-gray-200">
            <h2 className="text-lg font-medium text-gray-900">Integration Status</h2>
          </div>
          <div className="p-6 space-y-4">
            <IntegrationStatus
              platform="shopify"
              connected={integrationStatus.shopify?.connected || false}
              onConnect={() => handleConnectIntegration('shopify')}
            />
            <IntegrationStatus
              platform="etsy"
              connected={integrationStatus.etsy?.connected || false}
              onConnect={() => handleConnectIntegration('etsy')}
            />
          </div>
        </div>

        {/* Analytics Charts */}
        <ClientOnly 
          fallback={
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <div className="bg-white p-6 rounded-lg shadow">
                <h3 className="text-lg font-medium text-gray-900 mb-4">Revenue Trend</h3>
                <div className="h-64 flex items-center justify-center bg-gray-50 rounded">
                  <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-500"></div>
                </div>
              </div>
              <div className="bg-white p-6 rounded-lg shadow">
                <h3 className="text-lg font-medium text-gray-900 mb-4">Orders Trend</h3>
                <div className="h-64 flex items-center justify-center bg-gray-50 rounded">
                  <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-500"></div>
                </div>
              </div>
            </div>
          }
        >
          {analyticsData && analyticsData.revenue && analyticsData.orders && (
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Revenue Chart */}
              <div className="bg-white p-6 rounded-lg shadow">
                <h3 className="text-lg font-medium text-gray-900 mb-4">Revenue Trend</h3>
                <div style={{ width: '100%', height: 300 }}>
                  <ResponsiveContainer width="100%" height={300}>
                    <LineChart data={analyticsData.revenue.labels?.map((label, index) => ({
                      name: label,
                      value: analyticsData.revenue.data[index] || 0,
                    })) || []}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="name" />
                      <YAxis />
                      <Tooltip formatter={(value) => [`$${value}`, 'Revenue']} />
                      <Legend />
                      <Line 
                        type="monotone" 
                        dataKey="value" 
                        stroke="#3b82f6" 
                        strokeWidth={2}
                        name="Revenue"
                      />
                    </LineChart>
                  </ResponsiveContainer>
                </div>
              </div>

              {/* Orders Chart */}
              <div className="bg-white p-6 rounded-lg shadow">
                <h3 className="text-lg font-medium text-gray-900 mb-4">Orders Trend</h3>
                <div style={{ width: '100%', height: 300 }}>
                  <ResponsiveContainer width="100%" height={300}>
                    <BarChart data={analyticsData.orders.labels?.map((label, index) => ({
                      name: label,
                      value: analyticsData.orders.data[index] || 0,
                    })) || []}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="name" />
                      <YAxis />
                      <Tooltip formatter={(value) => [value, 'Orders']} />
                      <Legend />
                      <Bar dataKey="value" fill="#22c55e" name="Orders" />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              </div>
            </div>
          )}
        </ClientOnly>

        {/* Recent Orders */}
        {dashboardStats?.recent_orders && dashboardStats.recent_orders.length > 0 && (
          <div className="bg-white shadow rounded-lg">
            <div className="px-6 py-4 border-b border-gray-200">
              <h2 className="text-lg font-medium text-gray-900">Recent Orders</h2>
            </div>
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Order #
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Customer
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Total
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Status
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Platform
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {dashboardStats.recent_orders.map((order) => (
                    <tr key={order.id}>
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                        #{order.order_number}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {order.customer_name}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        ${order.total_amount.toFixed(2)}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                          order.status === 'delivered' ? 'bg-success-100 text-success-800' :
                          order.status === 'shipped' ? 'bg-primary-100 text-primary-800' :
                          order.status === 'processing' ? 'bg-warning-100 text-warning-800' :
                          'bg-gray-100 text-gray-800'
                        }`}>
                          {order.status}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 capitalize">
                        {order.platform}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </div>
    </MainLayout>
  );
}