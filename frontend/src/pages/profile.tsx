import React, { useState, useEffect } from 'react';
import MainLayout from '@/components/Layout/MainLayout';
import { useAuthStore } from '@/store/useStore';
import apiService from '@/services/api';
import { User } from '@/types';
import {
  UserIcon,
  KeyIcon,
  CreditCardIcon,
  BellIcon,
  ShieldCheckIcon,
  EyeIcon,
  EyeSlashIcon,
} from '@heroicons/react/24/outline';
import toast from 'react-hot-toast';

interface ProfileFormData {
  email: string;
  firstName: string;
  lastName: string;
  companyName?: string;
  phone?: string;
  timezone: string;
  language: string;
}

interface PasswordFormData {
  currentPassword: string;
  newPassword: string;
  confirmPassword: string;
}

interface BillingFormData {
  cardholderName: string;
  cardNumber: string;
  expiryMonth: string;
  expiryYear: string;
  cvv: string;
  billingAddress: {
    street: string;
    city: string;
    state: string;
    postalCode: string;
    country: string;
  };
}

interface NotificationSettings {
  emailNotifications: {
    orderUpdates: boolean;
    integrationAlerts: boolean;
    systemMaintenance: boolean;
    promotions: boolean;
  };
  pushNotifications: {
    orderCompleted: boolean;
    integrationErrors: boolean;
    lowInventory: boolean;
  };
}

