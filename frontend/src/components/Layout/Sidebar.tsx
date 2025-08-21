import React from 'react';
import Link from 'next/link';
import { useRouter } from 'next/router';
import { 
  HomeIcon, 
  ChartBarIcon, 
  ShoppingBagIcon, 
  DocumentTextIcon,
  CogIcon,
  BuildingOffice2Icon,
  UserGroupIcon,
  ArrowRightOnRectangleIcon,
  PhotoIcon,
  UserIcon
} from '@heroicons/react/24/outline';
import { useAuthStore, useUIStore } from '@/store/useStore';
import clsx from 'clsx';

const navigation = [
  { name: 'Dashboard', href: '/dashboard', icon: HomeIcon },
  { name: 'Analytics', href: '/analytics', icon: ChartBarIcon },
  { name: 'Orders', href: '/orders', icon: ShoppingBagIcon },
  { 
    name: 'Templates', 
    href: '/templates', 
    icon: DocumentTextIcon,
    subItems: [
      { name: 'Mockup Creator', href: '/mockups', icon: PhotoIcon }
    ]
  },
  { name: 'Integrations', href: '/integrations', icon: CogIcon },
  { name: 'Profile', href: '/profile', icon: UserIcon },
  { name: 'Tenants', href: '/tenants', icon: BuildingOffice2Icon, adminOnly: true },
  { name: 'Users', href: '/users', icon: UserGroupIcon, adminOnly: true },
];

export default function Sidebar() {
  const router = useRouter();
  const { user, logout } = useAuthStore();
  const { sidebarOpen, setSidebarOpen } = useUIStore();

  const handleLogout = () => {
    logout();
    router.push('/login');
  };

  if (!sidebarOpen) return null;

  return (
    <div className="flex flex-col w-64 bg-gray-900">
      <div className="flex items-center justify-center h-16 bg-gray-800">
        <h1 className="text-white text-xl font-bold">Printer SaaS</h1>
      </div>
      
      <div className="flex flex-col flex-1 overflow-y-auto">
        <nav className="flex-1 px-2 py-4 bg-gray-900">
          <div className="space-y-1">
            {navigation.map((item) => {
              // Skip admin-only items for non-admin users
              if (item.adminOnly && user?.email !== 'admin@printersaas.dev') {
                return null;
              }

              const isActive = router.pathname === item.href;
              const hasSubItems = item.subItems && item.subItems.length > 0;
              const isSubItemActive = hasSubItems && item.subItems.some(subItem => router.pathname === subItem.href);
              
              return (
                <div key={item.name}>
                  <Link
                    href={item.href}
                    className={clsx(
                      isActive || isSubItemActive
                        ? 'bg-gray-800 text-white'
                        : 'text-gray-300 hover:bg-gray-700 hover:text-white',
                      'group flex items-center px-2 py-2 text-sm font-medium rounded-md'
                    )}
                  >
                    <item.icon
                      className={clsx(
                        isActive || isSubItemActive
                          ? 'text-gray-300'
                          : 'text-gray-400 group-hover:text-gray-300',
                        'mr-3 flex-shrink-0 h-6 w-6'
                      )}
                      aria-hidden="true"
                    />
                    {item.name}
                  </Link>

                  {/* Sub-items */}
                  {hasSubItems && (
                    <div className="ml-6 mt-1 space-y-1">
                      {item.subItems.map((subItem) => {
                        const isSubActive = router.pathname === subItem.href;
                        return (
                          <Link
                            key={subItem.name}
                            href={subItem.href}
                            className={clsx(
                              isSubActive
                                ? 'bg-gray-700 text-white'
                                : 'text-gray-400 hover:bg-gray-700 hover:text-white',
                              'group flex items-center px-2 py-2 text-xs font-medium rounded-md'
                            )}
                          >
                            <subItem.icon
                              className={clsx(
                                isSubActive
                                  ? 'text-gray-300'
                                  : 'text-gray-500 group-hover:text-gray-300',
                                'mr-2 flex-shrink-0 h-4 w-4'
                              )}
                              aria-hidden="true"
                            />
                            {subItem.name}
                          </Link>
                        );
                      })}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </nav>
        
        {/* User section */}
        <div className="flex-shrink-0 flex bg-gray-800 p-4">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <div className="h-8 w-8 rounded-full bg-gray-600 flex items-center justify-center">
                <span className="text-sm font-medium text-white">
                  {user?.full_name?.charAt(0) || user?.email?.charAt(0) || 'U'}
                </span>
              </div>
            </div>
            <div className="ml-3">
              <p className="text-sm font-medium text-white">
                {user?.full_name || 'User'}
              </p>
              <p className="text-xs font-medium text-gray-300">
                {user?.email}
              </p>
            </div>
            <button
              onClick={handleLogout}
              className="ml-auto flex-shrink-0 bg-gray-800 p-1 rounded-full text-gray-400 hover:text-white focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-offset-gray-800 focus:ring-white"
            >
              <span className="sr-only">Logout</span>
              <ArrowRightOnRectangleIcon className="h-6 w-6" />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}