import React, { useState, useEffect } from 'react';
import { HealthMetrics } from '@/types';

interface HealthCheckResults {
  api: boolean;
  tenant: boolean;
  storage: boolean;
  timestamp: string;
}

interface TenantInfo {
  id: string;
  config?: Record<string, any>;
}

class HealthMonitor {
  private checks: Map<string, HealthCheckResults> = new Map();
  private monitoringInterval: NodeJS.Timeout | null = null;
  private apiBaseUrl: string;

  constructor() {
    this.apiBaseUrl = process.env.REACT_APP_API_BASE_URL || 'http://localhost:8000';
    this.startMonitoring();
  }

  async checkApiHealth(): Promise<boolean> {
    try {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 5000);

      const response = await fetch(`${this.apiBaseUrl}/health`, {
        method: 'GET',
        signal: controller.signal,
        headers: {
          'Content-Type': 'application/json',
        },
      });

      clearTimeout(timeoutId);
      return response.ok;
    } catch (error) {
      console.error('API health check failed:', error);
      return false;
    }
  }

  async checkTenantConfig(): Promise<boolean> {
    try {
      const tenant = this.getCurrentTenant();
      return !!(tenant?.id);
    } catch (error) {
      console.error('Tenant config check failed:', error);
      return false;
    }
  }

  checkLocalStorage(): boolean {
    if (typeof Storage === 'undefined') {
      return false;
    }

    try {
      const testKey = '__storage_test__';
      localStorage.setItem(testKey, 'test');
      const retrieved = localStorage.getItem(testKey);
      localStorage.removeItem(testKey);
      return retrieved === 'test';
    } catch (error) {
      console.error('Local storage check failed:', error);
      return false;
    }
  }

  private getCurrentTenant(): TenantInfo | null {
    if (typeof window === 'undefined') {
      return null;
    }

    try {
      // Check localStorage first
      const storedTenant = localStorage.getItem('current_tenant');
      if (storedTenant) {
        return { id: storedTenant };
      }

      // Extract from hostname
      const hostname = window.location.hostname;
      const subdomain = hostname.split('.')[0];
      
      if (['localhost', '127', '0', 'www'].includes(subdomain) || 
          /^\d+$/.test(subdomain)) {
        return { id: 'demo' };
      }
      
      return { id: subdomain };
    } catch (error) {
      console.error('Error getting current tenant:', error);
      return null;
    }
  }

  async performHealthChecks(): Promise<HealthCheckResults> {
    const results: HealthCheckResults = {
      api: await this.checkApiHealth(),
      tenant: await this.checkTenantConfig(),
      storage: this.checkLocalStorage(),
      timestamp: new Date().toISOString(),
    };

    this.checks.set('latest', results);
    this.checks.set(Date.now().toString(), results);

    // Keep only last 10 checks
    if (this.checks.size > 11) { // 10 + 'latest'
      const keys = Array.from(this.checks.keys()).filter(k => k !== 'latest');
      keys.sort();
      this.checks.delete(keys[0]);
    }

    return results;
  }

  startMonitoring(): void {
    if (this.monitoringInterval) {
      clearInterval(this.monitoringInterval);
    }

    // Perform initial check
    this.performHealthChecks();

    // Perform health checks every 2 minutes
    this.monitoringInterval = setInterval(() => {
      this.performHealthChecks();
    }, 120000);
  }

  stopMonitoring(): void {
    if (this.monitoringInterval) {
      clearInterval(this.monitoringInterval);
      this.monitoringInterval = null;
    }
  }

  getHealthStatus(): HealthCheckResults | null {
    return this.checks.get('latest') || null;
  }

  getHealthHistory(): HealthCheckResults[] {
    const keys = Array.from(this.checks.keys()).filter(k => k !== 'latest');
    return keys
      .sort()
      .map(key => this.checks.get(key)!)
      .filter(Boolean);
  }

  isHealthy(): boolean {
    const health = this.getHealthStatus();
    if (!health) return false;

    return health.api && health.tenant && health.storage;
  }

  getHealthMetrics(): HealthMetrics {
    const health = this.getHealthStatus();
    const isHealthy = this.isHealthy();

    return {
      responseTime: 0, // TODO: Implement actual response time measurement
      status: isHealthy ? 'healthy' : 'degraded',
      lastCheck: health ? new Date(health.timestamp).getTime() : 0,
    };
  }
}

