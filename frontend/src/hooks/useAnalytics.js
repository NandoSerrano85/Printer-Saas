// hooks/useAnalytics.js
import { useEffect } from 'react';
import { useTenant } from '../contexts/TenantContext';

class AnalyticsService {
  constructor() {
    this.events = [];
    this.sessionId = this.generateSessionId();
  }

  generateSessionId() {
    return `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }

  track(event, properties = {}) {
    const eventData = {
      event,
      properties: {
        ...properties,
        timestamp: new Date().toISOString(),
        sessionId: this.sessionId,
        url: window.location.href,
        userAgent: navigator.userAgent,
      },
    };

    this.events.push(eventData);
    
    // Send to analytics endpoint
    this.sendToAnalytics(eventData);
  }

  async sendToAnalytics(eventData) {
    try {
      await fetch('/api/analytics', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(eventData),
      });
    } catch (error) {
      console.error('Analytics tracking failed:', error);
    }
  }

  trackPageView(page, tenant) {
    this.track('page_view', {
      page,
      tenant: tenant?.id,
    });
  }

  trackUserAction(action, data = {}) {
    this.track('user_action', {
      action,
      ...data,
    });
  }

  trackPerformance(metric, value, tenant) {
    this.track('performance', {
      metric,
      value,
      tenant: tenant?.id,
    });
  }
}

const analytics = new AnalyticsService();

export const useAnalytics = () => {
  const { tenant } = useTenant();

  const trackEvent = (event, properties = {}) => {
    analytics.track(event, {
      ...properties,
      tenant: tenant?.id,
    });
  };

  const trackPageView = (page) => {
    analytics.trackPageView(page, tenant);
  };

  const trackUserAction = (action, data = {}) => {
    analytics.trackUserAction(action, {
      ...data,
      tenant: tenant?.id,
    });
  };

  return {
    trackEvent,
    trackPageView,
    trackUserAction,
  };
};

// Performance monitoring hook
export const usePerformanceMonitoring = () => {
  const { tenant } = useTenant();

  useEffect(() => {
    // Track Core Web Vitals
    import('web-vitals').then(({ getCLS, getFID, getFCP, getLCP, getTTFB }) => {
      getCLS((metric) => {
        analytics.trackPerformance('CLS', metric.value, tenant);
      });

      getFID((metric) => {
        analytics.trackPerformance('FID', metric.value, tenant);
      });

      getFCP((metric) => {
        analytics.trackPerformance('FCP', metric.value, tenant);
      });

      getLCP((metric) => {
        analytics.trackPerformance('LCP', metric.value, tenant);
      });

      getTTFB((metric) => {
        analytics.trackPerformance('TTFB', metric.value, tenant);
      });
    });

    // Track custom performance metrics
    const navigationStart = performance.timing.navigationStart;
    const domContentLoaded = performance.timing.domContentLoadedEventEnd;
    const loadTime = domContentLoaded - navigationStart;

    analytics.trackPerformance('page_load_time', loadTime, tenant);
  }, [tenant]);
};