/**
 * Service Worker for Aprende Comigo PWA
 * Milestone 0 - Basic prototype for offline capability testing
 */

// Production logging utility
const SERVICE_WORKER_DEBUG = false; // Set to false for production
const log = SERVICE_WORKER_DEBUG ? console.log.bind(console, '[SW]') : () => {};
const warn = SERVICE_WORKER_DEBUG ? console.warn.bind(console, '[SW]') : () => {};
const error = console.error.bind(console, '[SW]'); // Always log errors

const CACHE_NAME = 'aprende-comigo-v1';
const OFFLINE_URL = '/offline/';

// Assets to cache on install (Shell resources - critical for offline functionality)
const CACHE_ASSETS = [
  '/',
  '/offline/',
  '/static/manifest.json',
  '/static/js/pwa-core.js',
  '/static/js/push-notifications.js',
  '/static/images/icon-192x192.png',
  '/static/images/icon-512x512.png',
  // Add core CSS and JavaScript files when identified
];

// Install event - cache assets
self.addEventListener('install', (event) => {
  log('Service Worker: Installing...');
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then((cache) => {
        log('Service Worker: Caching assets');
        return cache.addAll(CACHE_ASSETS);
      })
      .catch((error) => {
        error('Service Worker: Cache failed', error);
      })
  );
  self.skipWaiting();
});

// Activate event - clean up old caches
self.addEventListener('activate', (event) => {
  log('Service Worker: Activating...');

  const cacheWhitelist = [CACHE_NAME, 'api-cache-v1', 'form-submissions-v1'];

  event.waitUntil(
    caches.keys().then((cacheNames) => {
      return Promise.all(
        cacheNames.map((cacheName) => {
          if (!cacheWhitelist.includes(cacheName)) {
            log('Service Worker: Deleting old cache', cacheName);
            return caches.delete(cacheName);
          }
        })
      );
    }).then(() => {
      // Clean up expired API cache entries
      return cleanupExpiredCache();
    })
  );
  self.clients.claim();
});

// Clean up expired API cache entries
async function cleanupExpiredCache() {
  try {
    const cache = await caches.open('api-cache-v1');
    const requests = await cache.keys();

    for (const request of requests) {
      const response = await cache.match(request);
      const cachedAt = response.headers.get('sw-cached-at');

      // Remove entries older than 5 minutes
      if (cachedAt && (Date.now() - parseInt(cachedAt)) > 300000) {
        await cache.delete(request);
        log('Service Worker: Removed expired cache entry', request.url);
      }
    }
  } catch (error) {
    error('Service Worker: Failed to cleanup expired cache:', error);
  }
}

// Fetch event - implement different caching strategies based on request type
self.addEventListener('fetch', (event) => {
  const url = new URL(event.request.url);

  // Skip cross-origin requests that we don't control
  if (url.origin !== location.origin) {
    return;
  }

  // Handle navigation requests (HTML pages)
  if (event.request.mode === 'navigate') {
    event.respondWith(handleNavigationRequest(event.request));
    return;
  }

  // Handle static assets (CSS, JS, images)
  if (event.request.destination === 'style' ||
      event.request.destination === 'script' ||
      event.request.destination === 'image') {
    event.respondWith(handleStaticAssets(event.request));
    return;
  }

  // Handle API requests
  if (url.pathname.startsWith('/api/') || url.pathname.startsWith('/ajax/')) {
    event.respondWith(handleAPIRequest(event.request));
    return;
  }

  // Default: Network first with cache fallback
  event.respondWith(handleDefaultRequest(event.request));
});

// Navigation requests: Network first, cache fallback, offline page
async function handleNavigationRequest(request) {
  try {
    const response = await fetch(request);
    // Cache successful navigation responses for offline access
    if (response.status === 200) {
      const cache = await caches.open(CACHE_NAME);
      cache.put(request, response.clone());
    }
    return response;
  } catch (error) {
    // Try cache first
    const cachedResponse = await caches.match(request);
    if (cachedResponse) {
      return cachedResponse;
    }
    // Fallback to offline page
    return caches.match(OFFLINE_URL);
  }
}