export const healthMonitor = new HealthMonitor();

// Health Status Component
interface HealthStatusProps {
  showDetails?: boolean;
  className?: string;
}

export const HealthStatus: React.FC<HealthStatusProps> = ({ 
  showDetails = false, 
  className = '' 
}) => {
  const [health, setHealth] = useState<HealthCheckResults | null>(null);
  const [isExpanded, setIsExpanded] = useState(false);

  useEffect(() => {
    const updateHealth = () => {
      setHealth(healthMonitor.getHealthStatus());
    };

    updateHealth();
    const interval = setInterval(updateHealth, 30000); // Update every 30s

    return () => clearInterval(interval);
  }, []);

  if (!health) return null;

  const allHealthy = health.api && health.tenant && health.storage;
  const healthyCount = [health.api, health.tenant, health.storage].filter(Boolean).length;

  return (
    <div className={`fixed bottom-4 right-4 ${className}`}>
      <div 
        className={`p-2 rounded-lg text-sm shadow-lg cursor-pointer transition-all ${
          allHealthy 
            ? 'bg-green-100 text-green-800 border border-green-200' 
            : 'bg-red-100 text-red-800 border border-red-200'
        } ${isExpanded ? 'w-64' : 'w-auto'}`}
        onClick={() => showDetails && setIsExpanded(!isExpanded)}
      >
        <div className="flex items-center gap-2">
          <div className={`w-2 h-2 rounded-full ${
            allHealthy ? 'bg-green-500' : 'bg-red-500'
          }`} />
          <span>
            System Status: {allHealthy ? 'Healthy' : `Issues (${healthyCount}/3)`}
          </span>
          {showDetails && (
            <svg 
              className={`w-4 h-4 transition-transform ${isExpanded ? 'rotate-180' : ''}`}
              fill="none" 
              stroke="currentColor" 
              viewBox="0 0 24 24"
            >
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
            </svg>
          )}
        </div>
        
        {showDetails && isExpanded && (
          <div className="mt-2 space-y-1 text-xs">
            <div className="flex justify-between">
              <span>API:</span>
              <span className={health.api ? 'text-green-600' : 'text-red-600'}>
                {health.api ? '✓' : '✗'}
              </span>
            </div>
            <div className="flex justify-between">
              <span>Tenant:</span>
              <span className={health.tenant ? 'text-green-600' : 'text-red-600'}>
                {health.tenant ? '✓' : '✗'}
              </span>
            </div>
            <div className="flex justify-between">
              <span>Storage:</span>
              <span className={health.storage ? 'text-green-600' : 'text-red-600'}>
                {health.storage ? '✓' : '✗'}
              </span>
            </div>
            <div className="text-gray-500 border-t pt-1">
              Last check: {new Date(health.timestamp).toLocaleTimeString()}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

// Hook for using health status in components
export const useHealthStatus = () => {
  const [health, setHealth] = useState<HealthCheckResults | null>(null);

  useEffect(() => {
    const updateHealth = () => {
      setHealth(healthMonitor.getHealthStatus());
    };

    updateHealth();
    const interval = setInterval(updateHealth, 30000);

    return () => clearInterval(interval);
  }, []);

  return {
    health,
    isHealthy: healthMonitor.isHealthy(),
    metrics: healthMonitor.getHealthMetrics(),
    history: healthMonitor.getHealthHistory(),
  };
};

export default HealthMonitor;