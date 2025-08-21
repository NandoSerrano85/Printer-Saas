import { ReportCallback } from 'web-vitals';

const reportWebVitals = (onPerfEntry?: ReportCallback): void => {
  if (onPerfEntry && typeof onPerfEntry === 'function') {
    import('web-vitals').then(({ getCLS, getFID, getFCP, getLCP, getTTFB }) => {
      getCLS(onPerfEntry);
      getFID(onPerfEntry);
      getFCP(onPerfEntry);
      getLCP(onPerfEntry);
      getTTFB(onPerfEntry);
    }).catch((error) => {
      console.warn('Failed to import web-vitals:', error);
    });
  }
};

export { reportWebVitals };