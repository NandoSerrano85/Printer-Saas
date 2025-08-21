import React, { useState, useEffect } from 'react';
import { useApiQuery } from '../../../hooks/useApiQuery';
import { useAnalytics } from '../../../hooks/useAnalytics';
import LoadingSpinner from '../../common/UI/LoadingSpinner';

const TemplateManager = () => {
  const { apiService } = useApiQuery();
  const { trackEvent } = useAnalytics();
  
  const [templates, setTemplates] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [editingTemplate, setEditingTemplate] = useState(null);

  useEffect(() => {
    loadTemplates();
  }, []);

  const loadTemplates = async () => {
    try {
      setIsLoading(true);
      const response = await apiService.get('/api/v1/templates');
      setTemplates(response);
    } catch (err) {
      setError('Failed to load templates');
      console.error('Error loading templates:', err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleCreateTemplate = () => {
    setEditingTemplate(null);
    setShowCreateModal(true);
    trackEvent('template_create_modal_opened');
  };

  const handleEditTemplate = (template) => {
    setEditingTemplate(template);
    setShowCreateModal(true);
    trackEvent('template_edit_modal_opened', { templateId: template.id });
  };

  const handleDeleteTemplate = async (templateId) => {
    if (!window.confirm('Are you sure you want to delete this template?')) {
      return;
    }

    try {
      await apiService.delete(`/api/v1/templates/${templateId}`);
      setTemplates(templates.filter(t => t.id !== templateId));
      trackEvent('template_deleted', { templateId });
    } catch (err) {
      setError('Failed to delete template');
      console.error('Error deleting template:', err);
    }
  };

  const handleSaveTemplate = async (templateData) => {
    try {
      if (editingTemplate) {
        const response = await apiService.put(`/api/v1/templates/${editingTemplate.id}`, templateData);
        setTemplates(templates.map(t => t.id === editingTemplate.id ? response : t));
        trackEvent('template_updated', { templateId: editingTemplate.id });
      } else {
        const response = await apiService.post('/api/v1/templates', templateData);
        setTemplates([...templates, response]);
        trackEvent('template_created', { templateId: response.id });
      }
      setShowCreateModal(false);
      setEditingTemplate(null);
    } catch (err) {
      setError('Failed to save template');
      console.error('Error saving template:', err);
    }
  };

  if (isLoading) {
    return <LoadingSpinner />;
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h2 className="text-2xl font-bold text-gray-900">Product Templates</h2>
        <button
          onClick={handleCreateTemplate}
          className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 flex items-center space-x-2"
        >
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
          </svg>
          <span>New Template</span>
        </button>
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded">
          {error}
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {templates.map((template) => (
          <TemplateCard
            key={template.id}
            template={template}
            onEdit={() => handleEditTemplate(template)}
            onDelete={() => handleDeleteTemplate(template.id)}
          />
        ))}
      </div>

      {templates.length === 0 && !isLoading && (
        <div className="text-center py-12">
          <svg className="mx-auto h-12 w-12 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
          </svg>
          <h3 className="mt-2 text-sm font-medium text-gray-900">No templates</h3>
          <p className="mt-1 text-sm text-gray-500">Get started by creating your first template.</p>
          <div className="mt-6">
            <button
              onClick={handleCreateTemplate}
              className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700"
            >
              Create Template
            </button>
          </div>
        </div>
      )}

      {showCreateModal && (
        <TemplateModal
          template={editingTemplate}
          onSave={handleSaveTemplate}
          onClose={() => {
            setShowCreateModal(false);
            setEditingTemplate(null);
          }}
        />
      )}
    </div>
  );
};

const TemplateCard = ({ template, onEdit, onDelete }) => (
  <div className="bg-white rounded-lg shadow border border-gray-200 p-6">
    <div className="flex justify-between items-start">
      <div className="flex-1">
        <h3 className="text-lg font-medium text-gray-900">{template.name}</h3>
        <p className="text-sm text-gray-600 mt-1">{template.title}</p>
        <p className="text-sm text-gray-500 mt-2 line-clamp-3">{template.description}</p>
      </div>
      <div className="flex space-x-2 ml-4">
        <button
          onClick={onEdit}
          className="text-gray-400 hover:text-gray-600"
          title="Edit template"
        >
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
          </svg>
        </button>
        <button
          onClick={onDelete}
          className="text-gray-400 hover:text-red-600"
          title="Delete template"
        >
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
          </svg>
        </button>
      </div>
    </div>
    
    <div className="mt-4 flex flex-wrap gap-2">
      {template.price && (
        <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
          ${template.price}
        </span>
      )}
      {template.quantity && (
        <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
          Qty: {template.quantity}
        </span>
      )}
    </div>
  </div>
);

const TemplateModal = ({ template, onSave, onClose }) => {
  const [formData, setFormData] = useState({
    name: template?.name || '',
    title: template?.title || '',
    description: template?.description || '',
    price: template?.price || '',
    quantity: template?.quantity || '',
    who_made: template?.who_made || 'i_did',
    when_made: template?.when_made || '2020_2023',
    materials: template?.materials || '',
    tags: template?.tags || '',
    ...template
  });

  const handleSubmit = (e) => {
    e.preventDefault();
    onSave(formData);
  };

  const handleChange = (field, value) => {
    setFormData(prev => ({ ...prev, [field]: value }));
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full mx-4 max-h-screen overflow-y-auto">
        <div className="p-6">
          <div className="flex justify-between items-center mb-6">
            <h3 className="text-lg font-medium text-gray-900">
              {template ? 'Edit Template' : 'Create Template'}
            </h3>
            <button
              onClick={onClose}
              className="text-gray-400 hover:text-gray-600"
            >
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>

          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700">Template Name</label>
                <input
                  type="text"
                  required
                  value={formData.name}
                  onChange={(e) => handleChange('name', e.target.value)}
                  className="mt-1 block w-full border border-gray-300 rounded-md px-3 py-2"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700">Product Title</label>
                <input
                  type="text"
                  value={formData.title}
                  onChange={(e) => handleChange('title', e.target.value)}
                  className="mt-1 block w-full border border-gray-300 rounded-md px-3 py-2"
                />
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700">Description</label>
              <textarea
                rows={3}
                value={formData.description}
                onChange={(e) => handleChange('description', e.target.value)}
                className="mt-1 block w-full border border-gray-300 rounded-md px-3 py-2"
              />
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700">Price</label>
                <input
                  type="number"
                  step="0.01"
                  value={formData.price}
                  onChange={(e) => handleChange('price', parseFloat(e.target.value))}
                  className="mt-1 block w-full border border-gray-300 rounded-md px-3 py-2"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700">Quantity</label>
                <input
                  type="number"
                  value={formData.quantity}
                  onChange={(e) => handleChange('quantity', parseInt(e.target.value))}
                  className="mt-1 block w-full border border-gray-300 rounded-md px-3 py-2"
                />
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700">Who Made</label>
                <select
                  value={formData.who_made}
                  onChange={(e) => handleChange('who_made', e.target.value)}
                  className="mt-1 block w-full border border-gray-300 rounded-md px-3 py-2"
                >
                  <option value="i_did">I did</option>
                  <option value="collective">A member of my shop</option>
                  <option value="someone_else">Someone else</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700">When Made</label>
                <select
                  value={formData.when_made}
                  onChange={(e) => handleChange('when_made', e.target.value)}
                  className="mt-1 block w-full border border-gray-300 rounded-md px-3 py-2"
                >
                  <option value="made_to_order">Made to order</option>
                  <option value="2020_2023">2020-2023</option>
                  <option value="2010_2019">2010-2019</option>
                  <option value="2004_2009">2004-2009</option>
                  <option value="before_2004">Before 2004</option>
                  <option value="2000_2003">2000-2003</option>
                  <option value="1990s">1990s</option>
                  <option value="1980s">1980s</option>
                </select>
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700">Materials (comma separated)</label>
              <input
                type="text"
                value={formData.materials}
                onChange={(e) => handleChange('materials', e.target.value)}
                className="mt-1 block w-full border border-gray-300 rounded-md px-3 py-2"
                placeholder="cotton, polyester, vinyl"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700">Tags (comma separated)</label>
              <input
                type="text"
                value={formData.tags}
                onChange={(e) => handleChange('tags', e.target.value)}
                className="mt-1 block w-full border border-gray-300 rounded-md px-3 py-2"
                placeholder="custom, personalized, gift"
              />
            </div>

            <div className="flex justify-end space-x-3 pt-6">
              <button
                type="button"
                onClick={onClose}
                className="bg-gray-300 text-gray-700 px-4 py-2 rounded-lg hover:bg-gray-400"
              >
                Cancel
              </button>
              <button
                type="submit"
                className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700"
              >
                {template ? 'Update' : 'Create'} Template
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
};

export default TemplateManager;