import { ThemeConfig } from '@/types';

interface ThemeVariables {
  [key: string]: string;
}

interface DynamicTheme extends ThemeConfig {
  id: string;
  variables: ThemeVariables;
  customCSS?: string;
}

class TenantThemeManager {
  private themes: Map<string, DynamicTheme> = new Map();
  private currentTheme: DynamicTheme | null = null;
  private styleElement: HTMLStyleElement | null = null;

  constructor() {
    this.initializeDefaultThemes();
    this.createStyleElement();
  }

  private initializeDefaultThemes(): void {
    const defaultThemes: DynamicTheme[] = [
      {
        id: 'default',
        name: 'Default',
        colors: {
          primary: '#3b82f6',
          secondary: '#64748b',
          background: '#ffffff',
          text: '#1f2937',
        },
        fonts: {
          primary: 'Inter, system-ui, sans-serif',
          secondary: 'ui-monospace, monospace',
        },
        variables: {
          '--color-primary': '#3b82f6',
          '--color-secondary': '#64748b',
          '--color-background': '#ffffff',
          '--color-text': '#1f2937',
          '--font-primary': 'Inter, system-ui, sans-serif',
          '--font-secondary': 'ui-monospace, monospace',
          '--border-radius': '0.5rem',
          '--shadow': '0 1px 3px rgba(0, 0, 0, 0.1)',
        },
      },
      {
        id: 'dark',
        name: 'Dark',
        colors: {
          primary: '#60a5fa',
          secondary: '#94a3b8',
          background: '#111827',
          text: '#f9fafb',
        },
        fonts: {
          primary: 'Inter, system-ui, sans-serif',
          secondary: 'ui-monospace, monospace',
        },
        variables: {
          '--color-primary': '#60a5fa',
          '--color-secondary': '#94a3b8',
          '--color-background': '#111827',
          '--color-text': '#f9fafb',
          '--font-primary': 'Inter, system-ui, sans-serif',
          '--font-secondary': 'ui-monospace, monospace',
          '--border-radius': '0.5rem',
          '--shadow': '0 1px 3px rgba(0, 0, 0, 0.3)',
        },
      },
      {
        id: 'purple',
        name: 'Purple',
        colors: {
          primary: '#8b5cf6',
          secondary: '#a78bfa',
          background: '#faf5ff',
          text: '#581c87',
        },
        fonts: {
          primary: 'Inter, system-ui, sans-serif',
          secondary: 'ui-monospace, monospace',
        },
        variables: {
          '--color-primary': '#8b5cf6',
          '--color-secondary': '#a78bfa',
          '--color-background': '#faf5ff',
          '--color-text': '#581c87',
          '--font-primary': 'Inter, system-ui, sans-serif',
          '--font-secondary': 'ui-monospace, monospace',
          '--border-radius': '0.75rem',
          '--shadow': '0 1px 3px rgba(139, 92, 246, 0.2)',
        },
      },
    ];

    defaultThemes.forEach(theme => {
      this.themes.set(theme.id, theme);
    });
  }

  private createStyleElement(): void {
    if (typeof document === 'undefined') return;

    this.styleElement = document.createElement('style');
    this.styleElement.id = 'tenant-theme-styles';
    document.head.appendChild(this.styleElement);
  }

  registerTheme(theme: DynamicTheme): void {
    this.themes.set(theme.id, theme);
  }

  getTheme(themeId: string): DynamicTheme | null {
    return this.themes.get(themeId) || null;
  }

  getAllThemes(): DynamicTheme[] {
    return Array.from(this.themes.values());
  }

  async loadTenantTheme(tenantId: string): Promise<DynamicTheme | null> {
    try {
      // Try to load tenant-specific theme from API
      const response = await fetch(`/api/tenants/${tenantId}/theme`);
      
      if (response.ok) {
        const tenantTheme: DynamicTheme = await response.json();
        this.registerTheme(tenantTheme);
        return tenantTheme;
      }
    } catch (error) {
      console.warn('Failed to load tenant theme:', error);
    }

    // Fallback to stored theme or default
    const storedThemeId = this.getStoredThemeId(tenantId);
    return this.getTheme(storedThemeId || 'default');
  }

  applyTheme(themeId: string): boolean {
    const theme = this.getTheme(themeId);
    if (!theme) {
      console.error(`Theme not found: ${themeId}`);
      return false;
    }

    this.currentTheme = theme;
    this.updateCSSVariables(theme);
    this.storeThemeId(themeId);
    
    // Dispatch event for components that need to react to theme changes
    if (typeof window !== 'undefined') {
      window.dispatchEvent(new CustomEvent('theme-changed', { 
        detail: { theme } 
      }));
    }

    return true;
  }

