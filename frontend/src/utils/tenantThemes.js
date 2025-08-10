export const getTenantTheme = (tenantId) => {
    const themes = {
        tenant1: {
            primary: '#3B82F6', // Blue
            secondary: '#10B981', // Green
            accent: '#F59E0B', // Amber
            logo: '/logos/tenant1-logo.svg',
            favicon: '/favicons/tenant1.ico'
        },
        tenant2: {
            primary: '#EF4444', // Red
            secondary: '#8B5CF6', // Purple
            accent: '#F97316', // Orange
            logo: '/logos/tenant2-logo.svg',
            favicon: '/favicons/tenant2.ico'
        },
        default: {
            primary: '#6B7280', // Gray
            secondary: '#374151',
            accent: '#9CA3AF',
            logo: '/logos/default-logo.svg',
            favicon: '/favicon.ico'
        }
    };
    return themes[tenantId] || themes.default;
};