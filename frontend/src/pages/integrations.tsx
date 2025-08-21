import React, { useEffect, useState } from 'react';
import { useRouter } from 'next/router';
import MainLayout from '@/components/Layout/MainLayout';
import { useAppStore } from '@/store/useStore';
import apiService from '@/services/api';
import { IntegrationStatus } from '@/types';
import {
  CheckCircleIcon,
  ExclamationCircleIcon,
  ArrowPathIcon,
  LinkIcon,
} from '@heroicons/react/24/outline';
import toast from 'react-hot-toast';
import { format } from 'date-fns';

const IntegrationCard = ({
  title,
  description,
  platform,
  status,
  onConnect,
  onDisconnect,
  onSync,
  loading,
}: {
  title: string;
  description: string;
  platform: 'shopify' | 'etsy';
  status: IntegrationStatus | null;
  onConnect: () => void;
  onDisconnect: () => void;
  onSync: () => void;
  loading: boolean;
}) => {
  const isConnected = status?.connected || false;

  return (
    <div className="bg-white overflow-hidden shadow rounded-lg">
      <div className="px-6 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center">
            <div className={`w-3 h-3 rounded-full mr-3 ${isConnected ? 'bg-success-500' : 'bg-error-500'}`} />
            <div>
              <h3 className="text-lg font-medium text-gray-900">{title}</h3>
              <p className="text-sm text-gray-500">{description}</p>
            </div>
          </div>
          <div className="flex items-center space-x-2">
            {isConnected ? (
              <CheckCircleIcon className="h-8 w-8 text-success-500" />
            ) : (
              <ExclamationCircleIcon className="h-8 w-8 text-error-500" />
            )}
          </div>
        </div>

        {isConnected && status && (
          <div className="mt-4 space-y-2">
            {status.shop_name && (
              <div className="text-sm">
                <span className="font-medium text-gray-700">Shop:</span>
                <span className="ml-2 text-gray-600">{status.shop_name}</span>
              </div>
            )}
            {status.last_sync && (
              <div className="text-sm">
                <span className="font-medium text-gray-700">Last Sync:</span>
                <span className="ml-2 text-gray-600">
                  {format(new Date(status.last_sync), 'MMM dd, yyyy HH:mm')}
                </span>
              </div>
            )}
            {status.error_message && (
              <div className="text-sm">
                <span className="font-medium text-error-700">Error:</span>
                <span className="ml-2 text-error-600">{status.error_message}</span>
              </div>
            )}
          </div>
        )}

        <div className="mt-6 flex space-x-3">
          {!isConnected ? (
            <button
              onClick={onConnect}
              disabled={loading}
              className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-primary-600 hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 disabled:opacity-50"
            >
              <LinkIcon className="h-4 w-4 mr-2" />
              {loading ? 'Connecting...' : 'Connect'}
            </button>
          ) : (
            <>
              <button
                onClick={onSync}
                disabled={loading}
                className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-success-600 hover:bg-success-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-success-500 disabled:opacity-50"
              >
                <ArrowPathIcon className="h-4 w-4 mr-2" />
                {loading ? 'Syncing...' : 'Sync Now'}
              </button>
              <button
                onClick={onDisconnect}
                disabled={loading}
                className="inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 disabled:opacity-50"
              >
                Disconnect
              </button>
            </>
          )}
        </div>
      </div>
    </div>
  );
};

const SyncStatus = ({ 
  title, 
  count, 
  lastSync, 
  error 
}: { 
  title: string; 
  count: number; 
  lastSync?: string; 
  error?: string; 
}) => (
  <div className="bg-gray-50 px-4 py-3 rounded-md">
    <div className="flex items-center justify-between">
      <div>
        <h4 className="text-sm font-medium text-gray-900">{title}</h4>
        <p className="text-sm text-gray-500">{count} items</p>
        {lastSync && (
          <p className="text-xs text-gray-400">
            Last synced: {format(new Date(lastSync), 'MMM dd, HH:mm')}
          </p>
        )}
        {error && (
          <p className="text-xs text-error-600">{error}</p>
        )}
      </div>
      <div className={`w-2 h-2 rounded-full ${error ? 'bg-error-500' : 'bg-success-500'}`} />
    </div>
  </div>
);

