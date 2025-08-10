import React from 'react';
import { useTenant } from '../../../contexts/TenantContext';
import { Sidebar } from '../Navigation/Sidebar';
import { Header } from './Header';
import { LoadingSpinner } from '../UI/LoadingSpinner';

export const AppLayout = ({ children }) => {
    const { tenant, isLoading } = useTenant();
    // Check if tenant data is still loading
    if (isLoading) {
        return <LoadingSpinner />;
    }
    return (
        <div className="min-h-screen bg-gray-50">
            <Header tenant={tenant} />
            <div className="flex">
                <Sidebar tenant={tenant} />
                <main className="flex-1 p-6">
                    <div className="max-w-7xl mx-auto">
                        {children}
                    </div>
                </main>
            </div>
        </div>
    );
};