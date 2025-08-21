import React, { useEffect, useState } from 'react';
import MainLayout from '@/components/Layout/MainLayout';
import apiService from '@/services/api';
import { Tenant, TenantForm } from '@/types';
import {
  PlusIcon,
  PencilIcon,
  TrashIcon,
  BuildingOffice2Icon,
  UsersIcon,
  ChartBarIcon,
  CogIcon,
} from '@heroicons/react/24/outline';
import toast from 'react-hot-toast';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { format } from 'date-fns';
import clsx from 'clsx';

const tenantFormSchema = z.object({
  subdomain: z.string()
    .min(3, 'Subdomain must be at least 3 characters')
    .max(63, 'Subdomain cannot exceed 63 characters')
    .regex(/^[a-z0-9-]+$/, 'Subdomain can only contain lowercase letters, numbers, and hyphens'),
  company_name: z.string().min(1, 'Company name is required').max(255),
  subscription_tier: z.enum(['basic', 'professional', 'enterprise']),
  custom_domain: z.string().optional().or(z.literal('')),
});

type TenantFormData = z.infer<typeof tenantFormSchema>;

const TenantCard = ({
  tenant,
  onEdit,
  onDelete,
  onViewUsers,
  onViewUsage,
}: {
  tenant: Tenant;
  onEdit: (tenant: Tenant) => void;
  onDelete: (id: string) => void;
  onViewUsers: (tenant: Tenant) => void;
  onViewUsage: (tenant: Tenant) => void;
}) => {
  const tierColors = {
    basic: 'bg-gray-100 text-gray-800',
    professional: 'bg-blue-100 text-blue-800',
    enterprise: 'bg-purple-100 text-purple-800',
  };

  return (
    <div className="bg-white overflow-hidden shadow rounded-lg">
      <div className="p-6">
        <div className="flex items-center justify-between">
          <div className="flex items-center">
            <BuildingOffice2Icon className="h-8 w-8 text-gray-400" />
            <div className="ml-3">
              <h3 className="text-lg font-medium text-gray-900">{tenant.company_name}</h3>
              <p className="text-sm text-gray-500">
                {tenant.subdomain}.printersaas.com
                {tenant.custom_domain && (
                  <span className="ml-2 text-blue-600">({tenant.custom_domain})</span>
                )}
              </p>
            </div>
          </div>
          <div className="flex items-center space-x-2">
            <span
              className={clsx(
                'inline-flex px-2 py-1 text-xs font-semibold rounded-full',
                tierColors[tenant.subscription_tier as keyof typeof tierColors]
              )}
            >
              {tenant.subscription_tier}
            </span>
            <div className={`w-3 h-3 rounded-full ${tenant.is_active ? 'bg-green-500' : 'bg-red-500'}`} />
          </div>
        </div>

        <div className="mt-4">
          <dl className="grid grid-cols-3 gap-4">
            <div>
              <dt className="text-sm font-medium text-gray-500">Schema</dt>
              <dd className="mt-1 text-sm text-gray-900">{tenant.database_schema}</dd>
            </div>
            <div>
              <dt className="text-sm font-medium text-gray-500">Status</dt>
              <dd className="mt-1">
                <span className={`text-sm ${tenant.is_active ? 'text-green-600' : 'text-red-600'}`}>
                  {tenant.is_active ? 'Active' : 'Inactive'}
                </span>
              </dd>
            </div>
            <div>
              <dt className="text-sm font-medium text-gray-500">Created</dt>
              <dd className="mt-1 text-sm text-gray-900">
                {format(new Date(tenant.created_at), 'MMM dd, yyyy')}
              </dd>
            </div>
          </dl>
        </div>

        <div className="mt-6 flex space-x-3">
          <button
            onClick={() => onViewUsers(tenant)}
            className="flex-1 inline-flex items-center justify-center px-3 py-2 border border-gray-300 shadow-sm text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500"
          >
            <UsersIcon className="h-4 w-4 mr-1" />
            Users
          </button>
          
          <button
            onClick={() => onViewUsage(tenant)}
            className="flex-1 inline-flex items-center justify-center px-3 py-2 border border-gray-300 shadow-sm text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500"
          >
            <ChartBarIcon className="h-4 w-4 mr-1" />
            Usage
          </button>
          
          <button
            onClick={() => onEdit(tenant)}
            className="flex-1 inline-flex items-center justify-center px-3 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-primary-600 hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500"
          >
            <PencilIcon className="h-4 w-4 mr-1" />
            Edit
          </button>
          
          <button
            onClick={() => onDelete(tenant.id)}
            className="inline-flex items-center justify-center px-3 py-2 border border-gray-300 shadow-sm text-sm font-medium rounded-md text-red-700 bg-white hover:bg-red-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500"
          >
            <TrashIcon className="h-4 w-4" />
          </button>
        </div>
      </div>
    </div>
  );
};

