import React, { useState, useEffect, useRef } from 'react';
import { useApiQuery } from '../../../hooks/useApiQuery';
import { useAnalytics } from '../../../hooks/useAnalytics';
import ProgressIndicator from '../../common/UI/ProgressIndicator';

const ImprovedMockupCreator = ({ isOpen, onClose, onComplete }) => {
  const { apiService } = useApiQuery();
  const { trackEvent } = useAnalytics();
  const canvasRef = useRef(null);
  
  // Workflow state
  const [currentStep, setCurrentStep] = useState(1);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  
  // Step data
  const [selectedTemplate, setSelectedTemplate] = useState(null);
  const [uploadedFiles, setUploadedFiles] = useState([]);
  const [watermarkFile, setWatermarkFile] = useState(null);
  const [mockupSettings, setMockupSettings] = useState({
    name: '',
    startingNumber: 100,
    quality: 'high'
  });
  
  // Data from API
  const [templates, setTemplates] = useState([]);
  
  const steps = [
    { id: 1, title: 'Choose Template', description: 'Select a product template' },
    { id: 2, title: 'Upload Files', description: 'Add your design files' },
    { id: 3, title: 'Add Watermark', description: 'Optional branding watermark' },
    { id: 4, title: 'Configure', description: 'Set mockup preferences' },
    { id: 5, title: 'Create', description: 'Generate your mockups' }
  ];

  useEffect(() => {
    if (isOpen) {
      loadTemplates();
      trackEvent('mockup_creator_opened');
    }
  }, [isOpen]);

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

  const handleTemplateSelect = (template) => {
    setSelectedTemplate(template);
    trackEvent('template_selected', { templateId: template.id });
    setCurrentStep(2);
  };

  const handleFileUpload = (files) => {
    setUploadedFiles(files);
    trackEvent('files_uploaded', { fileCount: files.length });
    setCurrentStep(3);
  };

  const handleWatermarkUpload = (file) => {
    setWatermarkFile(file);
    setCurrentStep(4);
  };

  const handleSettingsUpdate = (settings) => {
    setMockupSettings(settings);
    setCurrentStep(5);
  };

  const handleCreateMockups = async () => {
    try {
      setIsLoading(true);
      
      const mockupData = {
        templateId: selectedTemplate.id,
        files: uploadedFiles,
        watermark: watermarkFile,
        settings: mockupSettings
      };

      const response = await apiService.post('/api/v1/mockups', mockupData);
      
      setSuccess('Mockups created successfully!');
      trackEvent('mockups_created', { 
        templateId: selectedTemplate.id,
        fileCount: uploadedFiles.length 
      });
      
      setTimeout(() => {
        onComplete(response);
        onClose();
      }, 2000);
      
    } catch (err) {
      setError('Failed to create mockups');
      console.error('Error creating mockups:', err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleStepNavigation = (stepId) => {
    if (stepId <= currentStep) {
      setCurrentStep(stepId);
    }
  };

  const renderStepContent = () => {
    switch (currentStep) {
      case 1:
        return (
          <TemplateSelection
            templates={templates}
            selectedTemplate={selectedTemplate}
            onSelect={handleTemplateSelect}
            isLoading={isLoading}
          />
        );
      case 2:
        return (
          <FileUpload
            uploadedFiles={uploadedFiles}
            onUpload={handleFileUpload}
            onNext={() => setCurrentStep(3)}
          />
        );
      case 3:
        return (
          <WatermarkUpload
            watermarkFile={watermarkFile}
            onUpload={handleWatermarkUpload}
            onSkip={() => setCurrentStep(4)}
          />
        );
      case 4:
        return (
          <MockupSettings
            settings={mockupSettings}
            onUpdate={handleSettingsUpdate}
          />
        );
      case 5:
        return (
          <MockupCreation
            template={selectedTemplate}
            files={uploadedFiles}
            watermark={watermarkFile}
            settings={mockupSettings}
            onCreate={handleCreateMockups}
            isLoading={isLoading}
          />
        );
      default:
        return null;
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl max-w-4xl w-full mx-4 max-h-screen overflow-y-auto">
        <div className="p-6">
          <div className="flex justify-between items-center mb-6">
            <h2 className="text-2xl font-bold text-gray-900">Create Mockups</h2>
            <button
              onClick={onClose}
              className="text-gray-400 hover:text-gray-600 transition-colors"
            >
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>

          <ProgressIndicator 
            steps={steps} 
            currentStep={currentStep} 
            onStepClick={handleStepNavigation}
          />

          {error && (
            <div className="mb-4 bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded">
              {error}
            </div>
          )}

          {success && (
            <div className="mb-4 bg-green-50 border border-green-200 text-green-700 px-4 py-3 rounded">
              {success}
            </div>
          )}

          <div className="min-h-96">
            {renderStepContent()}
          </div>
        </div>
      </div>
    </div>
  );
};

// Component placeholders for sub-components
const TemplateSelection = ({ templates, selectedTemplate, onSelect, isLoading }) => (
  <div className="space-y-4">
    <h3 className="text-lg font-medium text-gray-900">Choose a Template</h3>
    {isLoading ? (
      <div className="text-center py-8">Loading templates...</div>
    ) : (
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {templates.map((template) => (
          <div
            key={template.id}
            className={`border rounded-lg p-4 cursor-pointer transition-colors ${
              selectedTemplate?.id === template.id
                ? 'border-blue-500 bg-blue-50'
                : 'border-gray-200 hover:border-gray-300'
            }`}
            onClick={() => onSelect(template)}
          >
            <h4 className="font-medium text-gray-900">{template.name}</h4>
            <p className="text-sm text-gray-600">{template.description}</p>
          </div>
        ))}
      </div>
    )}
  </div>
);

const FileUpload = ({ uploadedFiles, onUpload, onNext }) => (
  <div className="space-y-4">
    <h3 className="text-lg font-medium text-gray-900">Upload Design Files</h3>
    <div className="border-2 border-dashed border-gray-300 rounded-lg p-8 text-center">
      <p className="text-gray-600">Drag and drop files here or click to browse</p>
      <input type="file" multiple className="mt-4" onChange={(e) => onUpload(Array.from(e.target.files))} />
    </div>
    {uploadedFiles.length > 0 && (
      <div className="space-y-2">
        <h4 className="font-medium">Uploaded Files:</h4>
        {uploadedFiles.map((file, index) => (
          <div key={index} className="flex items-center space-x-2">
            <span className="text-sm text-gray-600">{file.name}</span>
          </div>
        ))}
        <button
          onClick={onNext}
          className="mt-4 bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700"
        >
          Next
        </button>
      </div>
    )}
  </div>
);

const WatermarkUpload = ({ watermarkFile, onUpload, onSkip }) => (
  <div className="space-y-4">
    <h3 className="text-lg font-medium text-gray-900">Add Watermark (Optional)</h3>
    <div className="border-2 border-dashed border-gray-300 rounded-lg p-8 text-center">
      <p className="text-gray-600">Upload a watermark image</p>
      <input type="file" className="mt-4" onChange={(e) => onUpload(e.target.files[0])} />
    </div>
    <div className="flex space-x-4">
      <button
        onClick={onSkip}
        className="bg-gray-300 text-gray-700 px-4 py-2 rounded hover:bg-gray-400"
      >
        Skip
      </button>
      {watermarkFile && (
        <button
          onClick={() => onUpload(watermarkFile)}
          className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700"
        >
          Next
        </button>
      )}
    </div>
  </div>
);

const MockupSettings = ({ settings, onUpdate }) => (
  <div className="space-y-4">
    <h3 className="text-lg font-medium text-gray-900">Configure Mockup Settings</h3>
    <div className="space-y-4">
      <div>
        <label className="block text-sm font-medium text-gray-700">Mockup Name</label>
        <input
          type="text"
          value={settings.name}
          onChange={(e) => onUpdate({ ...settings, name: e.target.value })}
          className="mt-1 block w-full border border-gray-300 rounded-md px-3 py-2"
        />
      </div>
      <div>
        <label className="block text-sm font-medium text-gray-700">Starting Number</label>
        <input
          type="number"
          value={settings.startingNumber}
          onChange={(e) => onUpdate({ ...settings, startingNumber: parseInt(e.target.value) })}
          className="mt-1 block w-full border border-gray-300 rounded-md px-3 py-2"
        />
      </div>
      <div>
        <label className="block text-sm font-medium text-gray-700">Quality</label>
        <select
          value={settings.quality}
          onChange={(e) => onUpdate({ ...settings, quality: e.target.value })}
          className="mt-1 block w-full border border-gray-300 rounded-md px-3 py-2"
        >
          <option value="high">High</option>
          <option value="medium">Medium</option>
          <option value="low">Low</option>
        </select>
      </div>
    </div>
    <button
      onClick={() => onUpdate(settings)}
      className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700"
    >
      Next
    </button>
  </div>
);

const MockupCreation = ({ template, files, watermark, settings, onCreate, isLoading }) => (
  <div className="space-y-4">
    <h3 className="text-lg font-medium text-gray-900">Review and Create</h3>
    <div className="bg-gray-50 rounded-lg p-4 space-y-2">
      <p><strong>Template:</strong> {template?.name}</p>
      <p><strong>Files:</strong> {files.length} uploaded</p>
      <p><strong>Watermark:</strong> {watermark ? 'Yes' : 'No'}</p>
      <p><strong>Name:</strong> {settings.name}</p>
      <p><strong>Quality:</strong> {settings.quality}</p>
    </div>
    <button
      onClick={onCreate}
      disabled={isLoading}
      className="w-full bg-green-600 text-white px-4 py-2 rounded hover:bg-green-700 disabled:bg-gray-400"
    >
      {isLoading ? 'Creating Mockups...' : 'Create Mockups'}
    </button>
  </div>
);

export default ImprovedMockupCreator;