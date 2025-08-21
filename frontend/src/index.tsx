import React from 'react';
import { createRoot } from 'react-dom/client';
import App from './App';
import { reportWebVitals } from './reportWebVitals';
import { healthMonitor } from '@/utils/healthMonitor';
import { logger } from '@/utils/logger';

// Initialize health monitoring
healthMonitor.startMonitoring();

// Global error handler
window.addEventListener('error', (event) => {
  logger.error('Global error caught', {
    message: event.message,
    filename: event.filename,
    lineno: event.lineno,
    colno: event.colno,
    error: event.error?.stack,
  });
});

// Global promise rejection handler
window.addEventListener('unhandledrejection', (event) => {
  logger.error('Unhandled promise rejection', {
    reason: event.reason,
    promise: event.promise,
  });
  
  // Prevent the default behavior (console error)
  event.preventDefault();
});

// Performance observer for monitoring web vitals
if ('PerformanceObserver' in window) {
  const observer = new PerformanceObserver((list) => {
    for (const entry of list.getEntries()) {
      logger.info('Performance metric', {
        name: entry.name,
        value: entry.value || (entry as any).duration,
        type: entry.entryType,
      });
    }
  });

  observer.observe({ 
    entryTypes: ['navigation', 'measure', 'mark'] 
  });
}

// Get root element
const container = document.getElementById('root');

if (!container) {
  throw new Error('Failed to find the root element');
}

// Create root and render
const root = createRoot(container);

root.render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);

// If you want to start measuring performance in your app, pass a function
// to log results (for example: reportWebVitals(console.log))
// or send to an analytics endpoint. Learn more: https://bit.ly/CRA-vitals
reportWebVitals((metric) => {
  // Send performance metrics to logger
  logger.info('Web Vital', {
    name: metric.name,
    value: metric.value,
    delta: metric.delta,
    id: metric.id,
    rating: metric.rating,
  });
  
  // In production, you might want to send this to an analytics service
  if (process.env.NODE_ENV === 'production') {
    // Example: analytics.track('Web Vital', metric);
  }
});