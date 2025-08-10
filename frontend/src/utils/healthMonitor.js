// utils/healthMonitor.js
class HealthMonitor {
  constructor() {
    this.checks = new Map();
    this.startMonitoring();
  }

  async checkApiHealth() {
    try {
      const response = await fetch(`${config.API_BASE_URL}/health`, {
        method: 'GET',
        timeout: 5000,
      });
      return response.ok;
    } catch (error) {
      console.error('API health check failed:', error);
      return false;
    }
  }

  async checkTenantConfig() {
    const tenant = this.getCurrentTenant();
    return !!(tenant?.id && tenant?.config);
  }

  async performHealthChecks() {
    const results = {
      api: await this.checkApiHealth(),
      tenant: await this.checkTenantConfig(),
      storage: this.checkLocalStorage(),
      timestamp: new Date().toISOString(),
    };

    this.checks.set('latest', results);
    return results;
  }

  checkLocalStorage() {
    try {
      const testKey = '__storage_test__';
      localStorage.setItem(testKey, 'test');
      localStorage.removeItem(testKey);
      return true;
    } catch (error) {
      return false;
    }
  }

  startMonitoring() {
    // Perform health checks every 2 minutes
    setInterval(() => {
      this.performHealthChecks();
    }, 120000);
  }

  getHealthStatus() {
    return this.checks.get('latest') || null;
  }
}

export const healthMonitor = new HealthMonitor();

// Health Status Component
export const HealthStatus = () => {
  const [health, setHealth] = useState(null);

  useEffect(() => {
    const updateHealth = () => {
      setHealth(healthMonitor.getHealthStatus());
    };

    updateHealth();
    const interval = setInterval(updateHealth, 30000); // Update every 30s

    return () => clearInterval(interval);
  }, []);

  if (!health) return null;

  const allHealthy = Object.values(health).every(status => 
    typeof status === 'boolean' ? status : true
  );

  return (
    <div className={`fixed bottom-4 right-4 p-2 rounded-lg text-sm ${
      allHealthy ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
    }`}>
      <div className="flex items-center gap-2">
        <div className={`w-2 h-2 rounded-full ${
          allHealthy ? 'bg-green-500' : 'bg-red-500'
        }`} />
        System Status: {allHealthy ? 'Healthy' : 'Issues Detected'}
      </div>
    </div>
  );
};