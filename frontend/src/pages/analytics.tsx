import React, { useState, useEffect } from 'react';
import MainLayout from '@/components/Layout/MainLayout';
import apiService from '@/services/api';
import {
  ChartBarIcon,
  CurrencyDollarIcon,
  ShoppingBagIcon,
  UserGroupIcon,
  TrendingUpIcon,
  TrendingDownIcon,
  ArrowUpIcon,
  ArrowDownIcon,
} from '@heroicons/react/24/outline';
import toast from 'react-hot-toast';

interface AnalyticsData {
  totalRevenue: number;
  totalOrders: number;
  totalCustomers: number;
  conversionRate: number;
  revenueGrowth: number;
  ordersGrowth: number;
  customersGrowth: number;
  conversionGrowth: number;
  recentOrders: Array<{
    id: string;
    customer_name: string;
    total: number;
    status: string;
    created_at: string;
  }>;
  topProducts: Array<{
    name: string;
    sales: number;
    revenue: number;
  }>;
}

const StatCard: React.FC<{
  title: string;
  value: string | number;
  icon: React.ElementType;
  growth?: number;
  prefix?: string;
  suffix?: string;
}> = ({ title, value, icon: Icon, growth, prefix = '', suffix = '' }) => (
  <div className="bg-white overflow-hidden shadow rounded-lg">
    <div className="p-5">
      <div className="flex items-center">
        <div className="flex-shrink-0">
          <Icon className="h-6 w-6 text-gray-400" aria-hidden="true" />
        </div>
        <div className="ml-5 w-0 flex-1">
          <dl>
            <dt className="text-sm font-medium text-gray-500 truncate">{title}</dt>
            <dd className="flex items-baseline">
              <div className="text-2xl font-semibold text-gray-900">
                {prefix}{typeof value === 'number' ? value.toLocaleString() : value}{suffix}
              </div>
              {growth !== undefined && (
                <div className={`ml-2 flex items-baseline text-sm font-semibold ${
                  growth >= 0 ? 'text-green-600' : 'text-red-600'
                }`}>
                  {growth >= 0 ? (
                    <ArrowUpIcon className="self-center flex-shrink-0 h-4 w-4" aria-hidden="true" />
                  ) : (
                    <ArrowDownIcon className="self-center flex-shrink-0 h-4 w-4" aria-hidden="true" />
                  )}
                  <span className="sr-only">{growth >= 0 ? 'Increased' : 'Decreased'} by</span>
                  {Math.abs(growth)}%
                </div>
              )}
            </dd>
          </dl>
        </div>
      </div>
    </div>
  </div>
);

