import React, { useState, useEffect, useRef } from 'react';
import MainLayout from '@/components/Layout/MainLayout';
import { useAppStore } from '@/store/useStore';
import apiService from '@/services/api';
import {
  PhotoIcon,
  SwatchIcon,
  AdjustmentsHorizontalIcon,
  ArrowDownTrayIcon,
  EyeIcon,
  PlusIcon,
  XMarkIcon,
} from '@heroicons/react/24/outline';
import toast from 'react-hot-toast';

interface MockupTemplate {
  id: string;
  name: string;
  category: string;
  previewUrl: string;
  width: number;
  height: number;
  placeholders: MockupPlaceholder[];
}

interface MockupPlaceholder {
  id: string;
  type: 'image' | 'text';
  x: number;
  y: number;
  width: number;
  height: number;
  rotation: number;
  name: string;
}

interface MockupProject {
  id?: string;
  name: string;
  template: MockupTemplate;
  elements: MockupElement[];
  backgroundColor: string;
  createdAt?: string;
  updatedAt?: string;
}

interface MockupElement {
  id: string;
  placeholderId: string;
  type: 'image' | 'text';
  content: string; // URL for images, text content for text
  x: number;
  y: number;
  width: number;
  height: number;
  rotation: number;
  opacity: number;
  filters: {
    brightness: number;
    contrast: number;
    saturation: number;
    blur: number;
  };
  textStyles?: {
    fontSize: number;
    fontFamily: string;
    color: string;
    bold: boolean;
    italic: boolean;
  };
}