export default function Integrations() {
  const router = useRouter();
  const { integrationStatus, setIntegrationStatus } = useAppStore();
  const [loading, setLoading] = useState<Record<string, boolean>>({});
  const [syncData, setSyncData] = useState<any>({});

  useEffect(() => {
    loadIntegrationStatus();
    loadSyncData();
    
    // Check for connection success messages
    if (router.query.connected === 'etsy') {
      toast.success('Etsy connected successfully!');
      // Clean the URL
      router.replace('/integrations', undefined, { shallow: true });
    }
  }, [router.query]);

  const setLoadingState = (key: string, value: boolean) => {
    setLoading(prev => ({ ...prev, [key]: value }));
  };

  const loadIntegrationStatus = async () => {
    try {
      const [shopifyStatus, etsyStatus] = await Promise.all([
        apiService.getShopifyIntegrationStatus().catch(() => ({ connected: false })),
        apiService.getEtsyIntegrationStatus().catch(() => ({ connected: false })),
      ]);
      
      setIntegrationStatus('shopify', {
        platform: 'shopify',
        connected: shopifyStatus.connected || false,
        shop_name: shopifyStatus.shop_name,
        last_sync: shopifyStatus.last_sync,
        error_message: shopifyStatus.error_message,
      });
      
      setIntegrationStatus('etsy', {
        platform: 'etsy',
        connected: etsyStatus.connected || false,
        shop_name: etsyStatus.shop_name,
        last_sync: etsyStatus.last_sync,
        error_message: etsyStatus.error_message,
      });
    } catch (error) {
      console.error('Error loading integration status:', error);
      toast.error('Failed to load integration status');
    }
  };

  const loadSyncData = async () => {
    // Mock sync data - replace with actual API calls when available
    setSyncData({
      shopify: {
        products: { count: 156, lastSync: new Date().toISOString() },
        orders: { count: 89, lastSync: new Date().toISOString() },
        collections: { count: 12, lastSync: new Date().toISOString() },
      },
      etsy: {
        listings: { count: 234, lastSync: new Date().toISOString() },
        orders: { count: 67, lastSync: new Date().toISOString() },
      }
    });
  };

  const handleConnect = async (platform: 'shopify' | 'etsy') => {
    setLoadingState(`connect-${platform}`, true);
    
    try {
      if (platform === 'shopify') {
        const shopDomain = prompt('Enter your Shopify shop domain (e.g., my-store.myshopify.com):');
        if (!shopDomain) {
          setLoadingState(`connect-${platform}`, false);
          return;
        }
        
        const response = await apiService.initShopifyOAuth(shopDomain);
        const authUrl = response.oauth_url || response.auth_url;
        
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
      } else if (platform === 'etsy') {
        // Redirect to dedicated Etsy connection page
        window.location.href = '/connect-etsy';
      }
    } catch (error: any) {
      console.error(`Error connecting to ${platform}:`, error);
      toast.error(error.response?.data?.detail || `Failed to connect to ${platform}`);
    } finally {
      setLoadingState(`connect-${platform}`, false);
    }
  };

  const handleDisconnect = async (platform: 'shopify' | 'etsy') => {
    if (!confirm(`Are you sure you want to disconnect from ${platform}?`)) {
      return;
    }

    setLoadingState(`disconnect-${platform}`, true);
    
    try {
      // API call to disconnect
      if (platform === 'shopify') {
        await fetch('/api/v1/shopify/integration/status', { method: 'DELETE' });
      } else if (platform === 'etsy') {
        await apiService.disconnectEtsy();
      }
      
      setIntegrationStatus(platform, {
        platform,
        connected: false,
        shop_name: undefined,
        last_sync: undefined,
        error_message: undefined,
      });
      
      toast.success(`Successfully disconnected from ${platform}`);
    } catch (error: any) {
      console.error(`Error disconnecting from ${platform}:`, error);
      toast.error(`Failed to disconnect from ${platform}`);
    } finally {
      setLoadingState(`disconnect-${platform}`, false);
    }
  };

  const handleSync = async (platform: 'shopify' | 'etsy') => {
    setLoadingState(`sync-${platform}`, true);
    
    try {
      // API call to trigger sync - implement when available
      // await apiService.syncIntegration(platform);
      
      toast.success(`${platform} sync started successfully`);
      
      // Refresh integration status after sync
      setTimeout(() => {
        loadIntegrationStatus();
        loadSyncData();
      }, 2000);
      
    } catch (error: any) {
      console.error(`Error syncing ${platform}:`, error);
      toast.error(`Failed to sync ${platform}`);
    } finally {
      setLoadingState(`sync-${platform}`, false);
    }
  };

  return (
    <MainLayout>
      <div className="space-y-6">
        {/* Page Header */}
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Integrations</h1>
          <p className="mt-1 text-sm text-gray-500">
            Connect and manage your e-commerce platform integrations
          </p>
        </div>

        {/* Integration Cards */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <IntegrationCard
            title="Shopify"
            description="Connect to your Shopify store to sync products, orders, and collections"
            platform="shopify"
            status={integrationStatus.shopify}
            onConnect={() => handleConnect('shopify')}
            onDisconnect={() => handleDisconnect('shopify')}
            onSync={() => handleSync('shopify')}
            loading={loading['connect-shopify'] || loading['sync-shopify'] || loading['disconnect-shopify']}
          />

          <IntegrationCard
            title="Etsy"
            description="Connect to your Etsy shop to sync listings and orders"
            platform="etsy"
            status={integrationStatus.etsy}
            onConnect={() => handleConnect('etsy')}
            onDisconnect={() => handleDisconnect('etsy')}
            onSync={() => handleSync('etsy')}
            loading={loading['connect-etsy'] || loading['sync-etsy'] || loading['disconnect-etsy']}
          />
        </div>

        {/* Sync Status */}
        {(integrationStatus.shopify?.connected || integrationStatus.etsy?.connected) && (
          <div className="bg-white shadow rounded-lg">
            <div className="px-6 py-4 border-b border-gray-200">
              <h2 className="text-lg font-medium text-gray-900">Sync Status</h2>
              <p className="text-sm text-gray-500">Current synchronization status for your connected platforms</p>
            </div>
            <div className="p-6">
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {integrationStatus.shopify?.connected && (
                  <div className="space-y-4">
                    <h3 className="text-md font-medium text-gray-900">Shopify</h3>
                    <div className="space-y-3">
                      <SyncStatus
                        title="Products"
                        count={syncData.shopify?.products?.count || 0}
                        lastSync={syncData.shopify?.products?.lastSync}
                      />
                      <SyncStatus
                        title="Orders"
                        count={syncData.shopify?.orders?.count || 0}
                        lastSync={syncData.shopify?.orders?.lastSync}
                      />
                      <SyncStatus
                        title="Collections"
                        count={syncData.shopify?.collections?.count || 0}
                        lastSync={syncData.shopify?.collections?.lastSync}
                      />
                    </div>
                  </div>
                )}

                {integrationStatus.etsy?.connected && (
                  <div className="space-y-4">
                    <h3 className="text-md font-medium text-gray-900">Etsy</h3>
                    <div className="space-y-3">
                      <SyncStatus
                        title="Listings"
                        count={syncData.etsy?.listings?.count || 0}
                        lastSync={syncData.etsy?.listings?.lastSync}
                      />
                      <SyncStatus
                        title="Orders"
                        count={syncData.etsy?.orders?.count || 0}
                        lastSync={syncData.etsy?.orders?.lastSync}
                      />
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>
        )}

        {/* Integration Help */}
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-6">
          <div className="flex">
            <div className="flex-shrink-0">
              <ExclamationCircleIcon className="h-5 w-5 text-blue-400" aria-hidden="true" />
            </div>
            <div className="ml-3">
              <h3 className="text-sm font-medium text-blue-800">Integration Help</h3>
              <div className="mt-2 text-sm text-blue-700">
                <ul className="list-disc pl-5 space-y-1">
                  <li>
                    <strong>Shopify:</strong> You'll need to install our app in your Shopify admin panel. 
                    We'll redirect you to complete the authorization process.
                  </li>
                  <li>
                    <strong>Etsy:</strong> You'll be redirected to Etsy to authorize access to your shop data.
                    Make sure you're logged into the correct Etsy account.
                  </li>
                  <li>
                    Data synchronization happens automatically every 15 minutes, but you can trigger manual sync anytime.
                  </li>
                </ul>
              </div>
            </div>
          </div>
        </div>
      </div>
    </MainLayout>
  );
}