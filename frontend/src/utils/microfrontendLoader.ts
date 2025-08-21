import { MicrofrontendConfig } from '@/types';

interface MicrofrontendModule {
  mount: (element: HTMLElement, props?: any) => void;
  unmount: (element: HTMLElement) => void;
  [key: string]: any;
}

interface LoadedMicrofrontend {
  config: MicrofrontendConfig;
  module: MicrofrontendModule;
  container?: any; // Webpack Module Federation container
}

class MicrofrontendLoader {
  private loadedMicrofrontends: Map<string, LoadedMicrofrontend> = new Map();
  private loadingPromises: Map<string, Promise<MicrofrontendModule>> = new Map();

  async loadMicrofrontend(config: MicrofrontendConfig): Promise<MicrofrontendModule> {
    // Return cached module if already loaded
    const cached = this.loadedMicrofrontends.get(config.name);
    if (cached) {
      return cached.module;
    }

    // Return existing loading promise if already loading
    const loadingPromise = this.loadingPromises.get(config.name);
    if (loadingPromise) {
      return loadingPromise;
    }

    // Start loading the microfrontend
    const promise = this.loadMicrofrontendModule(config);
    this.loadingPromises.set(config.name, promise);

    try {
      const module = await promise;
      
      // Cache the loaded module
      this.loadedMicrofrontends.set(config.name, {
        config,
        module,
      });

      // Remove from loading promises
      this.loadingPromises.delete(config.name);

      return module;
    } catch (error) {
      // Remove from loading promises on error
      this.loadingPromises.delete(config.name);
      throw error;
    }
  }

  private async loadMicrofrontendModule(config: MicrofrontendConfig): Promise<MicrofrontendModule> {
    try {
      // Check if this is a Module Federation setup
      if (this.isModuleFederationConfig(config)) {
        return this.loadModuleFederationMicrofrontend(config);
      }

      // Fallback to loading as a regular script
      return this.loadScriptMicrofrontend(config);
    } catch (error) {
      console.error(`Failed to load microfrontend ${config.name}:`, error);
      throw new Error(`Unable to load microfrontend: ${config.name}`);
    }
  }

  private isModuleFederationConfig(config: MicrofrontendConfig): boolean {
    return !!(config.scope && config.module);
  }

  private async loadModuleFederationMicrofrontend(config: MicrofrontendConfig): Promise<MicrofrontendModule> {
    if (typeof window === 'undefined') {
      throw new Error('Module Federation requires browser environment');
    }

    // Load the remote container
    await this.loadRemoteContainer(config.url, config.scope!);

    // Get the container
    const container = (window as any)[config.scope!];
    if (!container) {
      throw new Error(`Remote container not found: ${config.scope}`);
    }

    // Initialize the container
    await container.init((window as any).__webpack_share_scopes__?.default);

    // Get the module factory
    const factory = await container.get(config.module!);
    const module = factory();

    if (!module.mount || typeof module.mount !== 'function') {
      throw new Error(`Microfrontend ${config.name} does not export a mount function`);
    }

    return module;
  }

  private loadRemoteContainer(url: string, scope: string): Promise<void> {
    return new Promise((resolve, reject) => {
      // Check if already loaded
      if ((window as any)[scope]) {
        resolve();
        return;
      }

      const script = document.createElement('script');
      script.type = 'text/javascript';
      script.async = true;
      script.src = url;
      
      script.onload = () => {
        // Verify the container is available
        if ((window as any)[scope]) {
          resolve();
        } else {
          reject(new Error(`Container ${scope} not found after loading ${url}`));
        }
      };

      script.onerror = () => {
        reject(new Error(`Failed to load remote container: ${url}`));
      };

      document.head.appendChild(script);
    });
  }

  private async loadScriptMicrofrontend(config: MicrofrontendConfig): Promise<MicrofrontendModule> {
    // For non-Module Federation microfrontends, we need to load the script
    // and expect it to register itself in a global registry
    await this.loadScript(config.url);

    // Look for the module in a global registry
    const globalRegistry = (window as any).__MICROFRONTEND_REGISTRY__;
    if (!globalRegistry || !globalRegistry[config.name]) {
      throw new Error(`Microfrontend ${config.name} not found in global registry`);
    }

    const module = globalRegistry[config.name];
    if (!module.mount || typeof module.mount !== 'function') {
      throw new Error(`Microfrontend ${config.name} does not export a mount function`);
    }

    return module;
  }

