import React from 'react';
import { Bars3Icon, XMarkIcon } from '@heroicons/react/24/outline';
import { useUIStore } from '@/store/useStore';

export default function Header() {
  const { sidebarOpen, toggleSidebar } = useUIStore();

  return (
    <div className="sticky top-0 z-10 flex-shrink-0 flex h-16 bg-white border-b border-gray-200">
      <button
        type="button"
        className="px-4 border-r border-gray-200 text-gray-500 focus:outline-none focus:ring-2 focus:ring-inset focus:ring-primary-500 lg:hidden"
        onClick={toggleSidebar}
      >
        <span className="sr-only">Open sidebar</span>
        {sidebarOpen ? (
          <XMarkIcon className="h-6 w-6" aria-hidden="true" />
        ) : (
          <Bars3Icon className="h-6 w-6" aria-hidden="true" />
        )}
      </button>
      
      <div className="flex-1 px-4 flex justify-between items-center">
        <div className="flex-1 flex">
          <div className="w-full flex lg:ml-0">
            <div className="relative w-full text-gray-400 focus-within:text-gray-600">
              {/* Search functionality can be added here */}
            </div>
          </div>
        </div>
        
        <div className="ml-4 flex items-center lg:ml-6">
          {/* Notifications and other header items can be added here */}
          <div className="text-sm text-gray-600">
            Multi-Tenant Printer SaaS
          </div>
        </div>
      </div>
    </div>
  );
}