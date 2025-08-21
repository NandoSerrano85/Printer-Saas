import React, { useEffect, useState } from 'react';
import MainLayout from '@/components/Layout/MainLayout';
import apiService from '@/services/api';
import { Order, OrderItem } from '@/types';
import {
  EyeIcon,
  TruckIcon,
  ClipboardDocumentListIcon,
  PhotoIcon,
} from '@heroicons/react/24/outline';
import toast from 'react-hot-toast';
import { format } from 'date-fns';
import clsx from 'clsx';

const StatusBadge = ({ status }: { status: string }) => {
  const statusColors = {
    pending: 'bg-yellow-100 text-yellow-800',
    processing: 'bg-blue-100 text-blue-800',
    shipped: 'bg-purple-100 text-purple-800',
    delivered: 'bg-green-100 text-green-800',
    cancelled: 'bg-red-100 text-red-800',
  };

  return (
    <span
      className={clsx(
        'inline-flex px-2 py-1 text-xs font-semibold rounded-full',
        statusColors[status as keyof typeof statusColors] || 'bg-gray-100 text-gray-800'
      )}
    >
      {status}
    </span>
  );
};

const ProcessingStatusBadge = ({ status }: { status: string }) => {
  const statusColors = {
    pending: 'bg-gray-100 text-gray-800',
    processing: 'bg-blue-100 text-blue-800',
    ready: 'bg-green-100 text-green-800',
    printed: 'bg-purple-100 text-purple-800',
    shipped: 'bg-indigo-100 text-indigo-800',
  };

  return (
    <span
      className={clsx(
        'inline-flex px-2 py-1 text-xs font-semibold rounded-full',
        statusColors[status as keyof typeof statusColors] || 'bg-gray-100 text-gray-800'
      )}
    >
      {status}
    </span>
  );
};

