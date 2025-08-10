import { useTenant } from '../contexts/TenantContext';
import { useEffect } from 'react';

export const ThemeProvider = ({ children }) => {
  const { tenant } = useTenant();

  useEffect(() => {
    if (tenant?.theme) {
      document.documentElement.style.setProperty(
        '--primary-color',
        tenant.theme.primary
      );
      document.documentElement.style.setProperty(
        '--secondary-color',
        tenant.theme.secondary
      );
      document.documentElement.style.setProperty(
        '--accent-color',
        tenant.theme.accent
      );

      // Update favicon dynamically
      const favicon = document.querySelector('link[rel="icon"]');
      if (favicon) {
        favicon.href = tenant.theme.favicon;
      }
    }
  }, [tenant]);

  return <div className="theme-container">{children}</div>;
};