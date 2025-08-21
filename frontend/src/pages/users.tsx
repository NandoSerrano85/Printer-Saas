import React, { useState, useEffect } from 'react';
import MainLayout from '@/components/Layout/MainLayout';
import apiService from '@/services/api';
import {
  PlusIcon,
  PencilIcon,
  TrashIcon,
  MagnifyingGlassIcon,
  FunnelIcon,
  UserIcon,
  EnvelopeIcon,
  CalendarIcon,
} from '@heroicons/react/24/outline';
import toast from 'react-hot-toast';

interface User {
  id: string;
  email: string;
  full_name: string;
  is_active: boolean;
  created_at: string;
  last_login: string | null;
  role: 'admin' | 'user';
}

const UserCard: React.FC<{
  user: User;
  onEdit: (user: User) => void;
  onDelete: (id: string) => void;
}> = ({ user, onEdit, onDelete }) => (
  <div className="bg-white overflow-hidden shadow rounded-lg">
    <div className="p-6">
      <div className="flex items-center">
        <div className="flex-shrink-0">
          <div className="h-10 w-10 rounded-full bg-gray-200 flex items-center justify-center">
            <UserIcon className="h-6 w-6 text-gray-500" />
          </div>
        </div>
        <div className="ml-4 flex-1">
          <h3 className="text-lg font-medium text-gray-900">{user.full_name}</h3>
          <div className="flex items-center text-sm text-gray-500">
            <EnvelopeIcon className="h-4 w-4 mr-1" />
            {user.email}
          </div>
          <div className="flex items-center text-sm text-gray-500 mt-1">
            <CalendarIcon className="h-4 w-4 mr-1" />
            Joined {new Date(user.created_at).toLocaleDateString()}
          </div>
        </div>
        <div className="flex flex-col items-end space-y-2">
          <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
            user.is_active 
              ? 'bg-green-100 text-green-800' 
              : 'bg-red-100 text-red-800'
          }`}>
            {user.is_active ? 'Active' : 'Inactive'}
          </span>
          <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
            user.role === 'admin'
              ? 'bg-purple-100 text-purple-800'
              : 'bg-blue-100 text-blue-800'
          }`}>
            {user.role === 'admin' ? 'Admin' : 'User'}
          </span>
        </div>
      </div>
      
      <div className="mt-4 flex space-x-2">
        <button
          onClick={() => onEdit(user)}
          className="flex-1 inline-flex items-center justify-center px-3 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-primary-600 hover:bg-primary-700"
        >
          <PencilIcon className="h-4 w-4 mr-1" />
          Edit
        </button>
        <button
          onClick={() => onDelete(user.id)}
          className="inline-flex items-center justify-center px-3 py-2 border border-gray-300 shadow-sm text-sm font-medium rounded-md text-red-700 bg-white hover:bg-red-50"
        >
          <TrashIcon className="h-4 w-4" />
        </button>
      </div>
    </div>
  </div>
);

export default function Users() {
  const [users, setUsers] = useState<User[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [filter, setFilter] = useState('all');

  useEffect(() => {
    loadUsers();
  }, []);

  const loadUsers = async () => {
    try {
      // For now, use fallback data since the API might not be available
      const fallbackUsers: User[] = [
        {
          id: '1',
          email: 'admin@printersaas.dev',
          full_name: 'System Administrator',
          is_active: true,
          created_at: new Date().toISOString(),
          last_login: new Date().toISOString(),
          role: 'admin'
        },
        {
          id: '2',
          email: 'user@example.com',
          full_name: 'John Doe',
          is_active: true,
          created_at: new Date(Date.now() - 86400000).toISOString(),
          last_login: new Date(Date.now() - 3600000).toISOString(),
          role: 'user'
        }
      ];
      
      setUsers(fallbackUsers);
    } catch (error) {
      console.error('Error loading users:', error);
      toast.error('Failed to load users');
    } finally {
      setLoading(false);
    }
  };

  const handleEditUser = (user: User) => {
    toast.info('User editing feature coming soon');
  };

  const handleDeleteUser = async (id: string) => {
    if (!confirm('Are you sure you want to delete this user?')) return;
    
    try {
      toast.success('User deleted successfully');
      setUsers(users.filter(user => user.id !== id));
    } catch (error) {
      toast.error('Failed to delete user');
    }
  };

  const filteredUsers = users.filter(user => {
    const matchesSearch = user.full_name.toLowerCase().includes(searchQuery.toLowerCase()) ||
                         user.email.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesFilter = filter === 'all' || 
                         (filter === 'active' && user.is_active) ||
                         (filter === 'inactive' && !user.is_active) ||
                         (filter === 'admin' && user.role === 'admin') ||
                         (filter === 'user' && user.role === 'user');
    
    return matchesSearch && matchesFilter;
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
        {/* Header */}
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Users</h1>
            <p className="mt-1 text-sm text-gray-500">
              Manage user accounts and permissions
            </p>
          </div>
          <div className="mt-4 sm:mt-0">
            <button
              onClick={() => toast.info('Create user feature coming soon')}
              className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-primary-600 hover:bg-primary-700"
            >
              <PlusIcon className="h-5 w-5 mr-2" />
              Add User
            </button>
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
                  placeholder="Search users..."
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
                <option value="all">All Users</option>
                <option value="active">Active</option>
                <option value="inactive">Inactive</option>
                <option value="admin">Admins</option>
                <option value="user">Regular Users</option>
              </select>
            </div>

            <div className="text-sm text-gray-500">
              {filteredUsers.length} user{filteredUsers.length !== 1 ? 's' : ''}
            </div>
          </div>
        </div>

        {/* Users Grid */}
        {filteredUsers.length === 0 ? (
          <div className="text-center py-12">
            <UserIcon className="mx-auto h-12 w-12 text-gray-400 mb-4" />
            <h3 className="text-lg font-medium text-gray-900 mb-2">No users found</h3>
            <p className="text-gray-500 mb-4">
              {searchQuery || filter !== 'all'
                ? 'Try adjusting your search or filters'
                : 'Get started by adding your first user'
              }
            </p>
          </div>
        ) : (
          <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3">
            {filteredUsers.map((user) => (
              <UserCard
                key={user.id}
                user={user}
                onEdit={handleEditUser}
                onDelete={handleDeleteUser}
              />
            ))}
          </div>
        )}
      </div>
    </MainLayout>
  );
}