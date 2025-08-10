// hooks/usePWA.js
import { useState, useEffect } from 'react';

export const usePWA = () => {
  const [isInstallable, setIsInstallable] = useState(false);
  const [installPrompt, setInstallPrompt] = useState(null);
  const [isOnline, setIsOnline] = useState(navigator.onLine);

  useEffect(() => {
    // PWA install prompt
    const handleBeforeInstallPrompt = (e) => {
      e.preventDefault();
      setInstallPrompt(e);
      setIsInstallable(true);
    };

    // Online/offline status
    const handleOnline = () => setIsOnline(true);
    const handleOffline = () => setIsOnline(false);

    window.addEventListener('beforeinstallprompt', handleBeforeInstallPrompt);
    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);

    return () => {
      window.removeEventListener('beforeinstallprompt', handleBeforeInstallPrompt);
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
    };
  }, []);

  const installApp = async () => {
    if (installPrompt) {
      installPrompt.prompt();
      const result = await installPrompt.userChoice;
      if (result.outcome === 'accepted') {
        setIsInstallable(false);
        setInstallPrompt(null);
      }
    }
  };

  return {
    isInstallable,
    installApp,
    isOnline,
  };
};

// PWA Install Banner Component
export const PWAInstallBanner = () => {
  const { isInstallable, installApp } = usePWA();
  const [dismissed, setDismissed] = useState(
    localStorage.getItem('pwa-banner-dismissed') === 'true'
  );

  if (!isInstallable || dismissed) return null;

  const handleDismiss = () => {
    setDismissed(true);
    localStorage.setItem('pwa-banner-dismissed', 'true');
  };

  return (
    <div className="fixed top-0 left-0 right-0 bg-blue-600 text-white p-4 z-50">
      <div className="flex items-center justify-between max-w-4xl mx-auto">
        <div className="flex items-center gap-3">
          <span>📱</span>
          <span>Install Etsy Automater for quick access!</span>
        </div>
        <div className="flex gap-2">
          <button
            onClick={installApp}
            className="bg-blue-700 px-4 py-2 rounded hover:bg-blue-800"
          >
            Install
          </button>
          <button
            onClick={handleDismiss}
            className="bg-blue-700 px-4 py-2 rounded hover:bg-blue-800"
          >
            ✕
          </button>
        </div>
      </div>
    </div>
  );
};