const OrderPreviewModal = ({
  isOpen,
  onClose,
  orderId,
}: {
  isOpen: boolean;
  onClose: () => void;
  orderId: string | null;
}) => {
  const [previewData, setPreviewData] = useState<any>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (isOpen && orderId) {
      loadOrderPreview(orderId);
    }
  }, [isOpen, orderId]);

  const loadOrderPreview = async (id: string) => {
    setLoading(true);
    try {
      const response = await apiService.getOrderPreview(id);
      setPreviewData(response);
    } catch (error) {
      console.error('Error loading order preview:', error);
      toast.error('Failed to load order preview');
    } finally {
      setLoading(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
      <div className="relative top-20 mx-auto p-5 border w-4/5 max-w-4xl shadow-lg rounded-md bg-white">
        <div className="mt-3">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-medium text-gray-900">Order Preview</h3>
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
            <div className="flex items-center justify-center h-64">
              <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-primary-500"></div>
            </div>
          ) : previewData ? (
            <div className="space-y-6">
              {/* Order Info */}
              <div className="bg-gray-50 p-4 rounded-md">
                <h4 className="font-medium text-gray-900 mb-2">Order Information</h4>
                <div className="grid grid-cols-2 gap-4 text-sm">
                  <div>Order #: {previewData.order_number}</div>
                  <div>Status: <StatusBadge status={previewData.status} /></div>
                  <div>Customer: {previewData.customer_name}</div>
                  <div>Total: ${previewData.total_amount?.toFixed(2)}</div>
                </div>
              </div>

              {/* Order Items with Previews */}
              <div className="space-y-4">
                <h4 className="font-medium text-gray-900">Order Items & Previews</h4>
                {previewData.items?.map((item: any, index: number) => (
                  <div key={index} className="border rounded-lg p-4">
                    <div className="flex space-x-4">
                      <div className="flex-1">
                        <h5 className="font-medium text-gray-900">{item.product_name}</h5>
                        <p className="text-sm text-gray-500">Quantity: {item.quantity}</p>
                        <p className="text-sm text-gray-500">
                          Status: <ProcessingStatusBadge status={item.processing_status} />
                        </p>
                        
                        {item.upload_urls && item.upload_urls.length > 0 && (
                          <div className="mt-2">
                            <p className="text-sm font-medium text-gray-700">Uploaded Files:</p>
                            <div className="mt-1 space-y-1">
                              {item.upload_urls.map((url: string, urlIndex: number) => (
                                <a
                                  key={urlIndex}
                                  href={url}
                                  target="_blank"
                                  rel="noopener noreferrer"
                                  className="text-sm text-primary-600 hover:text-primary-800 block"
                                >
                                  File {urlIndex + 1}
                                </a>
                              ))}
                            </div>
                          </div>
                        )}
                      </div>

                      {item.preview_image_url && (
                        <div className="flex-shrink-0">
                          <img
                            src={item.preview_image_url}
                            alt={`Preview for ${item.product_name}`}
                            className="w-32 h-32 object-cover border rounded"
                          />
                        </div>
                      )}
                    </div>

                    {item.customization_data && (
                      <div className="mt-3 bg-gray-50 p-3 rounded">
                        <p className="text-sm font-medium text-gray-700 mb-1">Customization Details:</p>
                        <pre className="text-xs text-gray-600 whitespace-pre-wrap">
                          {JSON.stringify(item.customization_data, null, 2)}
                        </pre>
                      </div>
                    )}
                  </div>
                ))}
              </div>

              {/* Shipping Address */}
              {previewData.shipping_address && (
                <div className="bg-gray-50 p-4 rounded-md">
                  <h4 className="font-medium text-gray-900 mb-2">Shipping Address</h4>
                  <div className="text-sm text-gray-600">
                    <p>{previewData.shipping_address.first_name} {previewData.shipping_address.last_name}</p>
                    <p>{previewData.shipping_address.address1}</p>
                    {previewData.shipping_address.address2 && <p>{previewData.shipping_address.address2}</p>}
                    <p>
                      {previewData.shipping_address.city}, {previewData.shipping_address.province} {previewData.shipping_address.zip}
                    </p>
                    <p>{previewData.shipping_address.country}</p>
                  </div>
                </div>
              )}
            </div>
          ) : (
            <div className="text-center py-8">
              <p className="text-gray-500">No preview data available</p>
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

export default function Orders() {
  const [orders, setOrders] = useState<Order[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedOrderId, setSelectedOrderId] = useState<string | null>(null);
  const [isPreviewOpen, setIsPreviewOpen] = useState(false);
  const [filter, setFilter] = useState('all');
  const [searchQuery, setSearchQuery] = useState('');

  useEffect(() => {
    loadOrders();
  }, []);

  const loadOrders = async () => {
    try {
      const response = await apiService.getOrders().catch(() => ({ orders: [] }));
      setOrders(response.orders || response || []);
    } catch (error) {
      console.error('Error loading orders:', error);
      setOrders([]);
    } finally {
      setLoading(false);
    }
  };

  const handleUpdateOrderStatus = async (orderId: string, newStatus: string) => {
    try {
      await apiService.updateOrder(orderId, { status: newStatus });
      toast.success('Order status updated successfully');
      loadOrders();
    } catch (error: any) {
      console.error('Error updating order status:', error);
      toast.error(error.response?.data?.detail || 'Failed to update order status');
    }
  };

  const handlePreviewOrder = (orderId: string) => {
    setSelectedOrderId(orderId);
    setIsPreviewOpen(true);
  };

  const filteredOrders = orders.filter(order => {
    const matchesFilter = filter === 'all' || order.status === filter;
    const matchesSearch = 
      order.order_number.toLowerCase().includes(searchQuery.toLowerCase()) ||
      order.customer_name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      order.customer_email.toLowerCase().includes(searchQuery.toLowerCase());
    
    return matchesFilter && matchesSearch;
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
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Orders</h1>
          <p className="mt-1 text-sm text-gray-500">
            Manage and track your customer orders
          </p>
        </div>

        {/* Filters and Search */}
        <div className="flex flex-col sm:flex-row space-y-4 sm:space-y-0 sm:space-x-4">
          <div className="flex-1">
            <input
              type="text"
              placeholder="Search by order number, customer name, or email..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="block w-full border-gray-300 rounded-md shadow-sm focus:ring-primary-500 focus:border-primary-500 sm:text-sm"
            />
          </div>
          <select
            value={filter}
            onChange={(e) => setFilter(e.target.value)}
            className="block border-gray-300 rounded-md shadow-sm focus:ring-primary-500 focus:border-primary-500 sm:text-sm"
          >
            <option value="all">All Orders</option>
            <option value="pending">Pending</option>
            <option value="processing">Processing</option>
            <option value="shipped">Shipped</option>
            <option value="delivered">Delivered</option>
            <option value="cancelled">Cancelled</option>
          </select>
        </div>

        {/* Orders Table */}
        {filteredOrders.length === 0 ? (
          <div className="text-center py-12">
            <ClipboardDocumentListIcon className="mx-auto h-12 w-12 text-gray-400" />
            <h3 className="mt-2 text-sm font-medium text-gray-900">No orders found</h3>
            <p className="mt-1 text-sm text-gray-500">
              {orders.length === 0 
                ? "Orders from your connected platforms will appear here."
                : "Try adjusting your search or filter criteria."
              }
            </p>
          </div>
        ) : (
          <div className="bg-white shadow overflow-hidden sm:rounded-md">
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Order
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Customer
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Items
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
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Date
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Actions
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {filteredOrders.map((order) => (
                    <tr key={order.id} className="hover:bg-gray-50">
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="flex flex-col">
                          <div className="text-sm font-medium text-gray-900">
                            #{order.order_number}
                          </div>
                          {order.tracking_numbers.length > 0 && (
                            <div className="text-xs text-gray-500">
                              Tracking: {order.tracking_numbers[0]}
                            </div>
                          )}
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="flex flex-col">
                          <div className="text-sm font-medium text-gray-900">
                            {order.customer_name}
                          </div>
                          <div className="text-sm text-gray-500">
                            {order.customer_email}
                          </div>
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {order.items.length} item{order.items.length !== 1 ? 's' : ''}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                        ${order.total_amount.toFixed(2)} {order.currency}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <select
                          value={order.status}
                          onChange={(e) => handleUpdateOrderStatus(order.id, e.target.value)}
                          className="text-xs border-0 bg-transparent focus:ring-0 p-0 font-semibold rounded-full"
                        >
                          <option value="pending">Pending</option>
                          <option value="processing">Processing</option>
                          <option value="shipped">Shipped</option>
                          <option value="delivered">Delivered</option>
                          <option value="cancelled">Cancelled</option>
                        </select>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 capitalize">
                        {order.platform}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {format(new Date(order.created_at), 'MMM dd, yyyy')}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                        <div className="flex space-x-2">
                          <button
                            onClick={() => handlePreviewOrder(order.id)}
                            className="text-primary-600 hover:text-primary-900"
                            title="Preview Order"
                          >
                            <EyeIcon className="h-4 w-4" />
                          </button>
                          {order.items.some(item => item.preview_image_url) && (
                            <PhotoIcon className="h-4 w-4 text-green-500" title="Has Preview Images" />
                          )}
                          {order.tracking_numbers.length > 0 && (
                            <TruckIcon className="h-4 w-4 text-blue-500" title="Has Tracking" />
                          )}
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* Order Preview Modal */}
        <OrderPreviewModal
          isOpen={isPreviewOpen}
          onClose={() => {
            setIsPreviewOpen(false);
            setSelectedOrderId(null);
          }}
          orderId={selectedOrderId}
        />
      </div>
    </MainLayout>
  );
}