// Static assets: Cache first, network fallback
async function handleStaticAssets(request) {
  const cachedResponse = await caches.match(request);
  if (cachedResponse) {
    return cachedResponse;
  }

  try {
    const response = await fetch(request);
    if (response.status === 200 && request.method === 'GET') {
      const cache = await caches.open(CACHE_NAME);
      cache.put(request, response.clone());
    }
    return response;
  } catch (error) {
    // Return placeholder for failed images
    if (request.destination === 'image') {
      return new Response('', {
        status: 200,
        statusText: 'OK',
        headers: { 'Content-Type': 'image/svg+xml' }
      });
    }
    throw error;
  }
}

// API requests: Network first with short cache for performance
async function handleAPIRequest(request) {
  try {
    const response = await fetch(request);
    // Cache successful GET API responses for 5 minutes
    if (response.status === 200 && request.method === 'GET') {
      const cache = await caches.open('api-cache-v1');
      const responseWithTimestamp = response.clone();
      // Add timestamp header for cache expiration
      responseWithTimestamp.headers.set('sw-cached-at', Date.now().toString());
      cache.put(request, responseWithTimestamp);
    }
    return response;
  } catch (error) {
    // Try cached API response if network fails
    const cachedResponse = await caches.match(request);
    if (cachedResponse) {
      // Check if cache is still valid (5 minutes)
      const cachedAt = cachedResponse.headers.get('sw-cached-at');
      if (cachedAt && (Date.now() - parseInt(cachedAt)) < 300000) {
        return cachedResponse;
      }
    }
    throw error;
  }
}

// Default requests: Network first with cache fallback
async function handleDefaultRequest(request) {
  try {
    const response = await fetch(request);
    if (response.status === 200 && request.method === 'GET') {
      const cache = await caches.open(CACHE_NAME);
      cache.put(request, response.clone());
    }
    return response;
  } catch (error) {
    const cachedResponse = await caches.match(request);
    if (cachedResponse) {
      return cachedResponse;
    }
    throw error;
  }
}

// Background sync for offline actions
self.addEventListener('sync', (event) => {
  log('Service Worker: Background sync', event.tag);

  if (event.tag === 'chat-message-sync') {
    // Handle offline chat message queue
    event.waitUntil(syncOfflineMessages());
  }

  if (event.tag === 'file-upload-sync') {
    // Handle offline file upload queue
    event.waitUntil(syncOfflineUploads());
  }
});

// Push notification handling
self.addEventListener('push', (event) => {
  log('Service Worker: Push notification received');

  const options = {
    body: event.data ? event.data.text() : 'New notification from Aprende Comigo',
    icon: '/static/images/icon-192x192.png',
    badge: '/static/images/badge-icon.png',
    vibrate: [200, 100, 200],
    tag: 'aprende-comigo-notification',
    requireInteraction: true,
    actions: [
      {
        action: 'open',
        title: 'Open App',
        icon: '/static/images/open-icon.png'
      },
      {
        action: 'close',
        title: 'Close',
        icon: '/static/images/close-icon.png'
      }
    ]
  };

  event.waitUntil(
    self.registration.showNotification('Aprende Comigo', options)
  );
});

// Notification click handling
self.addEventListener('notificationclick', (event) => {
  log('Service Worker: Notification clicked', event.action);

  event.notification.close();

  if (event.action === 'open') {
    event.waitUntil(
      clients.openWindow('/')
    );
  }
});

// Helper function to sync offline messages
async function syncOfflineMessages() {
  try {
    const cache = await caches.open('offline-queue');
    const requests = await cache.keys();

    for (const request of requests) {
      if (request.url.includes('/api/messages/')) {
        // Attempt to send cached message
        const response = await fetch(request);
        if (response.ok) {
          await cache.delete(request);
        }
      }
    }
  } catch (error) {
    error('Failed to sync offline messages:', error);
  }
}

// Helper function to sync offline uploads
async function syncOfflineUploads() {
  try {
    const cache = await caches.open('offline-queue');
    const requests = await cache.keys();

    for (const request of requests) {
      if (request.url.includes('/upload/')) {
        // Attempt to upload cached file
        const response = await fetch(request);
        if (response.ok) {
          await cache.delete(request);
        }
      }
    }
  } catch (error) {
    error('Failed to sync offline uploads:', error);
  }
}