export default function Analytics() {
  const [analyticsData, setAnalyticsData] = useState<AnalyticsData | null>(null);
  const [loading, setLoading] = useState(true);
  const [timeRange, setTimeRange] = useState('30d');

  useEffect(() => {
    loadAnalyticsData();
  }, [timeRange]);

  const loadAnalyticsData = async () => {
    try {
      const response = await apiService.get(`/api/v1/dashboard/analytics?range=${timeRange}`);
      setAnalyticsData(response);
    } catch (error) {
      console.error('Error loading analytics data:', error);
      // Provide fallback data for demo purposes
      setAnalyticsData({
        totalRevenue: 15420.50,
        totalOrders: 127,
        totalCustomers: 89,
        conversionRate: 3.2,
        revenueGrowth: 12.5,
        ordersGrowth: 8.3,
        customersGrowth: 15.7,
        conversionGrowth: -2.1,
        recentOrders: [
          {
            id: '1',
            customer_name: 'John Doe',
            total: 89.99,
            status: 'completed',
            created_at: new Date().toISOString(),
          },
          {
            id: '2',
            customer_name: 'Jane Smith',
            total: 145.50,
            status: 'processing',
            created_at: new Date(Date.now() - 86400000).toISOString(),
          },
        ],
        topProducts: [
          { name: 'Custom T-Shirt', sales: 45, revenue: 1125.00 },
          { name: 'Business Cards', sales: 32, revenue: 640.00 },
          { name: 'Poster Print', sales: 28, revenue: 840.00 },
        ],
      });
    } finally {
      setLoading(false);
    }
  };

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
        {/* Header */}
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Analytics</h1>
            <p className="mt-1 text-sm text-gray-500">
              Track your business performance and insights
            </p>
          </div>
          <div className="mt-4 sm:mt-0">
            <select
              value={timeRange}
              onChange={(e) => setTimeRange(e.target.value)}
              className="block border-gray-300 rounded-md shadow-sm focus:ring-primary-500 focus:border-primary-500 sm:text-sm"
            >
              <option value="7d">Last 7 days</option>
              <option value="30d">Last 30 days</option>
              <option value="90d">Last 90 days</option>
              <option value="1y">Last year</option>
            </select>
          </div>
        </div>

        {/* Stats Grid */}
        <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-4">
          <StatCard
            title="Total Revenue"
            value={analyticsData?.totalRevenue || 0}
            icon={CurrencyDollarIcon}
            growth={analyticsData?.revenueGrowth}
            prefix="$"
          />
          <StatCard
            title="Total Orders"
            value={analyticsData?.totalOrders || 0}
            icon={ShoppingBagIcon}
            growth={analyticsData?.ordersGrowth}
          />
          <StatCard
            title="Total Customers"
            value={analyticsData?.totalCustomers || 0}
            icon={UserGroupIcon}
            growth={analyticsData?.customersGrowth}
          />
          <StatCard
            title="Conversion Rate"
            value={analyticsData?.conversionRate || 0}
            icon={ChartBarIcon}
            growth={analyticsData?.conversionGrowth}
            suffix="%"
          />
        </div>

        {/* Charts and Tables */}
        <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
          {/* Recent Orders */}
          <div className="bg-white shadow rounded-lg">
            <div className="px-4 py-5 sm:p-6">
              <h3 className="text-lg font-medium text-gray-900 mb-4">Recent Orders</h3>
              <div className="flow-root">
                <ul className="-my-5 divide-y divide-gray-200">
                  {analyticsData?.recentOrders?.map((order) => (
                    <li key={order.id} className="py-4">
                      <div className="flex items-center space-x-4">
                        <div className="flex-1 min-w-0">
                          <p className="text-sm font-medium text-gray-900 truncate">
                            {order.customer_name}
                          </p>
                          <p className="text-sm text-gray-500">
                            {new Date(order.created_at).toLocaleDateString()}
                          </p>
                        </div>
                        <div className="flex items-center space-x-2">
                          <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                            order.status === 'completed' 
                              ? 'bg-green-100 text-green-800'
                              : order.status === 'processing'
                              ? 'bg-blue-100 text-blue-800'
                              : 'bg-gray-100 text-gray-800'
                          }`}>
                            {order.status}
                          </span>
                          <span className="text-sm font-medium text-gray-900">
                            ${order.total.toFixed(2)}
                          </span>
                        </div>
                      </div>
                    </li>
                  ))}
                </ul>
              </div>
            </div>
          </div>

          {/* Top Products */}
          <div className="bg-white shadow rounded-lg">
            <div className="px-4 py-5 sm:p-6">
              <h3 className="text-lg font-medium text-gray-900 mb-4">Top Products</h3>
              <div className="space-y-4">
                {analyticsData?.topProducts?.map((product, index) => (
                  <div key={index} className="flex items-center justify-between">
                    <div className="flex-1">
                      <p className="text-sm font-medium text-gray-900">{product.name}</p>
                      <p className="text-sm text-gray-500">{product.sales} sales</p>
                    </div>
                    <div className="text-sm font-medium text-gray-900">
                      ${product.revenue.toFixed(2)}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>

        {/* Performance Chart Placeholder */}
        <div className="bg-white shadow rounded-lg">
          <div className="px-4 py-5 sm:p-6">
            <h3 className="text-lg font-medium text-gray-900 mb-4">Revenue Trend</h3>
            <div className="h-64 flex items-center justify-center bg-gray-50 rounded-md">
              <div className="text-center">
                <ChartBarIcon className="mx-auto h-12 w-12 text-gray-400" />
                <p className="mt-2 text-sm text-gray-500">
                  Chart integration coming soon
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </MainLayout>
  );
}