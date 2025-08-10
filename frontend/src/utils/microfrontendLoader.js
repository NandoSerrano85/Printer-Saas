// utils/microfrontendLoader.js
class MicrofrontendLoader {
  constructor() {
    this.loadedMicrofrontends = new Map();
  }

  async loadMicrofrontend(name, url, tenant) {
    const key = `${name}-${tenant}`;
    
    if (this.loadedMicrofrontends.has(key)) {
      return this.loadedMicrofrontends.get(key);
    }

    try {
      const module = await import(/* @vite-ignore */ `${url}/${name}.js`);
      this.loadedMicrofrontends.set(key, module);
      return module;
    } catch (error) {
      logger.error(`Failed to load microfrontend: ${name}`, { error, tenant });
      throw error;
    }
  }

  async loadTenantSpecificComponent(componentName, tenant) {
    const tenantComponentUrl = `/tenant-components/${tenant}`;
    
    try {
      return await this.loadMicrofrontend(componentName, tenantComponentUrl, tenant);
    } catch (error) {
      // Fallback to default component
      logger.warn(`Tenant-specific component not found, using default`, { 
        component: componentName, 
        tenant 
      });
      return await this.loadMicrofrontend(componentName, '/default-components', tenant);
    }
  }
}

export const microfrontendLoader = new MicrofrontendLoader();

// Dynamic Component Loader Hook
export const useDynamicComponent = (componentName) => {
  const { tenant } = useTenant();
  const [Component, setComponent] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    let mounted = true;

    const loadComponent = async () => {
      try {
        setLoading(true);
        const module = await microfrontendLoader.loadTenantSpecificComponent(
          componentName, 
          tenant?.id
        );
        
        if (mounted) {
          setComponent(() => module.default);
          setError(null);
        }
      } catch (err) {
        if (mounted) {
          setError(err);
          logger.error('Failed to load dynamic component', { 
            component: componentName, 
            tenant: tenant?.id, 
            error: err 
          });
        }
      } finally {
        if (mounted) {
          setLoading(false);
        }
      }
    };

    if (tenant?.id) {
      loadComponent();
    }

    return () => {
      mounted = false;
    };
  }, [componentName, tenant?.id]);

  return { Component, loading, error };
};