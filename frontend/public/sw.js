// public/sw.js - Service Worker for advanced caching
const CACHE_NAME = 'etsy-automater-v1';
const TENANT_CACHE_PREFIX = 'tenant-';

// Cache strategies for different resource types
const CACHE_STRATEGIES = {
  tenant_assets: 'cache-first',
  api_data: 'network-first',
  static_assets: 'cache-first',
};

self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      return cache.addAll([
        '/',
        '/static/css/main.css',
        '/static/js/main.js',
        '/static/media/logo.svg',
      ]);
    })
  );
});

self.addEventListener('fetch', (event) => {
  const { request } = event;
  const url = new URL(request.url);
  
  // Handle tenant-specific caching
  if (url.pathname.startsWith('/tenant-assets/')) {
    event.respondWith(cacheFirstStrategy(request));
  }
  
  // Handle API requests
  else if (url.pathname.startsWith('/api/')) {
    event.respondWith(networkFirstStrategy(request));
  }
  
  // Handle static assets
  else {
    event.respondWith(cacheFirstStrategy(request));
  }
});

async function cacheFirstStrategy(request) {
  const cache = await caches.open(CACHE_NAME);
  const cachedResponse = await cache.match(request);
  
  if (cachedResponse) {
    // Update cache in background
    fetch(request).then(response => {
      if (response.ok) {
        cache.put(request, response.clone());
      }
    });
    return cachedResponse;
  }
  
  const response = await fetch(request);
  if (response.ok) {
    cache.put(request, response.clone());
  }
  return response;
}

async function networkFirstStrategy(request) {
  try {
    const response = await fetch(request);
    if (response.ok) {
      const cache = await caches.open(CACHE_NAME);
      cache.put(request, response.clone());
    }
    return response;
  } catch (error) {
    const cache = await caches.open(CACHE_NAME);
    const cachedResponse = await cache.match(request);
    return cachedResponse || new Response('Offline', { status: 503 });
  }
}