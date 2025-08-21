import { useEffect, useRef, useState } from 'react';
import { useRouter } from 'next/router';
import apiService from '@/services/api';
import toast from 'react-hot-toast';

export default function OAuthRedirect() {
  const router = useRouter();
  const processed = useRef(false);
  const [status, setStatus] = useState('processing');
  const [message, setMessage] = useState('Connecting to Etsy...');

  useEffect(() => {
    const processOAuth = async () => {
      // Check if we've already processed this OAuth callback
      if (processed.current || sessionStorage?.getItem('etsy_oauth_completed')) {
        return;
      }

      const urlParams = new URLSearchParams(window.location.search);
      const code = urlParams.get('code');
      const state = urlParams.get('state');
      const error = urlParams.get('error');

      if (error) {
        setStatus('error');
        setMessage(`OAuth error: ${error}`);
        toast.error(`Connection failed: ${error}`);
        setTimeout(() => {
          router.push('/connect-etsy?error=oauth_error');
        }, 2000);
        return;
      }

      if (!code) {
        setStatus('error');
        setMessage('No authorization code received');
        toast.error('No authorization code received');
        setTimeout(() => {
          router.push('/connect-etsy?error=no_code');
        }, 2000);
        return;
      }

      processed.current = true;
      
      try {
        setMessage('Exchanging authorization code for access token...');
        const result = await apiService.handleEtsyOAuthCallback(code);
        
        if (result.success) {
          setStatus('success');
          setMessage('Successfully connected to Etsy!');
          toast.success('Etsy connection successful!');
          
          // Clear the completion flag when navigating away
          sessionStorage?.removeItem('etsy_oauth_completed');
          
          // Redirect to integrations page with success message
          setTimeout(() => {
            router.push('/integrations?connected=etsy');
          }, 1500);
        } else {
          setStatus('error');
          setMessage(result.message || 'Connection failed');
          toast.error(result.message || 'Connection failed');
          setTimeout(() => {
            router.push('/connect-etsy?error=oauth_failed');
          }, 2000);
        }
      } catch (error: any) {
        console.error('OAuth callback error:', error);
        setStatus('error');
        setMessage('Connection failed due to an unexpected error');
        toast.error('Connection failed');
        setTimeout(() => {
          router.push('/connect-etsy?error=callback_error');
        }, 2000);
      }
    };

    // Only process if we have the router query
    if (router.isReady) {
      processOAuth();
    }
  }, [router.isReady, router.query]);

  const getStatusIcon = () => {
    switch (status) {
      case 'processing':
        return (
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-orange-600 mx-auto"></div>
        );
      case 'success':
        return (
          <div className="mx-auto h-12 w-12 flex items-center justify-center rounded-full bg-green-100">
            <svg className="h-8 w-8 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
            </svg>
          </div>
        );
      case 'error':
        return (
          <div className="mx-auto h-12 w-12 flex items-center justify-center rounded-full bg-red-100">
            <svg className="h-8 w-8 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </div>
        );
      default:
        return null;
    }
  };

  const getStatusColor = () => {
    switch (status) {
      case 'success':
        return 'text-green-600';
      case 'error':
        return 'text-red-600';
      default:
        return 'text-gray-600';
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-purple-500 to-pink-500 px-4">
      <div className="bg-white rounded-xl shadow-lg p-8 w-full max-w-md text-center">
        {/* Etsy Logo */}
        <div className="mx-auto h-16 w-16 flex items-center justify-center rounded-full bg-orange-100 mb-6">
          <svg className="h-10 w-10 text-orange-600" fill="currentColor" viewBox="0 0 24 24">
            <path d="M7.93 11.84l3.11.78c.19.05.36.14.48.26.11.12.18.27.18.44 0 .33-.27.6-.6.6H5.7c-.33 0-.6-.27-.6-.6s.27-.6.6-.6h4.31l-2.08-.52v7.6c0 .33.27.6.6.6s.6-.27.6-.6v-7.96z"/>
            <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm0 18c-4.41 0-8-3.59-8-8s3.59-8 8-8 8 3.59 8 8-3.59 8-8 8z"/>
          </svg>
        </div>

        <h1 className="text-2xl font-bold mb-4 text-gray-900">Etsy Integration</h1>
        
        {/* Status Icon */}
        <div className="mb-6">
          {getStatusIcon()}
        </div>
        
        {/* Status Message */}
        <p className={`text-lg mb-6 ${getStatusColor()}`}>
          {message}
        </p>
        
        {status === 'processing' && (
          <div className="text-sm text-gray-500">
            Please wait while we complete the connection...
          </div>
        )}
        
        {status === 'error' && (
          <div className="text-sm text-gray-500">
            Redirecting back to connection page...
          </div>
        )}
        
        {status === 'success' && (
          <div className="text-sm text-gray-500">
            Redirecting to integrations page...
          </div>
        )}
      </div>
    </div>
  );
}