  private updateCSSVariables(theme: DynamicTheme): void {
    if (!this.styleElement) return;

    const cssRules = [
      ':root {',
      ...Object.entries(theme.variables).map(([key, value]) => `  ${key}: ${value};`),
      '}',
    ];

    if (theme.customCSS) {
      cssRules.push('', theme.customCSS);
    }

    this.styleElement.textContent = cssRules.join('\n');
  }

  getCurrentTheme(): DynamicTheme | null {
    return this.currentTheme;
  }

  private storeThemeId(themeId: string): void {
    if (typeof localStorage === 'undefined') return;
    
    try {
      localStorage.setItem('selected-theme', themeId);
    } catch (error) {
      console.warn('Failed to store theme preference:', error);
    }
  }

  private getStoredThemeId(tenantId?: string): string | null {
    if (typeof localStorage === 'undefined') return null;
    
    try {
      // First try tenant-specific theme
      if (tenantId) {
        const tenantTheme = localStorage.getItem(`theme-${tenantId}`);
        if (tenantTheme) return tenantTheme;
      }

      // Fallback to global theme preference
      return localStorage.getItem('selected-theme');
    } catch (error) {
      console.warn('Failed to get stored theme:', error);
      return null;
    }
  }

  // Utility method to generate CSS variables from theme
  generateCSSVariables(theme: ThemeConfig): ThemeVariables {
    return {
      '--color-primary': theme.colors.primary,
      '--color-secondary': theme.colors.secondary,
      '--color-background': theme.colors.background,
      '--color-text': theme.colors.text,
      '--font-primary': theme.fonts.primary,
      '--font-secondary': theme.fonts.secondary,
    };
  }

  // Method to create a new theme based on existing one
  createThemeVariant(baseThemeId: string, overrides: Partial<DynamicTheme>): DynamicTheme {
    const baseTheme = this.getTheme(baseThemeId);
    if (!baseTheme) {
      throw new Error(`Base theme not found: ${baseThemeId}`);
    }

    const newTheme: DynamicTheme = {
      ...baseTheme,
      ...overrides,
      id: overrides.id || `${baseThemeId}-variant-${Date.now()}`,
      colors: { ...baseTheme.colors, ...overrides.colors },
      fonts: { ...baseTheme.fonts, ...overrides.fonts },
      variables: { 
        ...baseTheme.variables, 
        ...overrides.variables,
        ...this.generateCSSVariables({
          name: overrides.name || baseTheme.name,
          colors: { ...baseTheme.colors, ...overrides.colors },
          fonts: { ...baseTheme.fonts, ...overrides.fonts },
        })
      },
    };

    this.registerTheme(newTheme);
    return newTheme;
  }

  // Method to export theme as JSON
  exportTheme(themeId: string): string | null {
    const theme = this.getTheme(themeId);
    if (!theme) return null;

    return JSON.stringify(theme, null, 2);
  }

  // Method to import theme from JSON
  importTheme(themeJson: string): DynamicTheme | null {
    try {
      const theme: DynamicTheme = JSON.parse(themeJson);
      
      // Validate theme structure
      if (!theme.id || !theme.name || !theme.colors || !theme.fonts) {
        throw new Error('Invalid theme structure');
      }

      // Generate variables if not present
      if (!theme.variables) {
        theme.variables = this.generateCSSVariables(theme);
      }

      this.registerTheme(theme);
      return theme;
    } catch (error) {
      console.error('Failed to import theme:', error);
      return null;
    }
  }
}

export const tenantThemeManager = new TenantThemeManager();

// React hook for using themes in components
export const useTheme = () => {
  const [currentTheme, setCurrentTheme] = React.useState<DynamicTheme | null>(
    tenantThemeManager.getCurrentTheme()
  );

  React.useEffect(() => {
    const handleThemeChange = (event: CustomEvent<{ theme: DynamicTheme }>) => {
      setCurrentTheme(event.detail.theme);
    };

    window.addEventListener('theme-changed', handleThemeChange as EventListener);

    return () => {
      window.removeEventListener('theme-changed', handleThemeChange as EventListener);
    };
  }, []);

  const applyTheme = (themeId: string) => {
    return tenantThemeManager.applyTheme(themeId);
  };

  const getAllThemes = () => {
    return tenantThemeManager.getAllThemes();
  };

  return {
    currentTheme,
    applyTheme,
    getAllThemes,
    themeManager: tenantThemeManager,
  };
};

export default tenantThemeManager;