const Profile: React.FC = () => {
  const { user, setUser } = useAuthStore();
  const [activeTab, setActiveTab] = useState<'profile' | 'security' | 'billing' | 'notifications'>('profile');
  const [isLoading, setIsLoading] = useState(false);
  const [showPassword, setShowPassword] = useState({
    current: false,
    new: false,
    confirm: false,
  });

  // Form states
  const [profileForm, setProfileForm] = useState<ProfileFormData>({
    email: user?.email || '',
    firstName: user?.full_name?.split(' ')[0] || '',
    lastName: user?.full_name?.split(' ').slice(1).join(' ') || '',
    companyName: '',
    phone: '',
    timezone: 'UTC',
    language: 'en',
  });

  const [passwordForm, setPasswordForm] = useState<PasswordFormData>({
    currentPassword: '',
    newPassword: '',
    confirmPassword: '',
  });

  const [billingForm, setBillingForm] = useState<BillingFormData>({
    cardholderName: '',
    cardNumber: '',
    expiryMonth: '',
    expiryYear: '',
    cvv: '',
    billingAddress: {
      street: '',
      city: '',
      state: '',
      postalCode: '',
      country: 'US',
    },
  });

  const [notifications, setNotifications] = useState<NotificationSettings>({
    emailNotifications: {
      orderUpdates: true,
      integrationAlerts: true,
      systemMaintenance: true,
      promotions: false,
    },
    pushNotifications: {
      orderCompleted: true,
      integrationErrors: true,
      lowInventory: false,
    },
  });

  useEffect(() => {
    loadUserProfile();
    loadBillingInfo();
    loadNotificationSettings();
  }, []);

  const loadUserProfile = async () => {
    try {
      const userProfile = await apiService.get('/api/v1/user/profile');
      // Update form with loaded data
      setProfileForm(prev => ({
        ...prev,
        ...userProfile,
      }));
    } catch (error) {
      console.error('Failed to load user profile:', error);
    }
  };

  const loadBillingInfo = async () => {
    try {
      const billing = await apiService.get('/api/v1/user/billing');
      setBillingForm(prev => ({
        ...prev,
        ...billing,
      }));
    } catch (error) {
      console.error('Failed to load billing info:', error);
    }
  };

  const loadNotificationSettings = async () => {
    try {
      const settings = await apiService.get('/api/v1/user/notifications');
      setNotifications(prev => ({
        ...prev,
        ...settings,
      }));
    } catch (error) {
      console.error('Failed to load notification settings:', error);
    }
  };

  const handleProfileSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);

    try {
      const response = await apiService.put('/api/v1/user/profile', profileForm);
      
      // Update user in auth store
      const updatedUser: User = {
        ...user!,
        email: profileForm.email,
        full_name: `${profileForm.firstName} ${profileForm.lastName}`.trim(),
        updated_at: new Date().toISOString(),
      };
      setUser(updatedUser);

      toast.success('Profile updated successfully');
    } catch (error: any) {
      toast.error(error.response?.data?.message || 'Failed to update profile');
    } finally {
      setIsLoading(false);
    }
  };

  const handlePasswordSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (passwordForm.newPassword !== passwordForm.confirmPassword) {
      toast.error('New passwords do not match');
      return;
    }

    if (passwordForm.newPassword.length < 8) {
      toast.error('Password must be at least 8 characters long');
      return;
    }

    setIsLoading(true);

    try {
      await apiService.post('/api/v1/user/change-password', {
        currentPassword: passwordForm.currentPassword,
        newPassword: passwordForm.newPassword,
      });

      setPasswordForm({
        currentPassword: '',
        newPassword: '',
        confirmPassword: '',
      });

      toast.success('Password updated successfully');
    } catch (error: any) {
      toast.error(error.response?.data?.message || 'Failed to update password');
    } finally {
      setIsLoading(false);
    }
  };

  const handleBillingSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);

    try {
      await apiService.put('/api/v1/user/billing', billingForm);
      toast.success('Billing information updated successfully');
    } catch (error: any) {
      toast.error(error.response?.data?.message || 'Failed to update billing information');
    } finally {
      setIsLoading(false);
    }
  };

  const handleNotificationSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);

    try {
      await apiService.put('/api/v1/user/notifications', notifications);
      toast.success('Notification settings updated successfully');
    } catch (error: any) {
      toast.error(error.response?.data?.message || 'Failed to update notification settings');
    } finally {
      setIsLoading(false);
    }
  };

  const tabs = [
    { id: 'profile', name: 'Profile', icon: UserIcon },
    { id: 'security', name: 'Security', icon: ShieldCheckIcon },
    { id: 'billing', name: 'Billing', icon: CreditCardIcon },
    { id: 'notifications', name: 'Notifications', icon: BellIcon },
  ] as const;

  return (
    <MainLayout>
      <div className="space-y-6">
        {/* Page Header */}
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Profile Settings</h1>
          <p className="mt-1 text-sm text-gray-500">
            Manage your account settings and preferences
          </p>
        </div>

        {/* Tab Navigation */}
        <div className="border-b border-gray-200">
          <nav className="-mb-px flex space-x-8">
            {tabs.map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`group inline-flex items-center py-2 px-1 border-b-2 font-medium text-sm ${
                  activeTab === tab.id
                    ? 'border-primary-500 text-primary-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                <tab.icon className="w-5 h-5 mr-2" />
                {tab.name}
              </button>
            ))}
          </nav>
        </div>

        {/* Tab Content */}
        <div className="bg-white shadow rounded-lg">
          {activeTab === 'profile' && (
            <form onSubmit={handleProfileSubmit} className="p-6 space-y-6">
              <div>
                <h3 className="text-lg font-medium text-gray-900 mb-4">Personal Information</h3>
                
                <div className="grid grid-cols-1 gap-6 sm:grid-cols-2">
                  <div>
                    <label className="block text-sm font-medium text-gray-700">First Name</label>
                    <input
                      type="text"
                      value={profileForm.firstName}
                      onChange={(e) => setProfileForm(prev => ({ ...prev, firstName: e.target.value }))}
                      className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-primary-500 focus:border-primary-500"
                      required
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700">Last Name</label>
                    <input
                      type="text"
                      value={profileForm.lastName}
                      onChange={(e) => setProfileForm(prev => ({ ...prev, lastName: e.target.value }))}
                      className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-primary-500 focus:border-primary-500"
                      required
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700">Email</label>
                    <input
                      type="email"
                      value={profileForm.email}
                      onChange={(e) => setProfileForm(prev => ({ ...prev, email: e.target.value }))}
                      className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-primary-500 focus:border-primary-500"
                      required
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700">Phone</label>
                    <input
                      type="tel"
                      value={profileForm.phone}
                      onChange={(e) => setProfileForm(prev => ({ ...prev, phone: e.target.value }))}
                      className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-primary-500 focus:border-primary-500"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700">Company Name</label>
                    <input
                      type="text"
                      value={profileForm.companyName}
                      onChange={(e) => setProfileForm(prev => ({ ...prev, companyName: e.target.value }))}
                      className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-primary-500 focus:border-primary-500"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700">Timezone</label>
                    <select
                      value={profileForm.timezone}
                      onChange={(e) => setProfileForm(prev => ({ ...prev, timezone: e.target.value }))}
                      className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-primary-500 focus:border-primary-500"
                    >
                      <option value="UTC">UTC</option>
                      <option value="America/New_York">Eastern Time</option>
                      <option value="America/Chicago">Central Time</option>
                      <option value="America/Denver">Mountain Time</option>
                      <option value="America/Los_Angeles">Pacific Time</option>
                      <option value="Europe/London">London</option>
                      <option value="Europe/Paris">Paris</option>
                      <option value="Asia/Tokyo">Tokyo</option>
                    </select>
                  </div>
                </div>
              </div>

              <div className="flex justify-end">
                <button
                  type="submit"
                  disabled={isLoading}
                  className="bg-primary-600 text-white px-4 py-2 rounded-md hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-primary-500 disabled:opacity-50"
                >
                  {isLoading ? 'Saving...' : 'Save Changes'}
                </button>
              </div>
            </form>
          )}

          {activeTab === 'security' && (
            <form onSubmit={handlePasswordSubmit} className="p-6 space-y-6">
              <div>
                <h3 className="text-lg font-medium text-gray-900 mb-4">Change Password</h3>
                
                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700">Current Password</label>
                    <div className="mt-1 relative">
                      <input
                        type={showPassword.current ? 'text' : 'password'}
                        value={passwordForm.currentPassword}
                        onChange={(e) => setPasswordForm(prev => ({ ...prev, currentPassword: e.target.value }))}
                        className="block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 pr-10 focus:outline-none focus:ring-primary-500 focus:border-primary-500"
                        required
                      />
                      <button
                        type="button"
                        onClick={() => setShowPassword(prev => ({ ...prev, current: !prev.current }))}
                        className="absolute inset-y-0 right-0 pr-3 flex items-center"
                      >
                        {showPassword.current ? (
                          <EyeSlashIcon className="h-4 w-4 text-gray-400" />
                        ) : (
                          <EyeIcon className="h-4 w-4 text-gray-400" />
                        )}
                      </button>
                    </div>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700">New Password</label>
                    <div className="mt-1 relative">
                      <input
                        type={showPassword.new ? 'text' : 'password'}
                        value={passwordForm.newPassword}
                        onChange={(e) => setPasswordForm(prev => ({ ...prev, newPassword: e.target.value }))}
                        className="block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 pr-10 focus:outline-none focus:ring-primary-500 focus:border-primary-500"
                        required
                        minLength={8}
                      />
                      <button
                        type="button"
                        onClick={() => setShowPassword(prev => ({ ...prev, new: !prev.new }))}
                        className="absolute inset-y-0 right-0 pr-3 flex items-center"
                      >
                        {showPassword.new ? (
                          <EyeSlashIcon className="h-4 w-4 text-gray-400" />
                        ) : (
                          <EyeIcon className="h-4 w-4 text-gray-400" />
                        )}
                      </button>
                    </div>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700">Confirm New Password</label>
                    <div className="mt-1 relative">
                      <input
                        type={showPassword.confirm ? 'text' : 'password'}
                        value={passwordForm.confirmPassword}
                        onChange={(e) => setPasswordForm(prev => ({ ...prev, confirmPassword: e.target.value }))}
                        className="block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 pr-10 focus:outline-none focus:ring-primary-500 focus:border-primary-500"
                        required
                        minLength={8}
                      />
                      <button
                        type="button"
                        onClick={() => setShowPassword(prev => ({ ...prev, confirm: !prev.confirm }))}
                        className="absolute inset-y-0 right-0 pr-3 flex items-center"
                      >
                        {showPassword.confirm ? (
                          <EyeSlashIcon className="h-4 w-4 text-gray-400" />
                        ) : (
                          <EyeIcon className="h-4 w-4 text-gray-400" />
                        )}
                      </button>
                    </div>
                  </div>
                </div>

                <div className="mt-4 text-sm text-gray-600">
                  <p>Password requirements:</p>
                  <ul className="list-disc list-inside mt-1 space-y-1">
                    <li>At least 8 characters long</li>
                    <li>Include uppercase and lowercase letters</li>
                    <li>Include at least one number</li>
                    <li>Include at least one special character</li>
                  </ul>
                </div>
              </div>

              <div className="flex justify-end">
                <button
                  type="submit"
                  disabled={isLoading}
                  className="bg-primary-600 text-white px-4 py-2 rounded-md hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-primary-500 disabled:opacity-50"
                >
                  {isLoading ? 'Updating...' : 'Update Password'}
                </button>
              </div>
            </form>
          )}

          {activeTab === 'billing' && (
            <form onSubmit={handleBillingSubmit} className="p-6 space-y-6">
              <div>
                <h3 className="text-lg font-medium text-gray-900 mb-4">Payment Information</h3>
                
                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700">Cardholder Name</label>
                    <input
                      type="text"
                      value={billingForm.cardholderName}
                      onChange={(e) => setBillingForm(prev => ({ ...prev, cardholderName: e.target.value }))}
                      className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-primary-500 focus:border-primary-500"
                      required
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700">Card Number</label>
                    <input
                      type="text"
                      value={billingForm.cardNumber}
                      onChange={(e) => setBillingForm(prev => ({ ...prev, cardNumber: e.target.value }))}
                      placeholder="1234 5678 9012 3456"
                      className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-primary-500 focus:border-primary-500"
                      required
                    />
                  </div>

                  <div className="grid grid-cols-3 gap-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700">Expiry Month</label>
                      <select
                        value={billingForm.expiryMonth}
                        onChange={(e) => setBillingForm(prev => ({ ...prev, expiryMonth: e.target.value }))}
                        className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-primary-500 focus:border-primary-500"
                        required
                      >
                        <option value="">Month</option>
                        {Array.from({ length: 12 }, (_, i) => (
                          <option key={i + 1} value={String(i + 1).padStart(2, '0')}>
                            {String(i + 1).padStart(2, '0')}
                          </option>
                        ))}
                      </select>
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-700">Expiry Year</label>
                      <select
                        value={billingForm.expiryYear}
                        onChange={(e) => setBillingForm(prev => ({ ...prev, expiryYear: e.target.value }))}
                        className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-primary-500 focus:border-primary-500"
                        required
                      >
                        <option value="">Year</option>
                        {Array.from({ length: 10 }, (_, i) => {
                          const year = new Date().getFullYear() + i;
                          return (
                            <option key={year} value={year}>
                              {year}
                            </option>
                          );
                        })}
                      </select>
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-700">CVV</label>
                      <input
                        type="text"
                        value={billingForm.cvv}
                        onChange={(e) => setBillingForm(prev => ({ ...prev, cvv: e.target.value }))}
                        placeholder="123"
                        maxLength={4}
                        className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-primary-500 focus:border-primary-500"
                        required
                      />
                    </div>
                  </div>
                </div>
              </div>

              <div>
                <h4 className="text-md font-medium text-gray-900 mb-4">Billing Address</h4>
                
                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700">Street Address</label>
                    <input
                      type="text"
                      value={billingForm.billingAddress.street}
                      onChange={(e) => setBillingForm(prev => ({
                        ...prev,
                        billingAddress: { ...prev.billingAddress, street: e.target.value }
                      }))}
                      className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-primary-500 focus:border-primary-500"
                      required
                    />
                  </div>

                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700">City</label>
                      <input
                        type="text"
                        value={billingForm.billingAddress.city}
                        onChange={(e) => setBillingForm(prev => ({
                          ...prev,
                          billingAddress: { ...prev.billingAddress, city: e.target.value }
                        }))}
                        className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-primary-500 focus:border-primary-500"
                        required
                      />
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-700">State</label>
                      <input
                        type="text"
                        value={billingForm.billingAddress.state}
                        onChange={(e) => setBillingForm(prev => ({
                          ...prev,
                          billingAddress: { ...prev.billingAddress, state: e.target.value }
                        }))}
                        className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-primary-500 focus:border-primary-500"
                        required
                      />
                    </div>
                  </div>

                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700">Postal Code</label>
                      <input
                        type="text"
                        value={billingForm.billingAddress.postalCode}
                        onChange={(e) => setBillingForm(prev => ({
                          ...prev,
                          billingAddress: { ...prev.billingAddress, postalCode: e.target.value }
                        }))}
                        className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-primary-500 focus:border-primary-500"
                        required
                      />
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-700">Country</label>
                      <select
                        value={billingForm.billingAddress.country}
                        onChange={(e) => setBillingForm(prev => ({
                          ...prev,
                          billingAddress: { ...prev.billingAddress, country: e.target.value }
                        }))}
                        className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-primary-500 focus:border-primary-500"
                        required
                      >
                        <option value="US">United States</option>
                        <option value="CA">Canada</option>
                        <option value="GB">United Kingdom</option>
                        <option value="AU">Australia</option>
                        <option value="DE">Germany</option>
                        <option value="FR">France</option>
                      </select>
                    </div>
                  </div>
                </div>
              </div>

              <div className="flex justify-end">
                <button
                  type="submit"
                  disabled={isLoading}
                  className="bg-primary-600 text-white px-4 py-2 rounded-md hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-primary-500 disabled:opacity-50"
                >
                  {isLoading ? 'Saving...' : 'Save Payment Info'}
                </button>
              </div>
            </form>
          )}

          {activeTab === 'notifications' && (
            <form onSubmit={handleNotificationSubmit} className="p-6 space-y-6">
              <div>
                <h3 className="text-lg font-medium text-gray-900 mb-4">Email Notifications</h3>
                
                <div className="space-y-4">
                  {Object.entries(notifications.emailNotifications).map(([key, value]) => (
                    <div key={key} className="flex items-center justify-between">
                      <div>
                        <h4 className="text-sm font-medium text-gray-900 capitalize">
                          {key.replace(/([A-Z])/g, ' $1').trim()}
                        </h4>
                        <p className="text-sm text-gray-500">
                          {key === 'orderUpdates' && 'Get notified when your orders are updated'}
                          {key === 'integrationAlerts' && 'Receive alerts about integration issues'}
                          {key === 'systemMaintenance' && 'Important system maintenance notifications'}
                          {key === 'promotions' && 'Marketing emails and promotional offers'}
                        </p>
                      </div>
                      <button
                        type="button"
                        onClick={() => setNotifications(prev => ({
                          ...prev,
                          emailNotifications: {
                            ...prev.emailNotifications,
                            [key]: !value,
                          },
                        }))}
                        className={`relative inline-flex h-6 w-11 flex-shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2 ${
                          value ? 'bg-primary-600' : 'bg-gray-200'
                        }`}
                      >
                        <span
                          className={`pointer-events-none inline-block h-5 w-5 transform rounded-full bg-white shadow ring-0 transition duration-200 ease-in-out ${
                            value ? 'translate-x-5' : 'translate-x-0'
                          }`}
                        />
                      </button>
                    </div>
                  ))}
                </div>
              </div>

              <div>
                <h3 className="text-lg font-medium text-gray-900 mb-4">Push Notifications</h3>
                
                <div className="space-y-4">
                  {Object.entries(notifications.pushNotifications).map(([key, value]) => (
                    <div key={key} className="flex items-center justify-between">
                      <div>
                        <h4 className="text-sm font-medium text-gray-900 capitalize">
                          {key.replace(/([A-Z])/g, ' $1').trim()}
                        </h4>
                        <p className="text-sm text-gray-500">
                          {key === 'orderCompleted' && 'Instant notifications when orders are completed'}
                          {key === 'integrationErrors' && 'Real-time alerts for integration errors'}
                          {key === 'lowInventory' && 'Alerts when product inventory is low'}
                        </p>
                      </div>
                      <button
                        type="button"
                        onClick={() => setNotifications(prev => ({
                          ...prev,
                          pushNotifications: {
                            ...prev.pushNotifications,
                            [key]: !value,
                          },
                        }))}
                        className={`relative inline-flex h-6 w-11 flex-shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2 ${
                          value ? 'bg-primary-600' : 'bg-gray-200'
                        }`}
                      >
                        <span
                          className={`pointer-events-none inline-block h-5 w-5 transform rounded-full bg-white shadow ring-0 transition duration-200 ease-in-out ${
                            value ? 'translate-x-5' : 'translate-x-0'
                          }`}
                        />
                      </button>
                    </div>
                  ))}
                </div>
              </div>

              <div className="flex justify-end">
                <button
                  type="submit"
                  disabled={isLoading}
                  className="bg-primary-600 text-white px-4 py-2 rounded-md hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-primary-500 disabled:opacity-50"
                >
                  {isLoading ? 'Saving...' : 'Save Preferences'}
                </button>
              </div>
            </form>
          )}
        </div>
      </div>
    </MainLayout>
  );
};

export default Profile;