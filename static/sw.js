/**
 * Service Worker for Aprende Comigo PWA
 * Implements advanced caching strategies and offline functionality
 */

// Production logging utility
const SW_DEBUG = false; // Set to false for production
const log = SW_DEBUG ? console.log.bind(console, '[SW]') : () => {};
const warn = SW_DEBUG ? console.warn.bind(console, '[SW]') : () => {};
const error = console.error.bind(console, '[SW]'); // Always log errors

const CACHE_VERSION = 'v1.0.0';
const STATIC_CACHE = `aprende-comigo-static-${CACHE_VERSION}`;
const DYNAMIC_CACHE = `aprende-comigo-dynamic-${CACHE_VERSION}`;
const API_CACHE = `aprende-comigo-api-${CACHE_VERSION}`;
const OFFLINE_PAGE = '/offline/';

// Files to cache immediately
const STATIC_ASSETS = [
    '/',
    '/static/css/tailwind.css',
    '/static/js/pwa-core.js',
    '/static/js/htmx.min.js',
    '/static/images/logo.png',
    '/offline/',
    '/manifest.json'
];

// API endpoints to cache
const CACHEABLE_APIS = [
    '/api/courses/',
    '/api/subjects/',
    '/api/teachers/',
    '/education/student/portal/',
    '/education/teacher/dashboard/'
];

// Network-first strategy URLs
const NETWORK_FIRST = [
    '/education/payments/',
    '/api/payments/',
    '/api/auth/',
    '/admin/'
];

// Cache-first strategy for static assets
const CACHE_FIRST = [
    '/static/',
    '/media/',
    '.css',
    '.js',
    '.png',
    '.jpg',
    '.jpeg',
    '.svg',
    '.woff',
    '.woff2'
];

self.addEventListener('install', (event) => {
    log('Service Worker installing...');

    event.waitUntil(
        caches.open(STATIC_CACHE)
            .then(cache => {
                log('Caching static assets...');
                return cache.addAll(STATIC_ASSETS);
            })
            .then(() => {
                log('Static assets cached successfully');
                return self.skipWaiting();
            })
            .catch(error => {
                error('Failed to cache static assets:', error);
            })
    );
});

self.addEventListener('activate', (event) => {
    log('Service Worker activating...');

    event.waitUntil(
        Promise.all([
            // Clean up old caches
            caches.keys().then(cacheNames => {
                return Promise.all(
                    cacheNames
                        .filter(cacheName => {
                            return cacheName.startsWith('aprende-comigo-') &&
                                   !cacheName.includes(CACHE_VERSION);
                        })
                        .map(cacheName => {
                            log('Deleting old cache:', cacheName);
                            return caches.delete(cacheName);
                        })
                );
            }),
            // Take control of all clients
            self.clients.claim()
        ])
    );
});

self.addEventListener('fetch', (event) => {
    const { request } = event;
    const url = new URL(request.url);

    // Skip cross-origin requests
    if (url.origin !== location.origin) {
        return;
    }

    // Determine caching strategy
    if (shouldUseNetworkFirst(request)) {
        event.respondWith(networkFirstStrategy(request));
    } else if (shouldUseCacheFirst(request)) {
        event.respondWith(cacheFirstStrategy(request));
    } else if (isAPIRequest(request)) {
        event.respondWith(staleWhileRevalidateStrategy(request));
    } else {
        event.respondWith(networkFallbackStrategy(request));
    }
});

// Caching Strategies

async function networkFirstStrategy(request) {
    try {
        // Try network first
        const networkResponse = await fetch(request);

        // Cache successful responses
        if (networkResponse.ok) {
            const cache = await caches.open(DYNAMIC_CACHE);
            cache.put(request, networkResponse.clone());
        }

        return networkResponse;
    } catch (error) {
        // Fallback to cache
        const cachedResponse = await caches.match(request);

        if (cachedResponse) {
            return cachedResponse;
        }

        // Return offline page for navigation requests
        if (request.mode === 'navigate') {
            return caches.match(OFFLINE_PAGE);
        }

        throw error;
    }
}

async function cacheFirstStrategy(request) {
    // Try cache first
    const cachedResponse = await caches.match(request);

    if (cachedResponse) {
        return cachedResponse;
    }

    // Fallback to network
    try {
        const networkResponse = await fetch(request);

        if (networkResponse.ok) {
            const cache = await caches.open(STATIC_CACHE);
            cache.put(request, networkResponse.clone());
        }

        return networkResponse;
    } catch (error) {
        error('Cache-first strategy failed:', error);
        throw error;
    }
}