const TenantModal = ({
  isOpen,
  onClose,
  tenant,
  onSave,
  loading,
}: {
  isOpen: boolean;
  onClose: () => void;
  tenant?: Tenant | null;
  onSave: (data: TenantFormData) => void;
  loading: boolean;
}) => {
  const isEdit = !!tenant;
  
  const {
    register,
    handleSubmit,
    reset,
    formState: { errors },
  } = useForm<TenantFormData>({
    resolver: zodResolver(tenantFormSchema),
    defaultValues: tenant ? {
      subdomain: tenant.subdomain,
      company_name: tenant.company_name,
      subscription_tier: tenant.subscription_tier as 'basic' | 'professional' | 'enterprise',
      custom_domain: tenant.custom_domain || '',
    } : {
      subdomain: '',
      company_name: '',
      subscription_tier: 'basic',
      custom_domain: '',
    },
  });

  useEffect(() => {
    if (tenant) {
      reset({
        subdomain: tenant.subdomain,
        company_name: tenant.company_name,
        subscription_tier: tenant.subscription_tier as 'basic' | 'professional' | 'enterprise',
        custom_domain: tenant.custom_domain || '',
      });
    } else {
      reset({
        subdomain: '',
        company_name: '',
        subscription_tier: 'basic',
        custom_domain: '',
      });
    }
  }, [tenant, reset]);

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
      <div className="relative top-20 mx-auto p-5 border w-96 shadow-lg rounded-md bg-white">
        <div className="mt-3">
          <h3 className="text-lg font-medium text-gray-900 mb-4">
            {isEdit ? 'Edit Tenant' : 'Create New Tenant'}
          </h3>
          
          <form onSubmit={handleSubmit(onSave)} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700">Subdomain</label>
              <div className="mt-1 flex rounded-md shadow-sm">
                <input
                  {...register('subdomain')}
                  disabled={isEdit}
                  className="flex-1 min-w-0 block w-full px-3 py-2 rounded-l-md border border-gray-300 focus:ring-primary-500 focus:border-primary-500 sm:text-sm disabled:bg-gray-100"
                  placeholder="company-name"
                />
                <span className="inline-flex items-center px-3 rounded-r-md border border-l-0 border-gray-300 bg-gray-50 text-gray-500 text-sm">
                  .printersaas.com
                </span>
              </div>
              {errors.subdomain && (
                <p className="mt-1 text-sm text-red-600">{errors.subdomain.message}</p>
              )}
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700">Company Name</label>
              <input
                {...register('company_name')}
                className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-primary-500 focus:border-primary-500 sm:text-sm"
                placeholder="Acme Corporation"
              />
              {errors.company_name && (
                <p className="mt-1 text-sm text-red-600">{errors.company_name.message}</p>
              )}
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700">Subscription Tier</label>
              <select
                {...register('subscription_tier')}
                className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-primary-500 focus:border-primary-500 sm:text-sm"
              >
                <option value="basic">Basic</option>
                <option value="professional">Professional</option>
                <option value="enterprise">Enterprise</option>
              </select>
              {errors.subscription_tier && (
                <p className="mt-1 text-sm text-red-600">{errors.subscription_tier.message}</p>
              )}
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700">Custom Domain (Optional)</label>
              <input
                {...register('custom_domain')}
                className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-primary-500 focus:border-primary-500 sm:text-sm"
                placeholder="printshop.example.com"
              />
              {errors.custom_domain && (
                <p className="mt-1 text-sm text-red-600">{errors.custom_domain.message}</p>
              )}
            </div>

            <div className="flex space-x-3 pt-4">
              <button
                type="button"
                onClick={onClose}
                className="flex-1 inline-flex justify-center py-2 px-4 border border-gray-300 shadow-sm text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={loading}
                className="flex-1 inline-flex justify-center py-2 px-4 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-primary-600 hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 disabled:opacity-50"
              >
                {loading ? 'Saving...' : (isEdit ? 'Update' : 'Create')}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
};

