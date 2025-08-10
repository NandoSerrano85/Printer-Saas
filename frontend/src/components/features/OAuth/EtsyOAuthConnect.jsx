import { useState, useEffect } from 'react';
import { useTenant } from '../../../contexts/TenantContext';
import { apiService } from '../../../services/apiService';

export const EtsyOAuthConnect = () => {
  const { tenant } = useTenant();
  const [isConnected, setIsConnected] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
    const handleConnect = async () => {
        setIsLoading(true);
        try {
        const oauthData = await apiService.getOAuthConfig();
        // Build OAuth URL with tenant-specific redirect
        const params = new URLSearchParams({
            client_id: oauthData.client_id,
            redirect_uri: `${window.location.origin}/oauth/redirect`,
            scope: oauthData.scope,
            state: tenant.id, // Include tenant ID in state
            response_type: 'code',
            code_challenge_method: 'S256',
            code_challenge: oauthData.code_challenge,
        });
        window.location.href = `https://www.etsy.com/oauth/connect?${params}`;
        } catch (error) {
        console.error('OAuth connection failed:', error);
        } finally {
        setIsLoading(false);
        }
    };
    return (
        <div className="bg-white rounded-lg shadow-md p-6">
            <h2 className="text-2xl font-bold mb-4">Connect Your Etsy Shop</h2>
            {isConnected ? (
                <div className="text-green-600">
                    Successfully connected to Etsy!!
                </div>
            ) : (
                <button
                    onClick={handleConnect}
                    disabled={isLoading}
                    className="bg-primary text-white px-6 py-3 rounded-lg hover:bg-primary-dark disabled:opacity-50"
                >
                    {isLoading ? 'Connecting...' : 'Connect to Etsy'}
                </button>
            )}
        </div>
    );
};
