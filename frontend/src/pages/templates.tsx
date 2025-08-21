import React, { useEffect, useState } from 'react';
import MainLayout from '@/components/Layout/MainLayout';
import apiService from '@/services/api';
import { Template, IntegrationStatus } from '@/types';
import { 
  getCategoriesForPlatform, 
  getAvailablePlatforms, 
  getDefaultFieldValues,
  PlatformCategory,
  PlatformFieldDefinition 
} from '@/types/platforms';
import {
  PlusIcon,
  PencilIcon,
  TrashIcon,
  EyeIcon,
  DocumentDuplicateIcon,
  LinkIcon,
  CheckCircleIcon,
  XCircleIcon,
  MagnifyingGlassIcon,
  FunnelIcon,
} from '@heroicons/react/24/outline';
import toast from 'react-hot-toast';
import { useForm } from 'react-hook-form';

interface ExtendedTemplate extends Template {
  platform?: 'shopify' | 'etsy';
  platform_fields?: Record<string, any>;
}

interface DynamicFieldProps {
  field: PlatformFieldDefinition;
  value: any;
  onChange: (value: any) => void;
  error?: string;
}

const DynamicField: React.FC<DynamicFieldProps> = ({ field, value, onChange, error }) => {
  const baseClasses = "mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-primary-500 focus:border-primary-500 sm:text-sm";
  
  const renderField = () => {
    switch (field.type) {
      case 'text':
        return (
          <input
            type="text"
            value={value || ''}
            onChange={(e) => onChange(e.target.value)}
            placeholder={field.placeholder}
            required={field.required}
            minLength={field.validation?.minLength}
            maxLength={field.validation?.maxLength}
            pattern={field.validation?.pattern}
            className={baseClasses}
          />
        );
      
      case 'textarea':
        return (
          <textarea
            value={value || ''}
            onChange={(e) => onChange(e.target.value)}
            placeholder={field.placeholder}
            required={field.required}
            minLength={field.validation?.minLength}
            maxLength={field.validation?.maxLength}
            rows={4}
            className={baseClasses}
          />
        );
      
      case 'number':
        return (
          <input
            type="number"
            value={value || ''}
            onChange={(e) => onChange(parseFloat(e.target.value))}
            placeholder={field.placeholder}
            required={field.required}
            min={field.validation?.min}
            max={field.validation?.max}
            className={baseClasses}
          />
        );
      
      case 'price':
        return (
          <div className="relative">
            <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
              <span className="text-gray-500 sm:text-sm">$</span>
            </div>
            <input
              type="number"
              step="0.01"
              value={value || ''}
              onChange={(e) => onChange(parseFloat(e.target.value))}
              placeholder={field.placeholder}
              required={field.required}
              min={field.validation?.min}
              max={field.validation?.max}
              className={`${baseClasses} pl-7`}
            />
          </div>
        );
      
      case 'select':
        return (
          <select
            value={value || ''}
            onChange={(e) => onChange(e.target.value)}
            required={field.required}
            className={baseClasses}
          >
            <option value="">Select {field.label}</option>
            {field.options?.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
        );
      
      case 'multiselect':
        return (
          <select
            multiple
            value={value || []}
            onChange={(e) => {
              const values = Array.from(e.target.selectedOptions, option => option.value);
              onChange(values);
            }}
            required={field.required}
            className={`${baseClasses} h-32`}
          >
            {field.options?.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
        );
      
      case 'boolean':
        return (
          <div className="flex items-center mt-1">
            <input
              type="checkbox"
              checked={value || false}
              onChange={(e) => onChange(e.target.checked)}
              className="h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300 rounded"
            />
            <label className="ml-2 block text-sm text-gray-900">
              {field.label}
            </label>
          </div>
        );
      
      case 'image':
        return (
          <div className="mt-1">
            <input
              type="file"
              accept="image/*"
              onChange={(e) => {
                const file = e.target.files?.[0];
                if (file) {
                  // Handle file upload here
                  onChange(file);
                }
              }}
              className="block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-primary-50 file:text-primary-700 hover:file:bg-primary-100"
            />
          </div>
        );
      
      default:
        return (
          <input
            type="text"
            value={value || ''}
            onChange={(e) => onChange(e.target.value)}
            className={baseClasses}
          />
        );
    }
  };

  return (
    <div>
      <label className="block text-sm font-medium text-gray-700">
        {field.label}
        {field.required && <span className="text-red-500 ml-1">*</span>}
      </label>
      {renderField()}
      {field.helpText && (
        <p className="mt-1 text-xs text-gray-500">{field.helpText}</p>
      )}
      {error && (
        <p className="mt-1 text-sm text-red-600">{error}</p>
      )}
    </div>
  );
};

const TemplateCard: React.FC<{
  template: ExtendedTemplate;
  onEdit: (template: ExtendedTemplate) => void;
  onDelete: (id: string) => void;
  onDuplicate: (template: ExtendedTemplate) => void;
  onPreview: (template: ExtendedTemplate) => void;
}> = ({ template, onEdit, onDelete, onDuplicate, onPreview }) => (
  <div className="bg-white overflow-hidden shadow rounded-lg hover:shadow-md transition-shadow">
    <div className="aspect-w-16 aspect-h-9 bg-gray-200">
      {template.thumbnail_url ? (
        <img
          src={template.thumbnail_url}
          alt={template.name}
          className="w-full h-48 object-cover"
        />
      ) : (
        <div className="w-full h-48 flex items-center justify-center bg-gray-100">
          <DocumentDuplicateIcon className="h-12 w-12 text-gray-400" />
        </div>
      )}
    </div>
    
    <div className="p-4">
      <div className="flex items-center justify-between mb-2">
        <h3 className="text-lg font-medium text-gray-900 truncate">{template.name}</h3>
        <div className="flex items-center space-x-1">
          {template.platform && (
            <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
              template.platform === 'shopify' 
                ? 'bg-green-100 text-green-800' 
                : 'bg-orange-100 text-orange-800'
            }`}>
              {template.platform === 'shopify' ? 'Shopify' : 'Etsy'}
            </span>
          )}
          <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
            template.is_public ? 'bg-blue-100 text-blue-800' : 'bg-gray-100 text-gray-800'
          }`}>
            {template.is_public ? 'Public' : 'Private'}
          </span>
        </div>
      </div>
      
      <p className="text-sm text-gray-600 mb-2 line-clamp-2">{template.description}</p>
      
      <div className="flex items-center justify-between text-xs text-gray-500 mb-4">
        <span>{template.category}</span>
        <span>Used {template.usage_count} times</span>
      </div>
      
      <div className="flex space-x-2">
        <button
          onClick={() => onPreview(template)}
          className="flex-1 inline-flex items-center justify-center px-3 py-2 border border-gray-300 shadow-sm text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500"
        >
          <EyeIcon className="h-4 w-4 mr-1" />
          Preview
        </button>
        
        <button
          onClick={() => onEdit(template)}
          className="flex-1 inline-flex items-center justify-center px-3 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-primary-600 hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500"
        >
          <PencilIcon className="h-4 w-4 mr-1" />
          Edit
        </button>
        
        <button
          onClick={() => onDuplicate(template)}
          className="inline-flex items-center justify-center px-3 py-2 border border-gray-300 shadow-sm text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500"
        >
          <DocumentDuplicateIcon className="h-4 w-4" />
        </button>
        
        <button
          onClick={() => onDelete(template.id)}
          className="inline-flex items-center justify-center px-3 py-2 border border-gray-300 shadow-sm text-sm font-medium rounded-md text-red-700 bg-white hover:bg-red-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500"
        >
          <TrashIcon className="h-4 w-4" />
        </button>
      </div>
    </div>
  </div>
);

const TemplateModal: React.FC<{
  isOpen: boolean;
  onClose: () => void;
  template?: ExtendedTemplate | null;
  onSave: (data: any) => void;
  loading: boolean;
  integrations: Record<string, IntegrationStatus>;
}> = ({ isOpen, onClose, template, onSave, loading, integrations }) => {
  const [selectedPlatform, setSelectedPlatform] = useState<'shopify' | 'etsy'>('shopify');
  const [selectedCategory, setSelectedCategory] = useState<string>('');
  const [platformFields, setPlatformFields] = useState<Record<string, any>>({});
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    is_public: false,
  });

  const availablePlatforms = getAvailablePlatforms().filter(platform => 
    integrations[platform.value]?.connected
  );

  const categories = getCategoriesForPlatform(selectedPlatform);
  const selectedCategoryData = categories.find(cat => cat.id === selectedCategory);

  useEffect(() => {
    if (template) {
      setFormData({
        name: template.name,
        description: template.description,
        is_public: template.is_public,
      });
      setSelectedPlatform(template.platform || 'shopify');
      setSelectedCategory(template.category);
      setPlatformFields(template.platform_fields || {});
    } else {
      setFormData({
        name: '',
        description: '',
        is_public: false,
      });
      setSelectedPlatform(availablePlatforms[0]?.value || 'shopify');
      setSelectedCategory('');
      setPlatformFields({});
    }
  }, [template, availablePlatforms]);

  useEffect(() => {
    if (selectedCategoryData) {
      const defaults = getDefaultFieldValues(selectedCategoryData.fields);
      setPlatformFields(defaults);
    }
  }, [selectedCategoryData]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSave({
      ...formData,
      platform: selectedPlatform,
      category: selectedCategory,
      platform_fields: platformFields,
    });
  };

  if (!isOpen) return null;

  if (availablePlatforms.length === 0) {
    return (
      <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
        <div className="relative top-20 mx-auto p-5 border w-96 shadow-lg rounded-md bg-white">
          <div className="mt-3 text-center">
            <XCircleIcon className="mx-auto h-12 w-12 text-red-500 mb-4" />
            <h3 className="text-lg font-medium text-gray-900 mb-2">No Integrations Connected</h3>
            <p className="text-sm text-gray-600 mb-4">
              You need to connect at least one integration (Shopify or Etsy) before creating templates.
            </p>
            <div className="flex space-x-3">
              <button
                onClick={onClose}
                className="flex-1 px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50"
              >
                Cancel
              </button>
              <a
                href="/integrations"
                className="flex-1 px-4 py-2 text-sm font-medium text-white bg-primary-600 border border-transparent rounded-md hover:bg-primary-700"
              >
                Setup Integrations
              </a>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
      <div className="relative top-10 mx-auto p-5 border max-w-4xl shadow-lg rounded-md bg-white">
        <div className="mt-3">
          <h3 className="text-lg font-medium text-gray-900 mb-4">
            {template ? 'Edit Template' : 'Create New Template'}
          </h3>
          
          <form onSubmit={handleSubmit} className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {/* Basic Information */}
              <div className="space-y-4">
                <h4 className="text-md font-medium text-gray-900">Basic Information</h4>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700">
                    Template Name <span className="text-red-500">*</span>
                  </label>
                  <input
                    type="text"
                    value={formData.name}
                    onChange={(e) => setFormData(prev => ({ ...prev, name: e.target.value }))}
                    className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-primary-500 focus:border-primary-500 sm:text-sm"
                    placeholder="Template name"
                    required
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700">
                    Description <span className="text-red-500">*</span>
                  </label>
                  <textarea
                    value={formData.description}
                    onChange={(e) => setFormData(prev => ({ ...prev, description: e.target.value }))}
                    rows={3}
                    className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-primary-500 focus:border-primary-500 sm:text-sm"
                    placeholder="Template description"
                    required
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700">
                    Platform <span className="text-red-500">*</span>
                  </label>
                  <select
                    value={selectedPlatform}
                    onChange={(e) => {
                      const platform = e.target.value as 'shopify' | 'etsy';
                      setSelectedPlatform(platform);
                      setSelectedCategory('');
                      setPlatformFields({});
                    }}
                    className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-primary-500 focus:border-primary-500 sm:text-sm"
                    required
                  >
                    {availablePlatforms.map(platform => (
                      <option key={platform.value} value={platform.value}>
                        {platform.label}
                        {integrations[platform.value]?.connected ? ' (Connected)' : ' (Not Connected)'}
                      </option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700">
                    Category <span className="text-red-500">*</span>
                  </label>
                  <select
                    value={selectedCategory}
                    onChange={(e) => setSelectedCategory(e.target.value)}
                    className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-primary-500 focus:border-primary-500 sm:text-sm"
                    required
                  >
                    <option value="">Select category</option>
                    {categories.map(category => (
                      <option key={category.id} value={category.id}>
                        {category.name}
                      </option>
                    ))}
                  </select>
                </div>

                <div className="flex items-center">
                  <input
                    type="checkbox"
                    checked={formData.is_public}
                    onChange={(e) => setFormData(prev => ({ ...prev, is_public: e.target.checked }))}
                    className="h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300 rounded"
                  />
                  <label className="ml-2 block text-sm text-gray-900">
                    Make this template public
                  </label>
                </div>
              </div>

              {/* Platform-Specific Fields */}
              <div className="space-y-4">
                <h4 className="text-md font-medium text-gray-900">
                  {selectedPlatform === 'shopify' ? 'Shopify' : 'Etsy'} Product Fields
                </h4>
                
                {selectedCategoryData ? (
                  <div className="space-y-4 max-h-96 overflow-y-auto">
                    {selectedCategoryData.fields.map(field => (
                      <DynamicField
                        key={field.name}
                        field={field}
                        value={platformFields[field.name]}
                        onChange={(value) => setPlatformFields(prev => ({ ...prev, [field.name]: value }))}
                      />
                    ))}
                  </div>
                ) : (
                  <p className="text-sm text-gray-500">
                    Select a category to see platform-specific fields
                  </p>
                )}
              </div>
            </div>

            <div className="flex space-x-3 pt-4 border-t">
              <button
                type="button"
                onClick={onClose}
                className="flex-1 inline-flex justify-center py-2 px-4 border border-gray-300 shadow-sm text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={loading || !selectedCategory}
                className="flex-1 inline-flex justify-center py-2 px-4 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-primary-600 hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 disabled:opacity-50"
              >
                {loading ? 'Saving...' : (template ? 'Update Template' : 'Create Template')}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
};

export default function Templates() {
  const [templates, setTemplates] = useState<ExtendedTemplate[]>([]);
  const [integrations, setIntegrations] = useState<Record<string, IntegrationStatus>>({});
  const [loading, setLoading] = useState(true);
  const [modalLoading, setModalLoading] = useState(false);
  const [selectedTemplate, setSelectedTemplate] = useState<ExtendedTemplate | null>(null);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [filter, setFilter] = useState('all');
  const [platformFilter, setPlatformFilter] = useState('all');
  const [searchQuery, setSearchQuery] = useState('');

  useEffect(() => {
    loadTemplates();
    loadIntegrations();
  }, []);

  const loadTemplates = async () => {
    try {
      const response = await apiService.get('/api/v1/templates').catch(() => ({ templates: [] }));
      setTemplates(response.templates || []);
    } catch (error) {
      console.error('Error loading templates:', error);
      // Set empty array on error instead of showing error
      setTemplates([]);
    } finally {
      setLoading(false);
    }
  };

  const loadIntegrations = async () => {
    try {
      const [shopifyStatus, etsyStatus] = await Promise.all([
        apiService.get('/api/v1/shopify/integration/status').catch(() => ({ connected: false })),
        apiService.get('/api/v1/etsy/integration/status').catch(() => ({ connected: false })),
      ]);
      
      setIntegrations({
        shopify: shopifyStatus,
        etsy: etsyStatus,
      });
    } catch (error) {
      console.error('Error loading integrations:', error);
    }
  };

  const handleCreateTemplate = () => {
    setSelectedTemplate(null);
    setIsModalOpen(true);
  };

  const handleEditTemplate = (template: ExtendedTemplate) => {
    setSelectedTemplate(template);
    setIsModalOpen(true);
  };

  const handleSaveTemplate = async (data: any) => {
    setModalLoading(true);
    try {
      let response;
      if (selectedTemplate) {
        response = await apiService.put(`/api/v1/templates/${selectedTemplate.id}`, data);
        toast.success('Template updated successfully');
      } else {
        response = await apiService.post('/api/v1/templates', data);
        toast.success('Template created successfully');
      }
      
      setIsModalOpen(false);
      loadTemplates();
    } catch (error: any) {
      toast.error(error.response?.data?.message || 'Failed to save template');
    } finally {
      setModalLoading(false);
    }
  };

  const handleDeleteTemplate = async (id: string) => {
    if (!confirm('Are you sure you want to delete this template?')) return;
    
    try {
      await apiService.delete(`/api/v1/templates/${id}`);
      toast.success('Template deleted successfully');
      loadTemplates();
    } catch (error: any) {
      toast.error(error.response?.data?.message || 'Failed to delete template');
    }
  };

  const handleDuplicateTemplate = async (template: ExtendedTemplate) => {
    try {
      const duplicateData = {
        ...template,
        name: `${template.name} (Copy)`,
        id: undefined,
      };
      delete duplicateData.id;
      
      await apiService.post('/api/v1/templates', duplicateData);
      toast.success('Template duplicated successfully');
      loadTemplates();
    } catch (error: any) {
      toast.error(error.response?.data?.message || 'Failed to duplicate template');
    }
  };

  const handlePreviewTemplate = (template: ExtendedTemplate) => {
    // Open preview modal or navigate to preview page
    console.log('Preview template:', template);
    toast.info('Template preview feature coming soon');
  };

  const filteredTemplates = templates.filter(template => {
    const matchesSearch = template.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
                         template.description.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesFilter = filter === 'all' || 
                         (filter === 'public' && template.is_public) ||
                         (filter === 'private' && !template.is_public);
    const matchesPlatform = platformFilter === 'all' || template.platform === platformFilter;
    
    return matchesSearch && matchesFilter && matchesPlatform;
  });

  const connectedPlatforms = Object.entries(integrations)
    .filter(([_, status]) => status.connected)
    .map(([platform]) => platform);

  return (
    <MainLayout>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Templates</h1>
            <p className="mt-1 text-sm text-gray-500">
              Create and manage product templates for your integrations
            </p>
          </div>
          <div className="mt-4 sm:mt-0">
            <button
              onClick={handleCreateTemplate}
              className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-primary-600 hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500"
            >
              <PlusIcon className="h-5 w-5 mr-2" />
              Create Template
            </button>
          </div>
        </div>

        {/* Integration Status */}
        <div className="bg-white shadow rounded-lg p-4">
          <h3 className="text-sm font-medium text-gray-900 mb-3">Connected Integrations</h3>
          <div className="flex items-center space-x-4">
            {getAvailablePlatforms().map(platform => {
              const isConnected = integrations[platform.value]?.connected;
              return (
                <div key={platform.value} className="flex items-center">
                  {isConnected ? (
                    <CheckCircleIcon className="h-5 w-5 text-green-500 mr-2" />
                  ) : (
                    <XCircleIcon className="h-5 w-5 text-red-500 mr-2" />
                  )}
                  <span className={`text-sm ${isConnected ? 'text-green-700' : 'text-red-700'}`}>
                    {platform.label}
                  </span>
                </div>
              );
            })}
            {connectedPlatforms.length === 0 && (
              <a
                href="/integrations"
                className="inline-flex items-center text-sm text-primary-600 hover:text-primary-700"
              >
                <LinkIcon className="h-4 w-4 mr-1" />
                Setup Integrations
              </a>
            )}
          </div>
        </div>

        {/* Filters */}
        <div className="bg-white shadow rounded-lg p-4">
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between space-y-3 sm:space-y-0">
            <div className="flex items-center space-x-4">
              <div className="relative">
                <MagnifyingGlassIcon className="h-5 w-5 absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" />
                <input
                  type="text"
                  placeholder="Search templates..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="pl-10 pr-4 py-2 border border-gray-300 rounded-md focus:ring-primary-500 focus:border-primary-500 sm:text-sm"
                />
              </div>
              
              <select
                value={filter}
                onChange={(e) => setFilter(e.target.value)}
                className="border border-gray-300 rounded-md py-2 px-3 focus:ring-primary-500 focus:border-primary-500 sm:text-sm"
              >
                <option value="all">All Templates</option>
                <option value="public">Public</option>
                <option value="private">Private</option>
              </select>

              <select
                value={platformFilter}
                onChange={(e) => setPlatformFilter(e.target.value)}
                className="border border-gray-300 rounded-md py-2 px-3 focus:ring-primary-500 focus:border-primary-500 sm:text-sm"
              >
                <option value="all">All Platforms</option>
                <option value="shopify">Shopify</option>
                <option value="etsy">Etsy</option>
              </select>
            </div>

            <div className="text-sm text-gray-500">
              {filteredTemplates.length} template{filteredTemplates.length !== 1 ? 's' : ''}
            </div>
          </div>
        </div>

        {/* Templates Grid */}
        {loading ? (
          <div className="flex items-center justify-center h-64">
            <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-primary-500"></div>
          </div>
        ) : filteredTemplates.length === 0 ? (
          <div className="text-center py-12">
            <DocumentDuplicateIcon className="mx-auto h-12 w-12 text-gray-400 mb-4" />
            <h3 className="text-lg font-medium text-gray-900 mb-2">No templates found</h3>
            <p className="text-gray-500 mb-4">
              {searchQuery || filter !== 'all' || platformFilter !== 'all'
                ? 'Try adjusting your search or filters'
                : 'Get started by creating your first template'
              }
            </p>
            {!searchQuery && filter === 'all' && platformFilter === 'all' && (
              <button
                onClick={handleCreateTemplate}
                className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-primary-600 hover:bg-primary-700"
              >
                <PlusIcon className="h-5 w-5 mr-2" />
                Create Your First Template
              </button>
            )}
          </div>
        ) : (
          <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
            {filteredTemplates.map((template) => (
              <TemplateCard
                key={template.id}
                template={template}
                onEdit={handleEditTemplate}
                onDelete={handleDeleteTemplate}
                onDuplicate={handleDuplicateTemplate}
                onPreview={handlePreviewTemplate}
              />
            ))}
          </div>
        )}

        {/* Template Modal */}
        <TemplateModal
          isOpen={isModalOpen}
          onClose={() => setIsModalOpen(false)}
          template={selectedTemplate}
          onSave={handleSaveTemplate}
          loading={modalLoading}
          integrations={integrations}
        />
      </div>
    </MainLayout>
  );
}