async function staleWhileRevalidateStrategy(request) {
    const cache = await caches.open(API_CACHE);
    const cachedResponse = await cache.match(request);

    // Fetch from network in background
    const networkPromise = fetch(request)
        .then(response => {
            if (response.ok) {
                cache.put(request, response.clone());
            }
            return response;
        })
        .catch(error => {
            error('Network fetch failed:', error);
            return null;
        });

    // Return cached version immediately, or wait for network
    return cachedResponse || networkPromise;
}

async function networkFallbackStrategy(request) {
    try {
        const networkResponse = await fetch(request);

        // Cache successful responses
        if (networkResponse.ok) {
            const cache = await caches.open(DYNAMIC_CACHE);
            cache.put(request, networkResponse.clone());
        }

        return networkResponse;
    } catch (error) {
        // Fallback to cache
        const cachedResponse = await caches.match(request);

        if (cachedResponse) {
            return cachedResponse;
        }

        // Return offline page for navigation requests
        if (request.mode === 'navigate') {
            return caches.match(OFFLINE_PAGE);
        }

        throw error;
    }
}

// Strategy Selection Helpers

function shouldUseNetworkFirst(request) {
    return NETWORK_FIRST.some(pattern => request.url.includes(pattern));
}

function shouldUseCacheFirst(request) {
    return CACHE_FIRST.some(pattern =>
        request.url.includes(pattern) || request.url.endsWith(pattern)
    );
}

function isAPIRequest(request) {
    return CACHEABLE_APIS.some(api => request.url.includes(api)) ||
           request.url.includes('/api/');
}

// Background Sync
self.addEventListener('sync', (event) => {
    log('Background sync triggered:', event.tag);

    if (event.tag === 'background-sync-forms') {
        event.waitUntil(syncFormSubmissions());
    } else if (event.tag === 'background-sync-enrollments') {
        event.waitUntil(syncEnrollments());
    }
});

async function syncFormSubmissions() {
    try {
        const cache = await caches.open('form-submissions-v1');
        const requests = await cache.keys();

        for (const request of requests) {
            try {
                const response = await cache.match(request);
                const formData = await response.json();

                // Attempt to submit the form
                const submitResponse = await fetch(formData.url, {
                    method: formData.method,
                    headers: formData.headers,
                    body: formData.body
                });

                if (submitResponse.ok) {
                    // Remove from cache on success
                    await cache.delete(request);
                    log('Form submission synced successfully');

                    // Notify clients
                    self.clients.matchAll().then(clients => {
                        clients.forEach(client => {
                            client.postMessage({
                                type: 'SYNC_SUCCESS',
                                message: 'Form submitted successfully'
                            });
                        });
                    });
                }
            } catch (error) {
                error('Failed to sync form submission:', error);
            }
        }
    } catch (error) {
        error('Background sync failed:', error);
    }
}

async function syncEnrollments() {
    // Implementation for enrollment-specific background sync
    log('Syncing enrollments...');
}

// Push Notifications
self.addEventListener('push', (event) => {
    log('Push notification received:', event);

    const options = {
        body: 'You have new updates in Aprende Comigo',
        icon: '/static/images/icon-192x192.png',
        badge: '/static/images/badge-72x72.png',
        vibrate: [100, 50, 100],
        data: {
            dateOfArrival: Date.now(),
            primaryKey: '2'
        },
        actions: [
            {
                action: 'explore',
                title: 'View Updates',
                icon: '/static/images/checkmark.png'
            },
            {
                action: 'close',
                title: 'Close',
                icon: '/static/images/xmark.png'
            }
        ]
    };

    if (event.data) {
        const data = event.data.json();
        options.body = data.message || options.body;
        options.data = { ...options.data, ...data };
    }

    event.waitUntil(
        self.registration.showNotification('Aprende Comigo', options)
    );
});

self.addEventListener('notificationclick', (event) => {
    log('Notification clicked:', event);
    event.notification.close();

    if (event.action === 'explore') {
        event.waitUntil(
            clients.openWindow('/')
        );
    } else if (event.action === 'close') {
        // Just close the notification
        return;
    } else {
        // Default action - open the app
        event.waitUntil(
            clients.openWindow('/')
        );
    }
});

// Message Handler for communication with main thread
self.addEventListener('message', (event) => {
    log('Service Worker received message:', event.data);

    if (event.data && event.data.type === 'SKIP_WAITING') {
        self.skipWaiting();
    }
});

log('Service Worker loaded successfully');
