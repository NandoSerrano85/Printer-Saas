import React, { useEffect, useState } from 'react';
import { useRouter } from 'next/router';
import apiService from '@/services/api';
import toast from 'react-hot-toast';

export default function ConnectEtsy() {
  const router = useRouter();
  const [oauthData, setOauthData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchOAuthData = async () => {
      try {
        const response = await apiService.getEtsyOAuthData();
        setOauthData(response);
      } catch (err: any) {
        setError('Failed to load OAuth configuration');
        console.error('Error fetching OAuth data:', err);
      } finally {
        setLoading(false);
      }
    };
    fetchOAuthData();
  }, []);

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-purple-500 to-pink-500 px-4">
        <div className="bg-white rounded-xl shadow-lg p-6 sm:p-8 w-full max-w-md text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-purple-600 mx-auto mb-4"></div>
          <p className="text-sm sm:text-base">Loading...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-purple-500 to-pink-500 px-4">
        <div className="bg-white rounded-xl shadow-lg p-6 sm:p-8 w-full max-w-md text-center">
          <p className="text-red-600 text-sm sm:text-base mb-4">{error}</p>
          <button
            onClick={() => router.push('/integrations')}
            className="bg-gray-500 hover:bg-gray-600 text-white font-bold py-2 px-4 rounded-lg transition-colors text-sm"
          >
            Back to Integrations
          </button>
        </div>
      </div>
    );
  }

  const authUrl = oauthData ? 
    `${oauthData.oauthConnectUrl || 'https://www.etsy.com/oauth/connect'}?response_type=${oauthData.responseType || 'code'}&redirect_uri=${encodeURIComponent(oauthData.redirectUri)}&scope=${encodeURIComponent(oauthData.scopes || 'listings_w listings_r shops_r shops_w transactions_r')}&client_id=${oauthData.clientId}&state=${oauthData.state}&code_challenge=${oauthData.codeChallenge}&code_challenge_method=${oauthData.codeChallengeMethod || 'S256'}` : 
    '#';

  const handleConnect = () => {
    if (authUrl === '#') {
      toast.error('OAuth configuration not available');
      return;
    }
    
    // Open OAuth URL in current window
    window.location.href = authUrl;
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-purple-500 to-pink-500 px-4">
      <div className="bg-white rounded-xl shadow-lg p-6 sm:p-8 w-full max-w-md text-center">
        {/* Etsy Logo */}
        <div className="mx-auto h-16 w-16 flex items-center justify-center rounded-full bg-orange-100 mb-4">
          <svg className="h-10 w-10 text-orange-600" fill="currentColor" viewBox="0 0 24 24">
            <path d="M7.93 11.84l3.11.78c.19.05.36.14.48.26.11.12.18.27.18.44 0 .33-.27.6-.6.6H5.7c-.33 0-.6-.27-.6-.6s.27-.6.6-.6h4.31l-2.08-.52v7.6c0 .33.27.6.6.6s.6-.27.6-.6v-7.96z"/>
            <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm0 18c-4.41 0-8-3.59-8-8s3.59-8 8-8 8 3.59 8 8-3.59 8-8 8z"/>
          </svg>
        </div>
        
        <h1 className="text-xl sm:text-2xl font-bold mb-4 text-gray-900">Connect Your Etsy Store</h1>
        <p className="mb-6 text-gray-700 text-sm sm:text-base">
          To get started, connect your Etsy store to enable automated product management and order processing.
        </p>
        
        <div className="mb-6">
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-4">
            <h3 className="text-sm font-medium text-blue-800 mb-2">What this enables:</h3>
            <ul className="text-sm text-blue-700 space-y-1">
              <li>• Automatic product listing management</li>
              <li>• Order synchronization</li>
              <li>• Inventory tracking</li>
              <li>• Analytics and reporting</li>
            </ul>
          </div>
        </div>
        
        <button
          onClick={handleConnect}
          disabled={!oauthData || authUrl === '#'}
          className="w-full bg-orange-500 hover:bg-orange-600 disabled:bg-gray-400 text-white font-bold py-3 px-6 rounded-lg transition-colors text-sm sm:text-base mb-4"
        >
          Connect Etsy Store
        </button>
        
        <button
          onClick={() => router.push('/integrations')}
          className="w-full bg-gray-500 hover:bg-gray-600 text-white font-bold py-2 px-4 rounded-lg transition-colors text-sm"
        >
          Cancel
        </button>
        
        {oauthData && (
          <div className="mt-6 p-3 bg-gray-50 border rounded text-xs text-gray-600">
            <p className="font-medium mb-1">Development Info:</p>
            <p>Client ID: {oauthData.clientId?.substring(0, 8)}...</p>
            <p>Redirect: {oauthData.redirectUri}</p>
          </div>
        )}
      </div>
    </div>
  );
}