const MockupCreator: React.FC = () => {
  const [templates, setTemplates] = useState<MockupTemplate[]>([]);
  const [projects, setProjects] = useState<MockupProject[]>([]);
  const [currentProject, setCurrentProject] = useState<MockupProject | null>(null);
  const [selectedElement, setSelectedElement] = useState<MockupElement | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [view, setView] = useState<'templates' | 'editor' | 'projects'>('templates');
  const [zoom, setZoom] = useState(100);
  const canvasRef = useRef<HTMLDivElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    loadTemplates();
    loadProjects();
  }, []);

  const loadTemplates = async () => {
    try {
      const response = await apiService.get('/api/v1/mockups/templates');
      setTemplates(response.templates || []);
    } catch (error) {
      console.error('Failed to load templates:', error);
      // Mock data for development
      setTemplates([
        {
          id: '1',
          name: 'T-Shirt Front',
          category: 'Apparel',
          previewUrl: '/mockups/tshirt-front.jpg',
          width: 800,
          height: 600,
          placeholders: [
            {
              id: 'design',
              type: 'image',
              x: 300,
              y: 200,
              width: 200,
              height: 200,
              rotation: 0,
              name: 'Design Area',
            },
          ],
        },
        {
          id: '2',
          name: 'Coffee Mug',
          category: 'Drinkware',
          previewUrl: '/mockups/mug.jpg',
          width: 600,
          height: 600,
          placeholders: [
            {
              id: 'design',
              type: 'image',
              x: 200,
              y: 150,
              width: 200,
              height: 150,
              rotation: -10,
              name: 'Mug Design',
            },
          ],
        },
        {
          id: '3',
          name: 'Phone Case',
          category: 'Accessories',
          previewUrl: '/mockups/phone-case.jpg',
          width: 400,
          height: 800,
          placeholders: [
            {
              id: 'design',
              type: 'image',
              x: 50,
              y: 100,
              width: 300,
              height: 600,
              rotation: 0,
              name: 'Case Design',
            },
          ],
        },
      ]);
    }
  };

  const loadProjects = async () => {
    try {
      const response = await apiService.get('/api/v1/mockups/projects');
      setProjects(response.projects || []);
    } catch (error) {
      console.error('Failed to load projects:', error);
    }
  };

  const createNewProject = (template: MockupTemplate) => {
    const newProject: MockupProject = {
      name: `New ${template.name} Project`,
      template,
      elements: [],
      backgroundColor: '#ffffff',
      createdAt: new Date().toISOString(),
    };
    setCurrentProject(newProject);
    setView('editor');
  };

  const saveProject = async () => {
    if (!currentProject) return;
    
    setIsLoading(true);
    try {
      let response;
      if (currentProject.id) {
        response = await apiService.put(`/api/v1/mockups/projects/${currentProject.id}`, currentProject);
      } else {
        response = await apiService.post('/api/v1/mockups/projects', currentProject);
      }
      
      const savedProject = response.project;
      setCurrentProject(savedProject);
      
      // Update projects list
      setProjects(prev => {
        const index = prev.findIndex(p => p.id === savedProject.id);
        if (index >= 0) {
          return prev.map((p, i) => i === index ? savedProject : p);
        } else {
          return [...prev, savedProject];
        }
      });
      
      toast.success('Project saved successfully');
    } catch (error) {
      toast.error('Failed to save project');
    } finally {
      setIsLoading(false);
    }
  };

  const uploadImage = async (file: File) => {
    try {
      const formData = new FormData();
      formData.append('file', file);
      
      const response = await apiService.post('/api/v1/upload', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });
      
      return response.url;
    } catch (error) {
      toast.error('Failed to upload image');
      throw error;
    }
  };

  const addImageElement = async (placeholderId: string, file: File) => {
    try {
      const imageUrl = await uploadImage(file);
      const placeholder = currentProject?.template.placeholders.find(p => p.id === placeholderId);
      
      if (!placeholder || !currentProject) return;

      const newElement: MockupElement = {
        id: crypto.randomUUID(),
        placeholderId,
        type: 'image',
        content: imageUrl,
        x: placeholder.x,
        y: placeholder.y,
        width: placeholder.width,
        height: placeholder.height,
        rotation: placeholder.rotation,
        opacity: 1,
        filters: {
          brightness: 100,
          contrast: 100,
          saturation: 100,
          blur: 0,
        },
      };

      setCurrentProject(prev => prev ? {
        ...prev,
        elements: [...prev.elements.filter(e => e.placeholderId !== placeholderId), newElement],
      } : null);

      setSelectedElement(newElement);
    } catch (error) {
      console.error('Failed to add image element:', error);
    }
  };

  const addTextElement = (placeholderId: string, text: string) => {
    const placeholder = currentProject?.template.placeholders.find(p => p.id === placeholderId);
    
    if (!placeholder || !currentProject) return;

    const newElement: MockupElement = {
      id: crypto.randomUUID(),
      placeholderId,
      type: 'text',
      content: text,
      x: placeholder.x,
      y: placeholder.y,
      width: placeholder.width,
      height: placeholder.height,
      rotation: placeholder.rotation,
      opacity: 1,
      filters: {
        brightness: 100,
        contrast: 100,
        saturation: 100,
        blur: 0,
      },
      textStyles: {
        fontSize: 24,
        fontFamily: 'Arial',
        color: '#000000',
        bold: false,
        italic: false,
      },
    };

    setCurrentProject(prev => prev ? {
      ...prev,
      elements: [...prev.elements.filter(e => e.placeholderId !== placeholderId), newElement],
    } : null);

    setSelectedElement(newElement);
  };

  const updateElement = (elementId: string, updates: Partial<MockupElement>) => {
    setCurrentProject(prev => prev ? {
      ...prev,
      elements: prev.elements.map(el => 
        el.id === elementId ? { ...el, ...updates } : el
      ),
    } : null);

    if (selectedElement?.id === elementId) {
      setSelectedElement(prev => prev ? { ...prev, ...updates } : null);
    }
  };

  const deleteElement = (elementId: string) => {
    setCurrentProject(prev => prev ? {
      ...prev,
      elements: prev.elements.filter(el => el.id !== elementId),
    } : null);

    if (selectedElement?.id === elementId) {
      setSelectedElement(null);
    }
  };

  const exportMockup = async (format: 'png' | 'jpg' | 'pdf' = 'png') => {
    if (!currentProject) return;

    setIsLoading(true);
    try {
      const response = await apiService.post('/api/v1/mockups/export', {
        project: currentProject,
        format,
        quality: 100,
      });

      // Create download link
      const link = document.createElement('a');
      link.href = response.downloadUrl;
      link.download = `${currentProject.name}.${format}`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);

      toast.success('Mockup exported successfully');
    } catch (error) {
      toast.error('Failed to export mockup');
    } finally {
      setIsLoading(false);
    }
  };

  const categories = Array.from(new Set(templates.map(t => t.category)));

  if (view === 'templates') {
    return (
      <MainLayout>
        <div className="space-y-6">
          {/* Header */}
          <div className="flex justify-between items-center">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">Mockup Creator</h1>
              <p className="mt-1 text-sm text-gray-500">
                Create stunning product mockups with our templates
              </p>
            </div>
            <div className="flex space-x-2">
              <button
                onClick={() => setView('projects')}
                className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50"
              >
                My Projects
              </button>
            </div>
          </div>

          {/* Categories */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
            {categories.map(category => (
              <div key={category} className="bg-white rounded-lg shadow p-6">
                <h3 className="text-lg font-medium text-gray-900 mb-4">{category}</h3>
                <div className="grid grid-cols-1 gap-4">
                  {templates.filter(t => t.category === category).map(template => (
                    <div
                      key={template.id}
                      className="group cursor-pointer border rounded-lg overflow-hidden hover:shadow-md transition-shadow"
                      onClick={() => createNewProject(template)}
                    >
                      <div className="aspect-w-4 aspect-h-3 bg-gray-200">
                        <img
                          src={template.previewUrl}
                          alt={template.name}
                          className="w-full h-32 object-cover group-hover:scale-105 transition-transform duration-200"
                          onError={(e) => {
                            const target = e.target as HTMLImageElement;
                            target.style.display = 'none';
                            target.nextElementSibling?.classList.remove('hidden');
                          }}
                        />
                        <div className="hidden w-full h-32 bg-gray-100 flex items-center justify-center">
                          <PhotoIcon className="w-8 h-8 text-gray-400" />
                        </div>
                      </div>
                      <div className="p-3">
                        <h4 className="text-sm font-medium text-gray-900">{template.name}</h4>
                        <p className="text-xs text-gray-500">
                          {template.width} × {template.height}px
                        </p>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </div>
      </MainLayout>
    );
  }

  if (view === 'projects') {
    return (
      <MainLayout>
        <div className="space-y-6">
          {/* Header */}
          <div className="flex justify-between items-center">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">My Projects</h1>
              <p className="mt-1 text-sm text-gray-500">
                Manage your saved mockup projects
              </p>
            </div>
            <div className="flex space-x-2">
              <button
                onClick={() => setView('templates')}
                className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50"
              >
                New Project
              </button>
            </div>
          </div>

          {/* Projects Grid */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
            {projects.map(project => (
              <div
                key={project.id}
                className="bg-white rounded-lg shadow overflow-hidden hover:shadow-md transition-shadow cursor-pointer"
                onClick={() => {
                  setCurrentProject(project);
                  setView('editor');
                }}
              >
                <div className="aspect-w-4 aspect-h-3 bg-gray-200">
                  <img
                    src={project.template.previewUrl}
                    alt={project.name}
                    className="w-full h-32 object-cover"
                    onError={(e) => {
                      const target = e.target as HTMLImageElement;
                      target.style.display = 'none';
                      target.nextElementSibling?.classList.remove('hidden');
                    }}
                  />
                  <div className="hidden w-full h-32 bg-gray-100 flex items-center justify-center">
                    <PhotoIcon className="w-8 h-8 text-gray-400" />
                  </div>
                </div>
                <div className="p-4">
                  <h3 className="text-sm font-medium text-gray-900">{project.name}</h3>
                  <p className="text-xs text-gray-500">{project.template.name}</p>
                  <p className="text-xs text-gray-400 mt-1">
                    {project.updatedAt ? new Date(project.updatedAt).toLocaleDateString() : 'Never saved'}
                  </p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </MainLayout>
    );
  }

  if (view === 'editor' && currentProject) {
    return (
      <MainLayout>
        <div className="flex h-screen">
          {/* Toolbar */}
          <div className="w-64 bg-white border-r border-gray-200 flex flex-col">
            <div className="p-4 border-b border-gray-200">
              <input
                type="text"
                value={currentProject.name}
                onChange={(e) => setCurrentProject(prev => prev ? { ...prev, name: e.target.value } : null)}
                className="w-full text-lg font-medium border-none bg-transparent focus:outline-none"
              />
              <div className="flex space-x-2 mt-2">
                <button
                  onClick={saveProject}
                  disabled={isLoading}
                  className="flex-1 px-3 py-1 text-sm bg-primary-600 text-white rounded hover:bg-primary-700 disabled:opacity-50"
                >
                  {isLoading ? 'Saving...' : 'Save'}
                </button>
                <button
                  onClick={() => exportMockup('png')}
                  disabled={isLoading}
                  className="flex-1 px-3 py-1 text-sm bg-green-600 text-white rounded hover:bg-green-700 disabled:opacity-50"
                >
                  Export
                </button>
              </div>
            </div>

            {/* Elements Panel */}
            <div className="flex-1 overflow-y-auto">
              <div className="p-4">
                <h3 className="text-sm font-medium text-gray-900 mb-3">Design Elements</h3>
                
                {currentProject.template.placeholders.map(placeholder => (
                  <div key={placeholder.id} className="mb-4 p-3 border rounded-lg">
                    <h4 className="text-sm font-medium text-gray-700 mb-2">{placeholder.name}</h4>
                    
                    <div className="space-y-2">
                      <button
                        onClick={() => fileInputRef.current?.click()}
                        className="w-full px-3 py-2 text-sm border border-dashed border-gray-300 rounded-lg hover:border-gray-400 flex items-center justify-center"
                      >
                        <PhotoIcon className="w-4 h-4 mr-2" />
                        Add Image
                      </button>
                      
                      <button
                        onClick={() => {
                          const text = prompt('Enter text:');
                          if (text) addTextElement(placeholder.id, text);
                        }}
                        className="w-full px-3 py-2 text-sm border border-dashed border-gray-300 rounded-lg hover:border-gray-400 flex items-center justify-center"
                      >
                        <PlusIcon className="w-4 h-4 mr-2" />
                        Add Text
                      </button>
                    </div>

                    {/* Show current element */}
                    {currentProject.elements.find(e => e.placeholderId === placeholder.id) && (
                      <div className="mt-2 p-2 bg-gray-50 rounded text-xs">
                        Current: {currentProject.elements.find(e => e.placeholderId === placeholder.id)?.type}
                        <button
                          onClick={() => {
                            const element = currentProject.elements.find(e => e.placeholderId === placeholder.id);
                            if (element) deleteElement(element.id);
                          }}
                          className="ml-2 text-red-600 hover:text-red-800"
                        >
                          <XMarkIcon className="w-3 h-3" />
                        </button>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>

            {/* Properties Panel */}
            {selectedElement && (
              <div className="border-t border-gray-200 p-4">
                <h3 className="text-sm font-medium text-gray-900 mb-3">Properties</h3>
                
                <div className="space-y-3">
                  <div>
                    <label className="block text-xs font-medium text-gray-700">Opacity</label>
                    <input
                      type="range"
                      min="0"
                      max="100"
                      value={selectedElement.opacity * 100}
                      onChange={(e) => updateElement(selectedElement.id, { opacity: parseInt(e.target.value) / 100 })}
                      className="w-full"
                    />
                  </div>

                  <div>
                    <label className="block text-xs font-medium text-gray-700">Rotation</label>
                    <input
                      type="range"
                      min="-180"
                      max="180"
                      value={selectedElement.rotation}
                      onChange={(e) => updateElement(selectedElement.id, { rotation: parseInt(e.target.value) })}
                      className="w-full"
                    />
                  </div>

                  {selectedElement.type === 'image' && (
                    <>
                      <div>
                        <label className="block text-xs font-medium text-gray-700">Brightness</label>
                        <input
                          type="range"
                          min="0"
                          max="200"
                          value={selectedElement.filters.brightness}
                          onChange={(e) => updateElement(selectedElement.id, {
                            filters: { ...selectedElement.filters, brightness: parseInt(e.target.value) }
                          })}
                          className="w-full"
                        />
                      </div>

                      <div>
                        <label className="block text-xs font-medium text-gray-700">Contrast</label>
                        <input
                          type="range"
                          min="0"
                          max="200"
                          value={selectedElement.filters.contrast}
                          onChange={(e) => updateElement(selectedElement.id, {
                            filters: { ...selectedElement.filters, contrast: parseInt(e.target.value) }
                          })}
                          className="w-full"
                        />
                      </div>
                    </>
                  )}

                  {selectedElement.type === 'text' && selectedElement.textStyles && (
                    <>
                      <div>
                        <label className="block text-xs font-medium text-gray-700">Font Size</label>
                        <input
                          type="range"
                          min="8"
                          max="72"
                          value={selectedElement.textStyles.fontSize}
                          onChange={(e) => updateElement(selectedElement.id, {
                            textStyles: { ...selectedElement.textStyles!, fontSize: parseInt(e.target.value) }
                          })}
                          className="w-full"
                        />
                      </div>

                      <div>
                        <label className="block text-xs font-medium text-gray-700">Color</label>
                        <input
                          type="color"
                          value={selectedElement.textStyles.color}
                          onChange={(e) => updateElement(selectedElement.id, {
                            textStyles: { ...selectedElement.textStyles!, color: e.target.value }
                          })}
                          className="w-full h-8"
                        />
                      </div>
                    </>
                  )}
                </div>
              </div>
            )}
          </div>

          {/* Canvas */}
          <div className="flex-1 bg-gray-100 flex items-center justify-center overflow-hidden">
            <div className="bg-white shadow-lg" style={{ transform: `scale(${zoom / 100})` }}>
              <div
                ref={canvasRef}
                className="relative"
                style={{
                  width: currentProject.template.width,
                  height: currentProject.template.height,
                  backgroundColor: currentProject.backgroundColor,
                }}
              >
                {/* Template Background */}
                <img
                  src={currentProject.template.previewUrl}
                  alt="Template"
                  className="absolute inset-0 w-full h-full object-cover"
                  draggable={false}
                />

                {/* Elements */}
                {currentProject.elements.map(element => (
                  <div
                    key={element.id}
                    className={`absolute cursor-pointer border-2 ${
                      selectedElement?.id === element.id ? 'border-primary-500' : 'border-transparent'
                    }`}
                    style={{
                      left: element.x,
                      top: element.y,
                      width: element.width,
                      height: element.height,
                      transform: `rotate(${element.rotation}deg)`,
                      opacity: element.opacity,
                    }}
                    onClick={() => setSelectedElement(element)}
                  >
                    {element.type === 'image' ? (
                      <img
                        src={element.content}
                        alt="Design element"
                        className="w-full h-full object-cover"
                        style={{
                          filter: `brightness(${element.filters.brightness}%) contrast(${element.filters.contrast}%) saturate(${element.filters.saturation}%) blur(${element.filters.blur}px)`,
                        }}
                        draggable={false}
                      />
                    ) : (
                      <div
                        className="w-full h-full flex items-center justify-center"
                        style={{
                          fontSize: element.textStyles?.fontSize || 24,
                          fontFamily: element.textStyles?.fontFamily || 'Arial',
                          color: element.textStyles?.color || '#000000',
                          fontWeight: element.textStyles?.bold ? 'bold' : 'normal',
                          fontStyle: element.textStyles?.italic ? 'italic' : 'normal',
                        }}
                      >
                        {element.content}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>

            {/* Zoom Controls */}
            <div className="absolute bottom-4 right-4 bg-white rounded-lg shadow-lg p-2 flex items-center space-x-2">
              <button
                onClick={() => setZoom(Math.max(25, zoom - 25))}
                className="p-1 hover:bg-gray-100 rounded"
              >
                -
              </button>
              <span className="text-sm font-medium">{zoom}%</span>
              <button
                onClick={() => setZoom(Math.min(200, zoom + 25))}
                className="p-1 hover:bg-gray-100 rounded"
              >
                +
              </button>
            </div>
          </div>

          {/* Hidden file input */}
          <input
            ref={fileInputRef}
            type="file"
            accept="image/*"
            className="hidden"
            onChange={(e) => {
              const file = e.target.files?.[0];
              if (file && currentProject.template.placeholders.length > 0) {
                addImageElement(currentProject.template.placeholders[0].id, file);
              }
            }}
          />
        </div>
      </MainLayout>
    );
  }

  return <div>Loading...</div>;
};

export default MockupCreator;