  private loadScript(url: string): Promise<void> {
    return new Promise((resolve, reject) => {
      // Check if script is already loaded
      const existingScript = document.querySelector(`script[src="${url}"]`);
      if (existingScript) {
        resolve();
        return;
      }

      const script = document.createElement('script');
      script.type = 'text/javascript';
      script.async = true;
      script.src = url;
      
      script.onload = () => resolve();
      script.onerror = () => reject(new Error(`Failed to load script: ${url}`));

      document.head.appendChild(script);
    });
  }

  getMicrofrontend(name: string): LoadedMicrofrontend | null {
    return this.loadedMicrofrontends.get(name) || null;
  }

  unloadMicrofrontend(name: string): boolean {
    const microfrontend = this.loadedMicrofrontends.get(name);
    if (!microfrontend) {
      return false;
    }

    // Call unmount if available
    if (microfrontend.module.unmount) {
      try {
        // We don't have the element here, so this is just cleanup
        microfrontend.module.unmount(document.createElement('div'));
      } catch (error) {
        console.warn(`Error during unmount of ${name}:`, error);
      }
    }

    // Remove from cache
    this.loadedMicrofrontends.delete(name);
    return true;
  }

  preloadMicrofrontends(configs: MicrofrontendConfig[]): Promise<PromiseSettledResult<MicrofrontendModule>[]> {
    const promises = configs.map(config => 
      this.loadMicrofrontend(config).catch(error => {
        console.warn(`Failed to preload microfrontend ${config.name}:`, error);
        throw error;
      })
    );

    return Promise.allSettled(promises);
  }

  getLoadedMicrofrontends(): string[] {
    return Array.from(this.loadedMicrofrontends.keys());
  }

  isLoaded(name: string): boolean {
    return this.loadedMicrofrontends.has(name);
  }

  isLoading(name: string): boolean {
    return this.loadingPromises.has(name);
  }

  clearCache(): void {
    this.loadedMicrofrontends.clear();
    this.loadingPromises.clear();
  }

  // Create a wrapper component for React
  createMicrofrontendComponent(config: MicrofrontendConfig) {
    return React.forwardRef<HTMLDivElement, { [key: string]: any }>((props, ref) => {
      const containerRef = React.useRef<HTMLDivElement>(null);
      const [isLoaded, setIsLoaded] = React.useState(false);
      const [error, setError] = React.useState<Error | null>(null);

      React.useImperativeHandle(ref, () => containerRef.current!);

      React.useEffect(() => {
        let mounted = true;

        const loadAndMount = async () => {
          try {
            setError(null);
            const module = await this.loadMicrofrontend(config);
            
            if (mounted && containerRef.current) {
              await module.mount(containerRef.current, props);
              setIsLoaded(true);
            }
          } catch (err) {
            if (mounted) {
              setError(err instanceof Error ? err : new Error(String(err)));
            }
          }
        };

        loadAndMount();

        return () => {
          mounted = false;
          
          // Unmount the microfrontend
          const microfrontend = this.getMicrofrontend(config.name);
          if (microfrontend?.module.unmount && containerRef.current) {
            try {
              microfrontend.module.unmount(containerRef.current);
            } catch (err) {
              console.warn(`Error unmounting ${config.name}:`, err);
            }
          }
        };
      }, [config.name, config.url]);

      if (error) {
        return (
          <div className="p-4 border border-red-300 rounded bg-red-50 text-red-800">
            <h3 className="font-semibold">Failed to load microfrontend</h3>
            <p className="text-sm">{error.message}</p>
          </div>
        );
      }

      if (!isLoaded) {
        return (
          <div className="p-4 flex items-center justify-center">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
            <span className="ml-2">Loading {config.name}...</span>
          </div>
        );
      }

      return <div ref={containerRef} className="w-full h-full" />;
    });
  }
}

export const microfrontendLoader = new MicrofrontendLoader();

// React hook for loading microfrontends
export const useMicrofrontend = (config: MicrofrontendConfig) => {
  const [module, setModule] = React.useState<MicrofrontendModule | null>(null);
  const [isLoading, setIsLoading] = React.useState<boolean>(false);
  const [error, setError] = React.useState<Error | null>(null);

  React.useEffect(() => {
    let cancelled = false;

    const loadMicrofrontend = async () => {
      setIsLoading(true);
      setError(null);

      try {
        const loadedModule = await microfrontendLoader.loadMicrofrontend(config);
        
        if (!cancelled) {
          setModule(loadedModule);
        }
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof Error ? err : new Error(String(err)));
        }
      } finally {
        if (!cancelled) {
          setIsLoading(false);
        }
      }
    };

    loadMicrofrontend();

    return () => {
      cancelled = true;
    };
  }, [config.name, config.url]);

  return {
    module,
    isLoading,
    error,
    isLoaded: !!module,
  };
};

export default microfrontendLoader;