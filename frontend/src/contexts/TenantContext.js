import { 
    createContext,
    useContext,
    useState,
    useEffect
} from 'react';

const TenantContext = createContext();

export const TenantProvider = ({ children }) => {
    const [tenant, setTenant] = useState(null);
    const [isLoading, setIsLoading] = useState(true);

    useEffect(() => {
        // Detect tenant from subdomain or path
        const detectTenant = () => {
            const hostname = window.location.hostname;
            const subdomain = hostname.split('.')[0];
            // tenant1.localhost, tenant2.localhost for local dev
            // tenant1.yourdomain.com for production
            if (subdomain !== 'localhost' && subdomain !== 'www') {
                return subdomain;
            }
            // Fallback to path-based routing: /tenant1/dashboard
            const pathSegments = window.location.pathname.split('/');
            return pathSegments[1] || 'default';
        };

        const tenantId = detectTenant();
        setTenant({
            id: tenantId,
            name: tenantId,
            theme: getTenantTheme(tenantId),
            config: getTenantConfig(tenantId)
        });
        setIsLoading(false);
    }, []);

    return (
        <TenantContext.Provider value={{ tenant, setTenant, isLoading }}>
            {children}
        </TenantContext.Provider>
    );
};

export const useTenant = () => {
    const context = useContext(TenantContext);
    if (!context) {
        throw new Error('useTenant must be used within TenantProvider');
    }
    return context;
}