const TenantUsageModal = ({
  isOpen,
  onClose,
  tenant,
}: {
  isOpen: boolean;
  onClose: () => void;
  tenant: Tenant | null;
}) => {
  const [usageData, setUsageData] = useState<any>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (isOpen && tenant) {
      loadUsageData(tenant.id);
    }
  }, [isOpen, tenant]);

  const loadUsageData = async (tenantId: string) => {
    setLoading(true);
    try {
      const response = await apiService.getTenantUsage(tenantId);
      setUsageData(response);
    } catch (error) {
      console.error('Error loading usage data:', error);
      toast.error('Failed to load usage data');
    } finally {
      setLoading(false);
    }
  };

  if (!isOpen || !tenant) return null;

  return (
    <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
      <div className="relative top-20 mx-auto p-5 border w-2/3 max-w-2xl shadow-lg rounded-md bg-white">
        <div className="mt-3">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-medium text-gray-900">
              Usage Analytics - {tenant.company_name}
            </h3>
            <button
              onClick={onClose}
              className="text-gray-400 hover:text-gray-600"
            >
              <span className="sr-only">Close</span>
              <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>

          {loading ? (
            <div className="flex items-center justify-center h-32">
              <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-primary-500"></div>
            </div>
          ) : usageData ? (
            <div className="space-y-6">
              {/* Usage Stats */}
              <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
                <div className="bg-blue-50 p-4 rounded-lg">
                  <div className="text-2xl font-bold text-blue-900">
                    {usageData.total_orders || 0}
                  </div>
                  <div className="text-sm text-blue-700">Total Orders</div>
                </div>
                <div className="bg-green-50 p-4 rounded-lg">
                  <div className="text-2xl font-bold text-green-900">
                    {usageData.active_templates || 0}
                  </div>
                  <div className="text-sm text-green-700">Active Templates</div>
                </div>
                <div className="bg-purple-50 p-4 rounded-lg">
                  <div className="text-2xl font-bold text-purple-900">
                    {usageData.integrations_count || 0}
                  </div>
                  <div className="text-sm text-purple-700">Integrations</div>
                </div>
                <div className="bg-yellow-50 p-4 rounded-lg">
                  <div className="text-2xl font-bold text-yellow-900">
                    ${(usageData.total_revenue || 0).toFixed(2)}
                  </div>
                  <div className="text-sm text-yellow-700">Total Revenue</div>
                </div>
              </div>

              {/* Storage Usage */}
              <div className="bg-gray-50 p-4 rounded-lg">
                <h4 className="font-medium text-gray-900 mb-2">Storage Usage</h4>
                <div className="space-y-2">
                  <div className="flex justify-between text-sm">
                    <span>Used: {(usageData.storage_used_mb || 0).toFixed(2)} MB</span>
                    <span>Limit: {(usageData.storage_limit_mb || 1000).toFixed(2)} MB</span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div
                      className="bg-primary-600 h-2 rounded-full"
                      style={{
                        width: `${Math.min(
                          ((usageData.storage_used_mb || 0) / (usageData.storage_limit_mb || 1000)) * 100,
                          100
                        )}%`,
                      }}
                    ></div>
                  </div>
                </div>
              </div>

              {/* API Usage */}
              <div className="bg-gray-50 p-4 rounded-lg">
                <h4 className="font-medium text-gray-900 mb-2">API Usage (This Month)</h4>
                <div className="space-y-2">
                  <div className="flex justify-between text-sm">
                    <span>Requests: {(usageData.api_requests_count || 0).toLocaleString()}</span>
                    <span>Limit: {(usageData.api_requests_limit || 10000).toLocaleString()}</span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div
                      className="bg-green-600 h-2 rounded-full"
                      style={{
                        width: `${Math.min(
                          ((usageData.api_requests_count || 0) / (usageData.api_requests_limit || 10000)) * 100,
                          100
                        )}%`,
                      }}
                    ></div>
                  </div>
                </div>
              </div>
            </div>
          ) : (
            <div className="text-center py-8">
              <p className="text-gray-500">No usage data available</p>
            </div>
          )}

          <div className="mt-6 flex justify-end">
            <button
              onClick={onClose}
              className="inline-flex items-center px-4 py-2 border border-gray-300 shadow-sm text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500"
            >
              Close
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default function Tenants() {
  const [tenants, setTenants] = useState<Tenant[]>([]);
  const [loading, setLoading] = useState(true);
  const [modalLoading, setModalLoading] = useState(false);
  const [selectedTenant, setSelectedTenant] = useState<Tenant | null>(null);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [isUsageModalOpen, setIsUsageModalOpen] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [filterTier, setFilterTier] = useState('all');

  useEffect(() => {
    loadTenants();
  }, []);

  const loadTenants = async () => {
    try {
      const response = await apiService.getTenants();
      setTenants(response.tenants || response || []);
    } catch (error) {
      console.error('Error loading tenants:', error);
      toast.error('Failed to load tenants');
      setTenants([]);
    } finally {
      setLoading(false);
    }
  };

  const handleSaveTenant = async (data: TenantFormData) => {
    setModalLoading(true);
    
    try {
      const tenantData = {
        ...data,
        custom_domain: data.custom_domain || undefined,
        settings: {},
      };

      if (selectedTenant) {
        await apiService.updateTenant(selectedTenant.id, tenantData);
        toast.success('Tenant updated successfully');
      } else {
        await apiService.createTenant(tenantData);
        toast.success('Tenant created successfully');
      }
      
      setIsModalOpen(false);
      setSelectedTenant(null);
      loadTenants();
    } catch (error: any) {
      console.error('Error saving tenant:', error);
      toast.error(error.response?.data?.detail || 'Failed to save tenant');
    } finally {
      setModalLoading(false);
    }
  };

  const handleDeleteTenant = async (id: string) => {
    if (!confirm('Are you sure you want to delete this tenant? This action cannot be undone.')) {
      return;
    }

    try {
      await apiService.deleteTenant(id);
      toast.success('Tenant deleted successfully');
      loadTenants();
    } catch (error: any) {
      console.error('Error deleting tenant:', error);
      toast.error(error.response?.data?.detail || 'Failed to delete tenant');
    }
  };

  const handleViewUsers = (tenant: Tenant) => {
    toast.info(`Viewing users for ${tenant.company_name} - Feature coming soon`);
  };

  const handleViewUsage = (tenant: Tenant) => {
    setSelectedTenant(tenant);
    setIsUsageModalOpen(true);
  };

  const filteredTenants = tenants.filter(tenant => {
    const matchesSearch = 
      tenant.company_name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      tenant.subdomain.toLowerCase().includes(searchQuery.toLowerCase()) ||
      (tenant.custom_domain && tenant.custom_domain.toLowerCase().includes(searchQuery.toLowerCase()));
    
    const matchesTier = filterTier === 'all' || tenant.subscription_tier === filterTier;
    
    return matchesSearch && matchesTier;
  });

  if (loading) {
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
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Tenant Management</h1>
            <p className="mt-1 text-sm text-gray-500">
              Manage and monitor your SaaS tenants
            </p>
          </div>
          <button
            onClick={() => {
              setSelectedTenant(null);
              setIsModalOpen(true);
            }}
            className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-primary-600 hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500"
          >
            <PlusIcon className="h-4 w-4 mr-2" />
            New Tenant
          </button>
        </div>

        {/* Filters and Search */}
        <div className="flex flex-col sm:flex-row space-y-4 sm:space-y-0 sm:space-x-4">
          <div className="flex-1">
            <input
              type="text"
              placeholder="Search tenants by company name, subdomain, or domain..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="block w-full border-gray-300 rounded-md shadow-sm focus:ring-primary-500 focus:border-primary-500 sm:text-sm"
            />
          </div>
          <select
            value={filterTier}
            onChange={(e) => setFilterTier(e.target.value)}
            className="block border-gray-300 rounded-md shadow-sm focus:ring-primary-500 focus:border-primary-500 sm:text-sm"
          >
            <option value="all">All Tiers</option>
            <option value="basic">Basic</option>
            <option value="professional">Professional</option>
            <option value="enterprise">Enterprise</option>
          </select>
        </div>

        {/* Tenants Grid */}
        {filteredTenants.length === 0 ? (
          <div className="text-center py-12">
            <BuildingOffice2Icon className="mx-auto h-12 w-12 text-gray-400" />
            <h3 className="mt-2 text-sm font-medium text-gray-900">No tenants found</h3>
            <p className="mt-1 text-sm text-gray-500">
              {tenants.length === 0 
                ? "Get started by creating your first tenant."
                : "Try adjusting your search or filter criteria."
              }
            </p>
            {tenants.length === 0 && (
              <div className="mt-6">
                <button
                  onClick={() => {
                    setSelectedTenant(null);
                    setIsModalOpen(true);
                  }}
                  className="inline-flex items-center px-4 py-2 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-primary-600 hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500"
                >
                  <PlusIcon className="h-4 w-4 mr-2" />
                  Create Tenant
                </button>
              </div>
            )}
          </div>
        ) : (
          <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-6">
            {filteredTenants.map((tenant) => (
              <TenantCard
                key={tenant.id}
                tenant={tenant}
                onEdit={(tenant) => {
                  setSelectedTenant(tenant);
                  setIsModalOpen(true);
                }}
                onDelete={handleDeleteTenant}
                onViewUsers={handleViewUsers}
                onViewUsage={handleViewUsage}
              />
            ))}
          </div>
        )}

        {/* Tenant Modal */}
        <TenantModal
          isOpen={isModalOpen}
          onClose={() => {
            setIsModalOpen(false);
            setSelectedTenant(null);
          }}
          tenant={selectedTenant}
          onSave={handleSaveTenant}
          loading={modalLoading}
        />

        {/* Usage Modal */}
        <TenantUsageModal
          isOpen={isUsageModalOpen}
          onClose={() => {
            setIsUsageModalOpen(false);
            setSelectedTenant(null);
          }}
          tenant={selectedTenant}
        />
      </div>
    </MainLayout>
  );
}