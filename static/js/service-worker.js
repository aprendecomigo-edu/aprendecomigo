/**
 * Service Worker for Aprende Comigo PWA
 * Milestone 0 - Basic prototype for offline capability testing
 */

// Production logging utility
const DEBUG = false; // Set to false for production
const log = DEBUG ? console.log.bind(console, '[SW]') : () => {};
const warn = DEBUG ? console.warn.bind(console, '[SW]') : () => {};
const error = console.error.bind(console, '[SW]'); // Always log errors

const CACHE_NAME = 'aprende-comigo-v1';
const OFFLINE_URL = '/offline/';

// Assets to cache on install
const CACHE_ASSETS = [
  '/',
  '/pwa/chat-prototype/',
  '/pwa/wizard-demo/',
  '/static/manifest.json',
  // Add other static assets as needed
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
  event.waitUntil(
    caches.keys().then((cacheNames) => {
      return Promise.all(
        cacheNames.map((cacheName) => {
          if (cacheName !== CACHE_NAME) {
            log('Service Worker: Deleting old cache', cacheName);
            return caches.delete(cacheName);
          }
        })
      );
    })
  );
  self.clients.claim();
});

// Fetch event - serve from cache or network
self.addEventListener('fetch', (event) => {
  // Handle navigation requests
  if (event.request.mode === 'navigate') {
    event.respondWith(
      fetch(event.request)
        .then((response) => {
          // If network request succeeds, return response
          return response;
        })
        .catch(() => {
          // If network fails, serve offline page
          return caches.match(OFFLINE_URL);
        })
    );
    return;
  }

  // Handle other requests (CSS, JS, images, API calls)
  event.respondWith(
    caches.match(event.request)
      .then((response) => {
        // Return cached version if available
        if (response) {
          return response;
        }
        
        // Otherwise fetch from network
        return fetch(event.request)
          .then((response) => {
            // Don't cache non-successful responses
            if (!response || response.status !== 200 || response.type !== 'basic') {
              return response;
            }

            // Clone response before caching
            const responseToCache = response.clone();
            
            caches.open(CACHE_NAME)
              .then((cache) => {
                cache.put(event.request, responseToCache);
              });

            return response;
          })
          .catch(() => {
            // For failed image requests, return placeholder
            if (event.request.destination === 'image') {
              return new Response('Image unavailable', {
                status: 200,
                statusText: 'OK',
                headers: { 'Content-Type': 'text/plain' }
              });
            }
          });
      })
  );
});

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
    icon: '/static/images/icon-192.png',
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